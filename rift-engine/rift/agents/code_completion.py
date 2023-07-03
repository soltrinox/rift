from dataclasses import dataclass
from abc import ABC
from typing import ClassVar, Dict
from rift.lsp import LspServer as BaseLspServer, rpc_method
from rift.agents.abstract import Agent

@dataclass
class ChatAgent(Agent):
    count: ClassVar[int] = 0

    @classmethod
    def create(cls, state, tasks, server, active_task_id=None):
        ChatAgent.count += 1
        return ChatAgent(state, tasks, server, id=ChatAgent.count)

    async def run(self, params: AgentRunParams) -> AgentRunResult:
        async def worker():
            response = ""
            from asyncio import Lock

            response_lock = Lock()
            assert self.running
            async with response_lock:
                await self.send_progress(response)
            doc_text = self.document.text
            pos = self.cursor
            offset = None if pos is None else self.document.position_to_offset(pos)

            stream = await self.model.run_chat(doc_text, self.cfg.messages, self.cfg.message, offset)

            async for delta in stream.text:
                response += delta
                async with response_lock:
                    await self.send_progress(response)
            logger.info(f"{self} finished streaming response.")

            self.running = False
            async with response_lock:
                await self.send_progress(response, done=True)

        
        task = asyncio.create_task(worker())
        self.running = True
        try:
            return await task
        except asyncio.CancelledError as e:
            logger.info(f"{self} run task got cancelled")
            return f"I stopped! {e}"
        finally:
            self.running = False

    async def request_input(self) -> ...:
        # TODO

    async def request_chat(self) -> ...:
        # TODO

    async def send_progress(self) -> ...:
        # TODO

    async def send_result(self) -> ...:
        # TODO

if __name__ == "__main__":
    ...
