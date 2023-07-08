import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from asyncio import Future
from rift.lsp import LspServer as BaseLspServer
from rift.agents.abstract import (
    AgentState,
    # AgentTask,
    AgentRunParams,
    AgentRunResult,
    Agent,
    AgentProgress,
    AgentRunResult,
    RunAgentParams,
)
from rift.llm.abstract import AbstractCodeCompletionProvider, InsertCodeResult
from rift.lsp.document import TextDocumentItem
import rift.lsp.types as lsp
from rift.server.selection import RangeSet
import asyncio
import logging
from rift.agents.agenttask import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class CodeCompletionRunResult(AgentRunResult):
    ...


@dataclass
class CodeCompletionProgress(AgentProgress):
    response: Optional[str] = None
    thoughts: Optional[str] = None
    textDocument: Optional[lsp.TextDocumentIdentifier] = None
    cursor: Optional[lsp.Position] = None
    ranges: Optional[RangeSet] = None


@dataclass
class CodeCompletionAgentParams(AgentRunParams):
    instructionPrompt: str
    textDocument: lsp.TextDocumentIdentifier
    position: Optional[lsp.Position]


@dataclass
class CodeCompletionAgentState(AgentState):
    model: AbstractCodeCompletionProvider
    document: lsp.TextDocumentItem
    cursor: lsp.Position
    params: CodeCompletionAgentParams
    ranges: RangeSet = field(default_factory=RangeSet)
    change_futures: Dict[str, Future] = field(default_factory=dict)


@dataclass
class CodeCompletionAgent(Agent):
    state: CodeCompletionAgentState
    agent_type: str = "code_completion"

    @classmethod
    def create(cls, params: CodeCompletionAgentParams, model, server):
        state = CodeCompletionAgentState(
            model=model,
            document=server.documents[params.textDocument.uri],
            cursor=params.position,
            ranges=RangeSet(),
            params=params,
            )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )
        return obj

    async def run(self) -> AgentRunResult: # main entry point

        self.server.register_change_callback(self.on_change, self.state.document.uri)
        stream: InsertCodeResult = await self.state.model.insert_code(
            self.state.document.text, self.state.document.position_to_offset(self.state.cursor), goal=self.state.params.instructionPrompt
        )

        async def generate_plan():
            all_deltas = []

            if stream.thoughts is not None:
                async for delta in stream.thoughts:
                    all_deltas.append(delta)

            return "".join(all_deltas)

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
                            # [todo] this happens when an edit occured that clobbers this, try redoing.
                            logger.error(f"timeout waiting for change '{delta}', retry the edit")
                        finally:
                            del self.state.change_futures[delta]
                            pass
                    with lsp.setdoc(self.state.document):
                        added_range = lsp.Range.of_pos(self.state.cursor, len(delta))
                        self.state.cursor += len(delta)
                        self.state.ranges.add(added_range)
                all_text = "".join(all_deltas)
                logger.info(f"{self} finished streaming {len(all_text)} characters")
                return all_text

            except asyncio.CancelledError as e:
                logger.info(f"{self} cancelled: {e}")
                self.cancel()
                return CodeCompletionRunResult()

            except Exception as e:
                logger.exception("worker failed")
                # self.status = "error"
                return CodeCompletionRunResult()

            finally:
                self.server.change_callbacks[self.state.document.uri].discard(self.on_change)
                await self.send_progress(
                    CodeCompletionProgress(response=None, textDocument=self.state.document,
                                           cursor=self.state.cursor, ranges=self.state.ranges)
                )

        await self.send_progress(
            CodeCompletionProgress(response=None, textDocument=self.state.document,
                                   cursor=self.state.cursor, ranges=self.state.ranges)
        )

        plan_task = self.add_task(
            AgentTask(
                "Plan out code edit",
                asyncio.create_task(
                    generate_plan()
                )
            )
        )

        await self.send_progress(
            CodeCompletionProgress(response=None, textDocument=self.state.document,
                                   cursor=self.state.cursor, ranges=self.state.ranges)
        )

        code_task = self.add_task(
            AgentTask(
                "Generate code",
                asyncio.create_task(
                    generate_code()
                )
            )
        )

        await self.send_progress(
            CodeCompletionProgress(response=None, textDocument=self.state.document,
                                   cursor=self.state.cursor, ranges=self.state.ranges)
        )

        await plan_task.run()
        await code_task.run()

        await self.send_progress()

        return CodeCompletionRunResult()



    # async def run(self) -> AgentRunResult:
    #     async def worker():
    #         try:
    #             self.server.register_change_callback(self.on_change, self.state.document.uri)
    #             model = self.state.model
    #             pos = self.state.cursor
    #             offset = self.state.document.position_to_offset(pos)
    #             doc_text = self.state.document.text
    #             stream: InsertCodeResult = await model.insert_code(
    #                 doc_text, offset, goal=self.state.params.instructionPrompt
    #             )
    #             logger.debug("starting streaming code")
    #             all_deltas = []
    #             async for delta in stream.code:
    #                 all_deltas.append(delta)
    #                 assert len(delta) > 0
    #                 attempts = 10
    #                 while True:
    #                     if attempts <= 0:
    #                         logger.error(f"too many edit attempts for '{delta}' dropped")
    #                         return
    #                     attempts -= 1
    #                     cf = asyncio.get_running_loop().create_future()
    #                     self.state.change_futures[delta] = cf
    #                     x = await self.server.apply_insert_text(
    #                         self.state.document.uri,
    #                         self.state.cursor,
    #                         delta,
    #                         self.state.document.version,
    #                     )
    #                     if x.applied == False:
    #                         logger.debug(f"edit '{delta}' failed, retrying")
    #                         await asyncio.sleep(0.1)
    #                         continue
    #                     try:
    #                         await asyncio.wait_for(cf, timeout=2)
    #                         break
    #                     except asyncio.TimeoutError:
    #                         # [todo] this happens when an edit occured that clobbers this, try redoing.
    #                         logger.error(f"timeout waiting for change '{delta}', retry the edit")
    #                     finally:
    #                         del self.state.change_futures[delta]
    #                         pass
    #                 with lsp.setdoc(self.state.document):
    #                     added_range = lsp.Range.of_pos(self.state.cursor, len(delta))
    #                     self.state.cursor += len(delta)
    #                     self.state.ranges.add(added_range)
    #                 await self.send_progress(
    #                     CodeCompletionProgress(tasks=self.tasks, response=None, status=self.status)
    #                 )
    #             all_text = "".join(all_deltas)
    #             logger.info(f"{self} finished streaming {len(all_text)} characters")
    #             self.status = "done"
    #             await self.send_progress(
    #                 CodeCompletionProgress(
    #                     tasks=self.tasks, response=None, thoughts=None, status=self.status
    #                 )
    #             )
    #             if stream.thoughts is not None:
    #                 thoughts = await stream.thoughts.read()
    #                 await self.send_progress(
    #                     CodeCompletionProgress(
    #                         tasks=self.tasks, thoughts=thoughts, status=self.status
    #                     )
    #                 )
    #                 return CodeCompletionRunResult()
    #             else:
    #                 thoughts = "done!"
    #             await self.send_progress(
    #                 CodeCompletionProgress(
    #                     tasks=self.tasks, response=None, thoughts=thoughts, status=self.status
    #                 )
    #             )
    #             return CodeCompletionResult()

    #         except asyncio.CancelledError as e:
    #             logger.info(f"{self} cancelled: {e}")
    #             self.status = "error"
    #             return CodeCompletionRunResult()

    #         except Exception as e:
    #             logger.exception("worker failed")
    #             self.status = "error"
    #             return CodeCompletionRunResult()

    #         finally:
    #             # self.task = None
    #             self.server.change_callbacks[self.state.document.uri].discard(self.on_change)
    #             await self.send_progress(
    #                 CodeCompletionProgress(status=self.status, tasks=self.tasks, response=None)
    #             )

    #     t = asyncio.Task(worker())
    #     self._task = t
    #     await t

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
                    self.state.ranges.apply_edit(c)
                if c.range is None:
                    self.cancel("the whole document got replaced")
                else:
                    if c.range.end <= self.state.cursor:
                        # some text was changed before our cursor
                        if c.range.end.line < self.state.cursor.line:
                            # the change is occuring on lines strictly above us
                            # so we can adjust the number of lines
                            lines_to_add = (
                                c.text.count("\n") + c.range.start.line - c.range.end.line
                            )
                            self.state.cursor += (lines_to_add, 0)
                        else:
                            # self.cancel("someone is editing on the same line as us")
                            pass  # temporarily disable
                    elif self.state.cursor in c.range:
                        self.cancel("someone is editing the same text as us")

        self.state.document = after


    async def request_input(self, request_input_request):
        return await self.server.request(
            f"morph/{self.agent_type}_{self.id}_request_input", request_input_request
        )


    async def request_chat(self, request_chat_request):
        return await self.server.request(
            f"morph/{self.agent_type}_{self.id}_request_chat", request_chat_request
        )


    # async def send_progress(self, progress: Optional[Any] = None):
    #     progress.id = self.id
    #     await self.server.notify(f"morph/{self.agent_type}_{self.id}_send_progress", progress)


    async def send_result(self, result):
        ...  # unreachable


    async def accept(self):
        logger.info(f"{self} user accepted result")
        if self.task.status not in ["error", "done"]:
            logger.error(f"cannot accept status {self.task.status}")
            return
        # self.status = "done"
        await self.send_progress(
            # TODO(jesse): this is a hack
            CodeCompletionProgress(response=None, textDocument=self.state.document, cursor=self.state.cursor, ranges=self.state.ranges)
        )


    async def reject(self):
        # [todo] in this case we need to revert all of the changes that we made.
        logger.info(f"{self} user rejected result")
        # self.status = "done"
        with lsp.setdoc(self.state.document):
            if self.state.ranges.is_empty:
                logger.error("no ranges to reject")
            else:
                edit = lsp.TextEdit(self.state.ranges.cover(), "")
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
                # TODO(jesse): this is a hack
                CodeCompletionProgress(response=None, textDocument=self.state.document, cursor=self.state.cursor, ranges=self.state.ranges)
            )
