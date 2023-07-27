import asyncio
import logging
import random
from asyncio import Future
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional

import rift.llm.openai_types as openai
import rift.lsp.types as lsp
from rift.agents.abstract import AgentProgress  # AgentTask,
from rift.agents.abstract import (Agent, AgentRunParams, AgentRunResult, AgentState,
                                  RequestChatRequest, RequestInputRequest, RunAgentParams, agent)
from rift.agents.agenttask import AgentTask
from rift.llm.abstract import AbstractCodeEditProvider, InsertCodeResult
from rift.lsp import LspServer as BaseLspServer
from rift.lsp.document import TextDocumentItem
from rift.server.selection import RangeSet
from rift.util.TextStream import TextStream

logger = logging.getLogger(__name__)


# dataclass for representing the result of the code completion agent run
@dataclass
class CodeEditRunResult(AgentRunResult):
    ...


# dataclass for representing the progress of the code completion agent
@dataclass
class CodeEditProgress(AgentProgress):
    response: Optional[str] = None
    thoughts: Optional[str] = None
    textDocument: Optional[lsp.TextDocumentIdentifier] = None
    cursor: Optional[lsp.Position] = None
    additive_ranges: Optional[RangeSet] = None
    negative_ranges: Optional[RangeSet] = None
    ready: bool = False


# dataclass for representing the parameters of the code completion agent
@dataclass
class CodeEditAgentParams(AgentRunParams):
    instructionPrompt: Optional[str] = None


# dataclass for representing the state of the code completion agent
@dataclass
class CodeEditAgentState(AgentState):
    model: AbstractCodeEditProvider
    document: lsp.TextDocumentItem
    active_range: lsp.Range
    cursor: lsp.Position
    params: CodeEditAgentParams
    selection: lsp.Selection
    messages: list[openai.Message]
    additive_ranges: RangeSet = field(default_factory=RangeSet)
    negative_ranges: RangeSet = field(default_factory=RangeSet)
    change_futures: Dict[str, Future] = field(default_factory=dict)
    _done: bool = False


# decorator for creating the code completion agent
@agent(
    agent_description="Generate code edit for currently selected region.",
    display_name="Code Edit",
)
@dataclass
class CodeEditAgent(Agent):
    state: CodeEditAgentState
    agent_type: ClassVar[str] = "code_edit"

    @classmethod
    def create(cls, params: CodeEditAgentParams, model, server):
        state = CodeEditAgentState(
            model=model,
            document=server.documents[params.textDocument.uri],
            active_range=lsp.Range(params.selection.start, params.selection.end),
            cursor=params.selection.second,  # begin at the start of the selection
            additive_ranges=RangeSet(),
            params=params,
            selection=params.selection,
            messages=[openai.Message.assistant("What do you want me to do?")],
            _done=False,
        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )
        return obj

    async def run(self) -> AgentRunResult:  # main entry point
        try:
            self.DIFF = None
            self.RANGE = None

            async def get_user_response() -> str:
                return await self.request_chat(RequestChatRequest(messages=self.state.messages))

            await self.send_progress()
            self.RANGE = lsp.Range(self.state.selection.first, self.state.selection.second)
            with lsp.setdoc(self.state.document):
                urtext = self.state.document.text
                uroffset_start = self.state.document.position_to_offset(self.state.selection.first)
                uroffset_end = self.state.document.position_to_offset(self.state.selection.second)

            while True:
                try:
                    # get the next prompt
                    # logger.info("getting user response")
                    get_user_response_t = self.add_task(
                        AgentTask("Get user response", get_user_response)
                    )
                    instructionPrompt = await get_user_response_t.run()
                    # logger.info("got user response")

                    # instructionPrompt = self.state.params.instructionPrompt or (
                    #     await self.request_input(
                    #         RequestInputRequest(
                    #             msg="Describe what you want me to do",
                    #             place_holder="Please implement the rest of this function",
                    #         )
                    #     )
                    # )
                    self.server.register_change_callback(self.on_change, self.state.document.uri)
                    from diff_match_patch import diff_match_patch

                    dmp = diff_match_patch()

                    # with lsp.setdoc(self.state.document):
                    # needs to know about previous edits which is why we pass in the messages
                    # this should preserve an old copy of the document actually
                    # DIFF contains the most recent diff
                    edit_code_result = await self.state.model.edit_code(
                        urtext,
                        uroffset_start,
                        uroffset_end,
                        goal=instructionPrompt,
                        latest_region=None
                        if self.DIFF is None
                        else (self.accepted_diff_text(self.DIFF)),
                    )
                    logger.info("started streaming result")
                    response_stream = TextStream()

                    # rf = asyncio.get_running_loop().create_future()
                    # response_stream._feed_task = rf
                    # rf2 = asyncio.get_running_loop().create_future()
                    async def generate_response():
                        # logger.info("GENERATING RESPONSE")
                        response = ""
                        try:
                            async for delta in response_stream:
                                # logger.info(f"RESPONSE DELTA: {delta=}")
                                response += delta
                                await self.send_progress(CodeEditProgress(response=response))
                        except Exception as e:
                            logger.info(f"RESPONSE EXCEPTION: {e}")
                            raise e
                        finally:
                            await self.send_progress({"response": response, "done_streaming": True})
                        # logger.info(f"DONE {response=}")
                        return response

                    generate_response_t = asyncio.create_task(generate_response())

                    # async def gather_plan():
                    #     logger.info("GATHERING PLAN")
                    #     flag = False
                    #     async with response_lock:
                    #         async for delta in edit_code_result.plan:
                    #             logger.info(f"PLAN DELTA: {delta=}")
                    #             response_stream.feed_data(delta)
                    #         response_stream.feed_data("\n```\n")

                    async def gather_thoughts():
                        # logger.info("GATHERING THOUGHTS")
                        flag = False
                        # async with response_lock:
                        async for delta in edit_code_result.thoughts:
                            # if not flag:
                            #     response_stream.feed_data("\n```\n\n")
                            #     flag = True
                            response_stream.feed_data(delta)
                            # logger.info("DONE GATHERING THOUGHTS")

                    async def cleanup():
                        # logger.info("CLEANING UP")
                        response_stream.feed_eof()
                        # logger.info("CLEANED UP")

                    # gather_plan_task = asyncio.create_task(gather_plan())

                    # gather_thoughts_task = asyncio.create_task(gather_thoughts())

                    # t = self.add_task(AgentTask("Generate response and code edit", generate_response))
                    # generate_response_t = asyncio.create_task(t.run())

                    logger.info("created text stream")

                    all_deltas = []
                    # logger.info(f"RANGE BEFORE ITERATION: {RANGE=}")
                    # calculate the diff
                    offset_start = self.state.document.position_to_offset(
                        self.state.selection.first
                    )
                    offset_end = self.state.document.position_to_offset(self.state.selection.second)
                    selection_text = self.state.document.text[offset_start:offset_end]

                    logger.info("starting to iterate through text stream")
                    self.DIFF = None

                    # await gather_plan_task
                    # logger.info("WAITING")
                    async def generate_code():
                        nonlocal all_deltas
                        async for delta in edit_code_result.code:
                            all_deltas.append(delta)
                            # response_stream.feed_data(delta)
                            fuel = 10
                            while True:
                                if self.state._done:
                                    break
                                if fuel <= 0:
                                    raise Exception(":(")
                                try:
                                    # logger.info("in main try")
                                    new_text = "".join(all_deltas)
                                    # logger.info(f"{selection_text=} {new_text=}")

                                    diff = dmp.diff_lineMode(selection_text, new_text, None)
                                    dmp.diff_cleanupSemantic(diff)
                                    # logger.info(f"{diff=}")
                                    self.DIFF = diff  # store the latest diff
                                    diff_text = "".join([text for _, text in diff])

                                    # logger.info(f"got the diff_text: {diff_text=}")

                                    if diff_text == selection_text:
                                        break

                                    cf = asyncio.get_running_loop().create_future()
                                    self.state.change_futures[diff_text] = cf

                                    await self.server.apply_range_edit(
                                        self.state.document.uri, self.RANGE, diff_text
                                    )

                                    def add_pos_text(pos: lsp.Position, text: str):
                                        line_delta = text.count("\n")
                                        if line_delta == 0:
                                            offset = pos.character + len(text)
                                        else:
                                            offset = list(reversed(text)).index("\n")
                                        return lsp.Position(pos.line + line_delta, offset)

                                    self.RANGE = lsp.Range(
                                        self.state.selection.first,
                                        add_pos_text(self.state.selection.first, diff_text),
                                    )

                                    try:
                                        await asyncio.wait_for(cf, timeout=2)
                                        break
                                    except asyncio.TimeoutError:
                                        # [todo] this happens when an edit occured that clobbered this, try redoing.
                                        # logger.error(f"timeout waiting for change '{diff_text=}', retry the edit")
                                        # logger.info(
                                        #     f"timeout waiting for change '{diff_text=}', continuing"
                                        # )
                                        break
                                    finally:
                                        del self.state.change_futures[diff_text]

                                        # recalculate our ranges
                                        self.state.additive_ranges = RangeSet()
                                        self.state.negative_ranges = RangeSet()
                                        with lsp.setdoc(self.state.document):
                                            cursor = self.state.selection.first
                                            for op, text in diff:
                                                next_cursor = add_pos_text(cursor, text)
                                                if op == -1:  # delete
                                                    self.state.negative_ranges.add(
                                                        lsp.Range(cursor, next_cursor)
                                                    )
                                                elif op == 0:  # keep
                                                    pass
                                                elif op == 1:  # add
                                                    self.state.additive_ranges.add(
                                                        lsp.Range(cursor, next_cursor)
                                                    )
                                                cursor = next_cursor

                                        progress = CodeEditProgress(
                                            response=None,
                                            textDocument=self.state.document,
                                            cursor=self.state.cursor,
                                            additive_ranges=list(self.state.additive_ranges),
                                            negative_ranges=list(self.state.negative_ranges),
                                        )
                                        # logger.info(f"{progress=}")
                                        await self.send_progress(progress)
                                except Exception as e:
                                    logger.info(f"caught {e=} retrying")
                                    fuel -= 1

                    # await gather_plan_task
                    await generate_code()
                    await gather_thoughts()
                    t = asyncio.create_task(cleanup())
                    # logger.info("WAITING GENERATE RESPONSE T")
                    assistant_response = await generate_response_t
                    # logger.info("AWAITING T")
                    await t
                    self.state.messages += [
                        openai.Message.user(content=instructionPrompt),
                        openai.Message.assistant(content=assistant_response),
                    ]

                    await self.send_progress(
                        CodeEditProgress(
                            response=None,
                            textDocument=self.state.document,
                            cursor=self.state.cursor,
                            additive_ranges=list(self.state.additive_ranges),
                            negative_ranges=list(self.state.negative_ranges),
                            ready=True,
                        )
                    )
                    # logger.info("LOOPING")
                finally:
                    self.server.change_callbacks[self.state.document.uri].discard(self.on_change)
            return CodeEditRunResult()
        except asyncio.CancelledError as e:
            try:
                await self.reject()
            except:
                raise e

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
            # logger.info(f"contentChange: {c=}")
            # fut = self.state.change_futures.get(c.text)
            fut = None
            for span, vfut in self.state.change_futures.items():
                if c.text in span:
                    fut = vfut

            if fut is not None:
                # we caused this change
                try:
                    fut.set_result(None)
                except:
                    pass
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

    def accepted_diff_text(self, diff):
        result = ""
        for op, text in diff:
            if op == -1:  # remove
                pass
            elif op == 0:
                result += text
            elif op == 1:
                result += text
        return result

    async def accept(self):
        logger.info(f"{self} user accepted result")

        await self.server.apply_range_edit(
            self.state.document.uri, self.RANGE, self.accepted_diff_text(self.DIFF)
        )
        # if self.task.status not in ["error", "done"]:
        #     logger.error(f"cannot accept status {self.task.status}")
        #     return
        # self.status = "done"
        await self.send_progress(
            payload="accepted",
            payload_only=True,
        )
        self.state._done = True

    def rejected_diff_text(self, diff):
        result = ""
        for op, text in diff:
            if op == -1:  # remove
                result += text
            elif op == 0:
                result += text
            elif op == 1:
                pass
        return result

    async def reject(self):
        logger.info(f"{self} user rejected result")

        await self.server.apply_range_edit(
            self.state.document.uri, self.RANGE, self.rejected_diff_text(self.DIFF)
        )
        await self.send_progress(
            payload="rejected",
            payload_only=True,
        )
        self.state._done = True
