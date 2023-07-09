import asyncio
from asyncio import Future
from dataclasses import dataclass
from typing import Optional

@dataclass
class AgentTask:
    """
    Represents a task associated with an agent

    Attributes:
        description (str): Description of the task
        task (asyncio.Task): The main coroutine task to be executed
        started (bool): Indicates whether the main inner task has started execution
        _error (Optional[Exception]): Error encountered during task execution (if any)
        _cancelled (bool): Indicates whether the task has been cancelled
    """

    description: str
    task: asyncio.Task
    started: bool = False
    _error: Optional[Exception] = None
    _cancelled: bool = False

    async def run(self):
        """
        Runs the task coroutine and handles exceptions
        """
        self.started = True
        try:
            return await self.task
        except asyncio.CancelledError:
            self._cancelled = True
        except Exception as e:
            self._error = e

    def cancel(self):
        """
        Cancels the task
        """
        return self.task.cancel()

    @property
    def done(self) -> bool:
        """
        Returns whether the task is done
        """
        return self.task.done()

    @property
    def cancelled(self) -> bool:
        """
        Returns whether the task is cancelled
        """
        return self._cancelled or self.task.cancelled()

    @property
    def error(self) -> bool:
        """
        Returns whether an error occurred in the task
        """
        return self._error is not None

    @property
    def status(self):
        """
        Returns the status of the task

        Returns:
            str: The status of the task (scheduled, running, done, cancelled, error)
        """
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
