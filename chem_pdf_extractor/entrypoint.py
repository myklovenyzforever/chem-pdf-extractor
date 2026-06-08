from __future__ import annotations

from .app import main
from .diagnostics import (
    append_diagnostic_log,
    install_global_exception_hook,
    log_exception,
    log_process_exit,
    log_startup_event,
)


def run(mode: str = "entrypoint") -> int:
    install_global_exception_hook()
    log_startup_event(mode=mode)
    exit_code = 0
    try:
        exit_code = int(main() or 0)
        return exit_code
    except KeyboardInterrupt:
        append_diagnostic_log("startup.log", "Interrupted by user.")
        print("\nInterrupted by user.")
        exit_code = 130
        return exit_code
    except SystemExit as exc:
        code = exc.code
        if code is None:
            exit_code = 0
        elif isinstance(code, int):
            exit_code = code
        else:
            print(code)
            exit_code = 1
        return exit_code
    except Exception as exc:
        log_exception(exc, context="top_level")
        print("Fatal error. See logs/crash.log for details.")
        exit_code = 1
        return exit_code
    finally:
        log_process_exit(exit_code)
