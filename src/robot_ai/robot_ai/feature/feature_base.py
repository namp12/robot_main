import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

logger = logging.getLogger("FeatureBase")


class FeatureBase(ABC):
    """
    Standard Abstract Base Class defining Feature Lifecycle Interface.
    Enforces clean setup, startup, pause, resume, stopping, cleanup, and release steps.
    """

    def __init__(self, name: str):
        self.name = name
        self._is_initialized = False
        self._is_ready = False
        self._is_running = False
        self._is_paused = False
        self._start_ts: float = 0.0

    @abstractmethod
    def on_initialize(self) -> bool:
        """Hook called when feature is initialized."""
        pass

    @abstractmethod
    def on_start(self) -> bool:
        """Hook called when feature starts running."""
        pass

    @abstractmethod
    def on_pause(self) -> bool:
        """Hook called when feature is paused."""
        pass

    @abstractmethod
    def on_resume(self) -> bool:
        """Hook called when feature resumes."""
        pass

    @abstractmethod
    def on_stop(self) -> bool:
        """Hook called when feature is stopping."""
        pass

    @abstractmethod
    def on_cleanup(self) -> bool:
        """Hook called during feature cleanup (cancel timers/workers)."""
        pass

    @abstractmethod
    def on_release(self) -> bool:
        """Hook called to release all held resources."""
        pass

    def initialize(self) -> bool:
        if not self._is_initialized:
            ok = self.on_initialize()
            if ok:
                self._is_initialized = True
                self._is_ready = True
            return ok
        return True

    def start(self) -> bool:
        if not self._is_initialized:
            if not self.initialize():
                return False
        if not self._is_running:
            ok = self.on_start()
            if ok:
                self._is_running = True
                self._is_paused = False
                self._start_ts = time.time()
            return ok
        return True

    def pause(self) -> bool:
        if self._is_running and not self._is_paused:
            ok = self.on_pause()
            if ok:
                self._is_paused = True
            return ok
        return True

    def resume(self) -> bool:
        if self._is_running and self._is_paused:
            ok = self.on_resume()
            if ok:
                self._is_paused = False
            return ok
        return True

    def stop(self) -> bool:
        if self._is_running or self._is_paused:
            stop_ok = self.on_stop()
            cleanup_ok = self.cleanup()
            release_ok = self.release()
            self._is_running = False
            self._is_paused = False
            return stop_ok and cleanup_ok and release_ok
        return True

    def cleanup(self) -> bool:
        return self.on_cleanup()

    def release(self) -> bool:
        ok = self.on_release()
        self._is_ready = False
        self._is_initialized = False
        return ok

    def is_running(self) -> bool:
        return self._is_running and not self._is_paused

    def is_ready(self) -> bool:
        return self._is_ready

    def get_running_duration(self) -> float:
        if self._is_running:
            return round(time.time() - self._start_ts, 1)
        return 0.0
