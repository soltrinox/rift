import asyncio
import logging
from asyncio import Future
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional

import rift.lsp.types as lsp
from rift.agents.abstract import (
    Agent,
    AgentProgress,  # AgentTask,
    AgentRunParams,
    AgentRunResult,
    AgentState,
    RequestInputRequest,
    RunAgentParams,
    agent,
)
from rift.agents.agenttask import AgentTask
from rift.llm.abstract import AbstractCodeCompletionProvider, InsertCodeResult
from rift.lsp import LspServer as BaseLspServer
from rift.lsp.document import TextDocumentItem
from rift.server.selection import RangeSet

logger = logging.getLogger(__name__)


# dataclass for representing the result of the code completion agent run
@dataclass
class CodeCompletionRunResult(AgentRunResult):
    ...


# dataclass for representing the progress of the code completion agent
@dataclass
class CodeCompletionProgress(AgentProgress):
    response: Optional[str] = None
    thoughts: Optional[str] = None
    textDocument: Optional[lsp.TextDocumentIdentifier] = None
    cursor: Optional[lsp.Position] = None
    additive_ranges: Optional[RangeSet] = None
    negative_ranges: Optional[RangeSet] = None


# dataclass for representing the parameters of the code completion agent
@dataclass
class CodeCompletionAgentParams(AgentRunParams):
    textDocument: lsp.TextDocumentIdentifier
    selection: Optional[lsp.Selection]
    instructionPrompt: Optional[str] = None


# dataclass for representing the state of the code completion agent
@dataclass
class CodeCompletionAgentState(AgentState):
    model: AbstractCodeCompletionProvider
    document: lsp.TextDocumentItem
    cursor: lsp.Position
    params: CodeCompletionAgentParams
    additive_ranges: RangeSet = field(default_factory=RangeSet)
    change_futures: Dict[str, Future] = field(default_factory=dict)


# decorator for creating the code completion agent
@agent(
    agent_description="Generate code following an instruction to be inserted directly at your current cursor location.",
    display_name="Rift Code Completion",
)
@dataclass
class CodeCompletionAgent(Agent):
    state: CodeCompletionAgentState
    agent_type: ClassVar[str] = "code_completion"

    @classmethod
    def create(cls, params: CodeCompletionAgentParams, model, server):
        state = CodeCompletionAgentState(
            model=model,
            document=server.documents[params.textDocument.uri],
            cursor=params.selection.first, # begin at the start of the selection
            additive_ranges=RangeSet(),
            params=params,
        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )
        return obj

    async def run(self) -> AgentRunResult:  # main entry point
        await self.send_progress()
        instructionPrompt = self.state.params.instructionPrompt or (
            await self.request_input(
                RequestInputRequest(
                    msg="Describe what you want me to do",
                    place_holder="Please implement the rest of this function",
                )
            )
        )

        self.server.register_change_callback(self.on_change, self.state.document.uri)
        stream: InsertCodeResult = await self.state.model.insert_code(
            self.state.document.text,
            self.state.document.position_to_offset(self.state.cursor),
            goal=instructionPrompt,
        )

        # function to asynchronously generate the plan
        async def generate_explanation():
            all_deltas = []

            if stream.thoughts is not None:
                async for delta in stream.thoughts:
                    all_deltas.append(delta)
                    await asyncio.sleep(0.01)

            await self.send_progress()
            return "".join(all_deltas)

        # function to asynchronously generate the code
        async def generate_code():
            try:
                all_deltas = []
                async for delta in stream.code:
                    all_deltas.append(delta)
                    assert len(delta) > 0
                    attempts = 10
                    while True:
                        if attempts <= 0:
                            logger.error(f"too many edit attempts for '{delta}' dropped")
                            return
                        attempts -= 1
                        cf = asyncio.get_running_loop().create_future()
                        self.state.change_futures[delta] = cf
                        x = await self.server.apply_insert_text(
                            self.state.document.uri,
                            self.state.cursor,
                            delta,
                            self.state.document.version,
                        )
                        if x.applied == False:
                            logger.debug(f"edit '{delta}' failed, retrying")
                            await asyncio.sleep(0.1)
                            continue
                        try:
                            await asyncio.wait_for(cf, timeout=2)
                            break
                        except asyncio.TimeoutError:
                            # [todo] this happens when an edit occured that clobbered this, try redoing.
                            logger.error(f"timeout waiting for change '{delta}', retry the edit")
                        finally:
                            del self.state.change_futures[delta]
                    with lsp.setdoc(self.state.document):
                        added_range = lsp.Range.of_pos(self.state.cursor, len(delta))
                        self.state.cursor += len(delta)
                        self.state.additive_ranges.add(added_range)
                        # send progress here because VSCode highlighting is triggered by the range
                        await self.send_progress(
                            CodeCompletionProgress(
                                response=None,
                                textDocument=self.state.document,
                                cursor=self.state.cursor,
                                additive_ranges=self.state.additive_ranges,
                            )
                        )                        
                all_text = "".join(all_deltas)
                logger.info(f"{self} finished streaming {len(all_text)} characters")
                await self.send_progress()
                return all_text

            except asyncio.CancelledError as e:
                logger.info(f"{self} cancelled: {e}")
                await self.cancel()
                return CodeCompletionRunResult()

            except Exception as e:
                logger.exception("worker failed")
                # self.status = "error"
                return CodeCompletionRunResult()

            finally:
                self.server.change_callbacks[self.state.document.uri].discard(self.on_change)
                await self.send_progress(
                    CodeCompletionProgress(
                        response=None,
                        textDocument=self.state.document,
                        cursor=self.state.cursor,
                        additive_ranges=self.state.additive_ranges,
                    )
                )

        await self.send_progress(
            CodeCompletionProgress(
                response=None,
                textDocument=self.state.document,
                cursor=self.state.cursor,
                additive_ranges=self.state.additive_ranges,
            )
        )

        code_task = self.add_task(AgentTask("Generate code", generate_code))

        await self.send_progress(
            CodeCompletionProgress(
                response=None,
                textDocument=self.state.document,
                cursor=self.state.cursor,
                additive_ranges=self.state.additive_ranges,
            )
        )

        explanation_task = self.add_task(AgentTask("Explain code edit", generate_explanation))

        await self.send_progress(
            CodeCompletionProgress(
                response=None,
                textDocument=self.state.document,
                cursor=self.state.cursor,
                additive_ranges=self.state.additive_ranges,
            )
        )

        await code_task.run()
        await self.send_progress()

        explanation = await explanation_task.run()
        await self.send_progress()

        await self.send_update(explanation)

        return CodeCompletionRunResult()

    async def on_change(
        self,
        *,
        before: lsp.TextDocumentItem,
        after: lsp.TextDocumentItem,
        changes: lsp.DidChangeTextDocumentParams,
    ):
        if self.task.status != "running":
            return
        """
        [todo]
        When a change happens:
        1. if the change is before our 'working area', then we stop the completion request and run again.
        2. if the change is in our 'working area', then the user is correcting something that
        3. if the change is after our 'working area', then just keep going.
        4. if _we_ caused the change, then just keep going.
        """
        assert changes.textDocument.uri == self.state.document.uri
        self.state.document = before
        for c in changes.contentChanges:
            fut = self.state.change_futures.get(c.text)
            if fut is not None:
                # we caused this change
                fut.set_result(None)
            else:
                # someone else caused this change
                # [todo], in the below examples, we shouldn't cancel, but instead figure out what changed and restart the insertions with the new information.
                with lsp.setdoc(self.state.document):
                    self.state.additive_ranges.apply_edit(c)
                if c.range is None:
                    await self.cancel("the whole document got replaced")
                else:
                    if c.range.end <= self.state.cursor:
                        # some text was changed before our cursor
                        if c.range.end.line < self.state.cursor.line:
                            # the change is occurring on lines strictly above us
                            # so we can adjust the number of lines
                            lines_to_add = (
                                c.text.count("\n") + c.range.start.line - c.range.end.line
                            )
                            self.state.cursor += (lines_to_add, 0)
                        else:
                            # self.cancel("someone is editing on the same line as us")
                            pass  # temporarily disabled
                    elif self.state.cursor in c.range:
                        await self.cancel("someone is editing the same text as us")

        self.state.document = after

    async def send_result(self, result):
        ...  # unreachable

    async def accept(self):
        logger.info(f"{self} user accepted result")
        if self.task.status not in ["error", "done"]:
            logger.error(f"cannot accept status {self.task.status}")
            return
        # self.status = "done"
        await self.send_progress(
            payload="accepted",
            payload_only=True,
        )

    async def reject(self):
        # [todo] in this case we need to revert all of the changes that we made.
        logger.info(f"{self} user rejected result")
        # self.status = "done"
        with lsp.setdoc(self.state.document):
            if self.state.additive_ranges.is_empty:
                logger.error("no ranges to reject")
            else:
                edit = lsp.TextEdit(self.state.additive_ranges.cover(), "")
                params = lsp.ApplyWorkspaceEditParams(
                    edit=lsp.WorkspaceEdit(
                        documentChanges=[
                            lsp.TextDocumentEdit(
                                textDocument=self.state.document.id,
                                edits=[edit],
                            )
                        ]
                    )
                )
                x = await self.server.apply_workspace_edit(params)
                if not x.applied:
                    logger.error("failed to apply rejection edit")
            await self.send_progress(
                payload="rejected",
                payload_only=True,
            )
