from dataclasses import dataclass
import asyncio
from asyncio import Future
from typing import Optional

"""
each Agent should have a tree of AgentTasks
top-level AgentTask is the Agent's entry point and is named after the agent
each Task wraps a coroutine which represents some part of the Agent's execution
the status of that coroutine is precisely the status of that task
the agent is done when all its subtasks are done, etc
"""

@dataclass
class AgentTask:
    description: str
    task: asyncio.Task
    started: bool = False
    _error: Optional[Exception] = None
    _cancelled: bool = False

    async def run(self):
        self.started = True
        try:
            return await self.task
        except asyncio.CancelledError:
            self._cancelled = True
        
        except Exception as e:
            self._error = e

    def cancel(self):
        return self.task.cancel()

    @property
    def done(self) -> bool:
        return self.task.done()

    @property
    def cancelled(self) -> bool:
        return self._cancelled or self.task.cancelled()

    @property
    def error(self) -> bool:
        return self._error is not None
    
    @property
    def status(self):
        if self.error:
            return "error"
        elif self.cancelled:
            return "cancelled"
        elif self.done:
            return "done"
        elif self.started:
            return "running"
        else:
            return "scheduled"
    
