import asyncio
from asyncio import Future
from dataclasses import dataclass, field
from typing import Optional, Awaitable, Any, Iterable, Callable, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """
    Represents a task associated with an agent

    Attributes:
        description (str): Description of the task
        task: thunk returning a Task
        started (bool): Indicates whether the main inner task has started execution
        _error (Optional[Exception]): Error encountered during task execution (if any)
        _cancelled (bool): Indicates whether the task has been cancelled
    """

    description: str
    task: Callable[Any, Awaitable[Any]]
    args: Optional[Callable[Any, Awaitable[Iterable[Any]]]] = None
    kwargs: Optional[Callable[Any, Awaitable[Dict[Any, Any]]]] = None
    _task: Optional[asyncio.Task] = None
    _running: bool = False
    _error: Optional[Exception] = None
    _cancelled: bool = False

    async def run(self):
        """
        Runs the task coroutine and handles exceptions
        """
        if self._running:
            raise Exception("Task is already running")

        self._running = True
        try:
            args = [*(await self.args())] if self.args else []
            kwargs = {**(await self.kwargs())} if self.kwargs else dict()
            return await self.task(*args, **kwargs)
        except asyncio.CancelledError:
            self._cancelled = True
        except Exception as e:
            self._error = e
            logger.debug(f"[AgentTask] caught error: {e}")
        finally:
            self._running = False

    def cancel(self):
        """
        Cancels the task
        """
        if self._task:
            return self._task.cancel()
        self._cancelled = True

    @property
    def running(self) -> bool:
        return self._running

    @property
    def done(self) -> bool:
        """
        Returns whether the task is done
        """
        if self._task:
            return self._task.done()
        else:
            return False

    @property
    def cancelled(self) -> bool:
        """
        Returns whether the task is cancelled
        """
        return self._cancelled or (self._task.cancelled() if self._task else False)

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
        elif self._running:
            return "running"
        else:
            return "scheduled"
            return "scheduled"
            return "scheduled"
