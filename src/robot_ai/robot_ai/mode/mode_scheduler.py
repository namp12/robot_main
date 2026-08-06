import time
import threading
from dataclasses import dataclass
from typing import List, Callable, Optional
from robot_ai.mode_manager.mode_types import RobotMode


@dataclass
class ScheduledTask:
    task_id: str
    target_mode: RobotMode
    execute_at_ts: float
    reason: str


class ModeScheduler:
    """Schedules one-shot or delayed mode switches."""

    def __init__(self, callback: Optional[Callable[[RobotMode, str], None]] = None):
        self.callback = callback
        self._tasks: List[ScheduledTask] = []
        self._lock = threading.Lock()

    def schedule_mode_switch(self, target_mode: RobotMode, delay_sec: float, reason: str = "") -> str:
        task_id = f"task_{int(time.time() * 1000)}"
        exec_ts = time.time() + delay_sec
        task = ScheduledTask(task_id, target_mode, exec_ts, reason)
        with self._lock:
            self._tasks.append(task)
        return task_id

    def check_and_execute(self):
        now = time.time()
        with self._lock:
            due = [t for t in self._tasks if t.execute_at_ts <= now]
            self._tasks = [t for t in self._tasks if t.execute_at_ts > now]

        for t in due:
            if self.callback:
                try:
                    self.callback(t.target_mode, f"Scheduler task: {t.task_id} ({t.reason})")
                except Exception:
                    pass
