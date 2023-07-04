from dataclasses import dataclass
from abc import ABC
from typing import ClassVar, Dict
from rift.lsp import LspServer as BaseLspServer, rpc_method
from rift.agents.abstract import Agent, AgentTask, AgentProgress, RequestChatRequest
from rift.llm.openai_types import Message as ChatMessage

@dataclass
class ChatProgress(AgentProgress): # reports what tasks are active and responsible for reporting new tasks
    response: Optional[str] = None
    done_streaming: bool = False

@dataclass
class ChatAgentState(Agent):
    messages: List[ChatMessage]

@dataclass
class ChatAgent(Agent):
    agent_id: str
    count: ClassVar[int] = 0
    agent_type: str = "chat"

    @classmethod
    def create(cls, messages, server, task: Optional[AgentTask] = None):
        ChatAgent.count += 1
        obj = ChatAgent(state=ChatAgentState(messages=messages), tasks=dict(), server=server, id=ChatAgent.count)
        if task is not None:
            obj.active_task_id = obj.add_task(task)
        return obj

    async def run(self, params: AgentRunParams) -> AgentRunResult:
        async def worker():
            while True:
                user_response = await self.request_chat(self.state.messages)
                response = ""
                from asyncio import Lock

                response_lock = Lock()
                assert self.running
                async with response_lock:
                    await self.send_progress(response)
                doc_text = self.document.text
                pos = self.cursor
                offset = None if pos is None else self.document.position_to_offset(pos)

                stream = await self.model.run_chat(doc_text, self.state.messages, user_response, offset)

                async for delta in stream.text:
                    response += delta
                    async with response_lock:
                        await self.send_progress(response)
                logger.info(f"{self} finished streaming response.")

                self.running = False
                async with response_lock:
                    await self.send_progress(response, done=True)
                    self.state.messages.append(ChatMessage.assistant(response))


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
        response_fut = await self.server.request(f"morph/{self.agent_type}_{self.agent_id}_request_input", request_input_request)
        return await response_fut

    async def request_chat(self, request_chat_request: RequestChatRequest) -> RequestChatResponse:
        response_fut = await self.server.request(f"morph/{self.agent_type}_{self.agent_id}_request_chat", request_chat_request)
        return await response_fut

    async def send_progress(self, progress: AgentProgress) -> None:
        await self.notify("morph/{self.agent_type}_{self.agent_id}_send_progress", progress)

    async def send_result(self):
        ... # unreachable

if __name__ == "__main__":
    ...
