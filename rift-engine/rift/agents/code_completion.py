from dataclasses import dataclass
from abc import ABC
from typing import ClassVar, Dict
from rift.lsp import LspServer as BaseLspServer, rpc_method
from rift.agents.abstract import Agent, AgentTask, AgentProgress, RequestCodeCompletionRequest
from rift.llm.openai_types import Message as CodeCompletionMessage
from rift.llm.abstract import AbstractCodeCompletionProvider


@dataclass
class CodeCompletionProgress(
    AgentProgress
):  # reports what tasks are active and responsible for reporting new tasks
    response: Optional[str] = None
    done_streaming: bool = False


@dataclass
class CodeCompletionAgentState(Agent):
    messages: List[CodeCompletionMessage]


@dataclass
class CodeCompletionAgent(Agent):
    agent_id: str
    model: AbstractCodeCompletionProvider
    count: ClassVar[int] = 0
    agent_type: str = "code_completion"

    @classmethod
    def create(cls, messages, server):
        CodeCompletionAgent.count += 1
        obj = CodeCompletionAgent(
            state=CodeCompletionAgentState(messages=messages), tasks=dict(), server=server, id=CodeCompletionAgent.count
        )
        obj.active_task_id = obj.add_task(AgentTask("running", "Get user response", [], None))
        obj.wait_user_response_task = obj.tasks[active_task_id]
        obj.generate_response_task = obj.tasks[
            obj.add_task(AgentTask("done", "Generate response", [], None))
        ]
        return obj

    async def run(self, params: AgentRunParams) -> AgentRunResult:
        async def worker():
            while True:
                self.wait_user_response_task.status = "running"
                self.generate_response_task.status = "done"
                obj.active_task_id = self.wait_user_response_task.id
                self.send_progress(CodeCompletionProgress(tasks=self.tasks))

                user_response = await self.request_code_completion(self.state.messages)
                response = ""
                from asyncio import Lock

                response_lock = Lock()
                assert self.running
                async with response_lock:
                    self.wait_user_response_task.status = "done"
                    self.generate_response_task.status = "running"
                    obj.active_task_id = self.generate_response_task.id
                    await self.send_progress(CodeCompletionProgress(response=response, tasks=self.tasks))
                doc_text = self.document.text
                pos = self.cursor
                offset = None if pos is None else self.document.position_to_offset(pos)

                stream = await self.model.run_code_completion(
                    doc_text, self.state.messages, user_response, offset
                )

                async for delta in stream.text:
                    response += delta
                    async with response_lock:
                        await self.send_progress(CodeCompletionProgress(response=response))
                logger.info(f"{self} finished streaming response.")

                self.running = False
                async with response_lock:
                    await self.send_progress(response=response, done_streaming=True)
                    self.state.messages.append(CodeCompletionMessage.assistant(response))

        task = asyncio.create_task(worker())
        self.running = True
        try:
            return await task
        except asyncio.CancelledError as e:
            logger.info(f"{self} run task got cancelled")
            return f"I stopped! {e}"
        finally:
            self.running = False

    async def request_input(self) -> RequestInputResponse:
        response_fut = await self.server.request(
            f"morph/{self.agent_type}_{self.id}_request_input", request_input_request
        )
        return await response_fut

    async def request_code_completion(self, request_code_completion_request: RequestCodeCompletionRequest) -> RequestCodeCompletionResponse:
        response_fut = await self.server.request(
            f"morph/{self.agent_type}_{self.id}_request_code_completion", request_code_completion_request
        )
        return await response_fut

    async def send_progress(self, progress: AgentProgress) -> None:
        await self.notify("morph/{self.agent_type}_{self.id}_send_progress", progress)

    async def send_result(self):
        ...  # unreachable


if __name__ == "__main__":
    ...
