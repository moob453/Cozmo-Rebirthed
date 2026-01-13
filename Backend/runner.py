"""Thread-based module runner.

Example usage:

    from Backend.runner import ThreadManager

    manager = ThreadManager()
    manager.add_module_from_path('Backend.sample_worker')
    shared_data = {}
    manager.start_all(shared_data)

    manager.stop_all()
"""

from __future__ import annotations

import importlib
import inspect
import logging
import multiprocessing as mp
import threading
import time
from types import ModuleType
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# --- Process support -----------------------------------------------
def _process_entry(module_path: str):
    """Entry function run inside spawned processes.

    It imports the module and tries to call `run`, `start` or `init`.
    """
    # Configure simple logging format that includes PID so we can see which
    # process is emitting logs (helps debug lingering processes).
    try:
        logging.basicConfig(format='%(asctime)s %(process)d %(name)s %(levelname)s: %(message)s')
    except Exception:
        pass
    try:
        mod = importlib.import_module(module_path)
    except Exception:
        logger.exception("Failed to import module %s in child process", module_path)
        return

    # Support common entry point names used in this project (run/start/init/runtime/main)
    fn = (getattr(mod, 'run', None)
          or getattr(mod, 'start', None)
          or getattr(mod, 'init', None)
          or getattr(mod, 'runtime', None)
          or getattr(mod, 'main', None))
    if fn is None:
        logger.warning("No runnable entry found in module %s (tried run/start/init/runtime/main)", module_path)
        return

    try:
        logger.info("Invoking %s.%s() in child process", module_path, getattr(fn, '__name__', '<callable>'))
        sig = inspect.signature(fn)
        if len(sig.parameters) == 2:
            ev = mp.Event()
            fn({}, ev)
        elif len(sig.parameters) == 1:
            fn({})
        else:
            fn()
    except Exception:
        logger.exception("Exception while running %s in child process", module_path)


class ProcessModule:
    """Represents a module running in its own process."""

    def __init__(self, name: str, module_path: str):
        self.name = name
        self.module_path = module_path
        self.process: Optional[mp.Process] = None

    def start(self):
        if self.process is not None and self.process.is_alive():
            logger.debug("Process %s already running", self.name)
            return
        p = mp.Process(target=_process_entry, args=(self.module_path,), name=f"ProcModule-{self.name}")
        p.start()
        self.process = p
        logger.info("Started process module %s (pid=%s)", self.name, getattr(p, 'pid', None))

    def stop(self, timeout: float = 2.0):
        if self.process is None:
            return
        if self.process.is_alive():
            try:
                logger.info("Terminating process %s (pid=%s)", self.name, getattr(self.process, 'pid', None))
                self.process.terminate()
                self.process.join(timeout)
                if self.process.is_alive():
                    # Try more forceful methods when terminate() didn't work
                    try:
                        kill = getattr(self.process, 'kill', None)
                        if callable(kill):
                            logger.info("Killing process %s (pid=%s)", self.name, getattr(self.process, 'pid', None))
                            kill()
                            self.process.join(timeout)
                    except Exception:
                        logger.exception("Error calling kill() on process %s", self.name)

                    # On Windows, fall back to taskkill to remove process tree
                    if self.process.is_alive():
                        try:
                            import os
                            import subprocess
                            if os.name == 'nt' and getattr(self.process, 'pid', None) is not None:
                                logger.info("Using taskkill to forcefully kill PID %s", self.process.pid)
                                subprocess.run(['taskkill', '/PID', str(self.process.pid), '/T', '/F'], check=False)
                                # give it a moment
                                self.process.join(0.5)
                        except Exception:
                            logger.exception("Error running taskkill for process %s", self.name)
            except Exception:
                logger.exception("Error terminating process module %s", self.name)
        self.process = None
        logger.info("Stopped process module %s", self.name)


class Runner:
    """Unified manager for thread- and process-based modules.

    Methods:
        run(module_or_path, mode='process'|'thread'|'main', name=None)
        stop(name)
        kill_all()
        status()
    """

    def __init__(self):
        self._threads = ThreadManager()
        self._processes: Dict[str, ProcessModule] = {}
        self._lock = threading.Lock()

    def run(self, module_or_path: "str|Callable", *, name: Optional[str] = None, mode: str = 'process'):
        """Run a module or callable.

        - If `module_or_path` is a string, treat it as a dotted module path and import it in the child process or main thread.
        - If `module_or_path` is a callable and mode=='thread', run it in a thread.
        - If mode=='main', call the module/callable in the current thread (blocking).
        """
        if mode not in ('process', 'thread', 'main'):
            raise ValueError('mode must be one of process, thread, main')

        # Determine name
        if name is None:
            if isinstance(module_or_path, str):
                name = module_or_path
            else:
                name = getattr(module_or_path, '__name__', repr(module_or_path))

        if mode == 'process':
            if isinstance(module_or_path, str):
                pm = ProcessModule(name=name, module_path=module_or_path)
                with self._lock:
                    self._processes[name] = pm
                pm.start()
                return pm
            else:
                def _callable_entry(func):
                    try:
                        func()
                    except Exception:
                        logger.exception('Exception in callable process')

                p = mp.Process(target=_callable_entry, args=(module_or_path,), name=f"ProcCallable-{name}")
                p.start()
                pm = ProcessModule(name=name, module_path='<callable>')
                pm.process = p
                with self._lock:
                    self._processes[name] = pm
                return pm

        if mode == 'thread':
            if isinstance(module_or_path, str):
                return self._threads.add_module_from_path(module_path=module_or_path, name=name)
            else:
                return self._threads.add_callable(name=name, func=module_or_path)

        # mode == 'main'
        if isinstance(module_or_path, str):
            mod = importlib.import_module(module_or_path)
            fn = getattr(mod, 'init', None) or getattr(mod, 'run', None) or getattr(mod, 'start', None)
            if fn is None:
                raise RuntimeError('No runnable entry found in module %s' % module_or_path)
            return fn()
        else:
            return module_or_path()

    def stop(self, name: str, timeout: float = 2.0):
        with self._lock:
            if name in self._processes:
                self._processes[name].stop(timeout)
                del self._processes[name]
                return
            # Try threads
            try:
                self._threads.stop(name, timeout)
            except KeyError:
                raise KeyError(name)

    def kill_all(self):
        """Stop all managed processes and threads."""
        with self._lock:
            procs_snapshot = list(self._processes.items())
            for name, pm in procs_snapshot:
                try:
                    pm.stop()
                except Exception:
                    logger.exception('Failed to stop process %s', name)
            # Keep snapshot for lingering check, then clear registry
            self._processes.clear()

        # stop threads too
        try:
            self._threads.stop_all()
        except Exception:
            logger.exception('Failed to stop threads')
        # Give processes a moment to terminate, then report any lingering ones
        time.sleep(0.2)
        lingering = [name for name, pm in procs_snapshot if pm.process is not None and pm.process.is_alive()]
        if lingering:
            logger.warning('Lingering processes after kill_all(): %s', lingering)

    def list_modules(self):
        with self._lock:
            return list(self._processes.keys()) + self._threads.list_modules()

    def status(self):
        status = {}
        with self._lock:
            for name, pm in self._processes.items():
                status[name] = bool(pm.process is not None and pm.process.is_alive())
        status.update(self._threads.status())
        return status


class ThreadModule:
    """Represents a module (or callable) running in its own thread."""

    def __init__(self, name: str, target: Optional[Callable] = None, module: Optional[ModuleType] = None, run_name: str = 'run'):
        self.name = name
        self.module = module
        self.target = target
        self.run_name = run_name
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self._started = False

    def _resolve_callable(self) -> Optional[Callable]:
        if self.target is not None:
            return self.target
        if self.module is None:
            return None
        # Prefer `run`, then `start`.
        fn = getattr(self.module, self.run_name, None)
        if fn is not None:
            return fn
        fn = getattr(self.module, 'start', None)
        if fn is not None:
            return fn
        return None

    def start(self, shared_data: Dict[str, Any]):
        if self._started:
            logger.debug("Module %s already started", self.name)
            return

        fn = self._resolve_callable()
        if fn is None:
            raise RuntimeError(f"No callable found for module {self.name}")

        def entry():
            try:
                sig = inspect.signature(fn)
                params = sig.parameters
                # If function accepts shared_data and stop_event
                if len(params) == 2:
                    fn(shared_data, self.stop_event)
                # Accept single shared_data
                elif len(params) == 1:
                    fn(shared_data)
                # No params
                else:
                    fn()
            except Exception as exc:  # Keep thread alive until stopped by external means
                logger.exception("Exception in module %s: %s", self.name, exc)

        self.thread = threading.Thread(target=entry, name=f"ThreadModule-{self.name}", daemon=True)
        self.stop_event.clear()
        self.thread.start()
        self._started = True
        logger.info("Started module %s", self.name)

    def stop(self, timeout: float = 2.0):
        if not self._started:
            return
        # Signal the running function
        self.stop_event.set()

        # If the module provides a stop() function, call it
        if self.module is not None:
            stop_fn = getattr(self.module, 'stop', None)
            if callable(stop_fn):
                try:
                    stop_fn()
                except Exception:
                    logger.exception("Error calling stop() on module %s", self.name)

        # Join thread
        if self.thread is not None:
            self.thread.join(timeout)
            if self.thread.is_alive():
                logger.warning("Module %s did not stop within timeout", self.name)
            else:
                logger.info("Module %s stopped cleanly", self.name)

        self._started = False


class ThreadManager:
    """Manage multiple ThreadModule instances."""

    def __init__(self):
        self._modules: Dict[str, ThreadModule] = {}
        self._lock = threading.Lock()

    def add_module_from_path(self, module_path: str, name: Optional[str] = None, run_name: str = 'run') -> ThreadModule:
        """Import a module by dotted path and add it.

        The module should export `run(shared_data, stop_event)` or `start(shared_data)`.
        """
        mod = importlib.import_module(module_path)
        if name is None:
            name = module_path
        tm = ThreadModule(name=name, module=mod, run_name=run_name)
        with self._lock:
            self._modules[name] = tm
        logger.debug("Added module %s from path %s", name, module_path)
        return tm

    def add_callable(self, name: str, func: Callable) -> ThreadModule:
        tm = ThreadModule(name=name, target=func)
        with self._lock:
            self._modules[name] = tm
        logger.debug("Added callable module %s", name)
        return tm

    def start_all(self, shared_data: Dict[str, Any]):
        with self._lock:
            for tm in list(self._modules.values()):
                try:
                    tm.start(shared_data)
                except Exception:
                    logger.exception("Failed to start module %s", tm.name)

    def stop_all(self, timeout: float = 2.0):
        with self._lock:
            for tm in list(self._modules.values()):
                try:
                    tm.stop(timeout)
                except Exception:
                    logger.exception("Failed to stop module %s", tm.name)

    def start(self, name: str, shared_data: Dict[str, Any]):
        with self._lock:
            tm = self._modules.get(name)
            if tm is None:
                raise KeyError(name)
            tm.start(shared_data)

    def stop(self, name: str, timeout: float = 2.0):
        with self._lock:
            tm = self._modules.get(name)
            if tm is None:
                raise KeyError(name)
            tm.stop(timeout)

    def list_modules(self):
        with self._lock:
            return list(self._modules.keys())

    def status(self) -> Dict[str, bool]:
        with self._lock:
            return {name: bool(tm._started and tm.thread is not None and tm.thread.is_alive()) for name, tm in self._modules.items()}


# Module-level default runner for convenience (defined after ThreadManager)
default_runner = Runner()


def run(module_or_path: "str|Callable", *, name: Optional[str] = None, mode: str = 'process'):
    return default_runner.run(module_or_path, name=name, mode=mode)


def stop(name: str, timeout: float = 2.0):
    return default_runner.stop(name, timeout)


def kill_all():
    return default_runner.kill_all()


def status():
    return default_runner.status()


def list_modules():
    return default_runner.list_modules()