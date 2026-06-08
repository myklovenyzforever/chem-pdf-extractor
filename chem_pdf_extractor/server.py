from __future__ import annotations

import html as html_lib
import json
import os
import socket
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
import webbrowser

from .config import (
    DEFAULT_CLOUD_BASE_URL,
    DEFAULT_CLOUD_MODEL,
    DEFAULT_CLOUD_MODEL_SUGGESTIONS,
    DEFAULT_CLOUD_SERVICE_NAME,
    DEFAULT_MAX_CHARS,
    DEFAULT_MODEL,
    DEFAULT_NUM_CTX,
    DEFAULT_OLLAMA_BASE_URL,
    BAD_ROW_MIN_FILL_RATE,
    RuntimeDeps,
    apply_cloud_config_defaults,
    default_input_dir,
    default_output_path,
    load_local_config,
    mask_api_key,
    save_local_config,
)
from .diagnostics import append_diagnostic_log, log_exception, log_startup_event
from .extractor import JobState, run_extraction_job, state_update
from .llm import choose_model, fetch_openai_compatible_models, get_ollama_models
from .text_safety import json_dumps_utf8

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_html_template() -> str:
    return (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")


def render_html(defaults: dict[str, Any], default_fields: list[dict[str, Any]]) -> str:
    html = load_html_template()
    html = html.replace("__DEFAULT_FIELDS_JSON__", json_dumps_utf8(default_fields))
    html = html.replace("__DEFAULT_CONFIG_JSON__", json_dumps_utf8(defaults))
    model_options = "\n".join(
        f'                <option value="{html_lib.escape(model)}">{html_lib.escape(model)}</option>'
        for model in DEFAULT_CLOUD_MODEL_SUGGESTIONS
    )
    html = html.replace("__DEFAULT_CLOUD_MODEL_OPTIONS__", model_options)
    return html


class ChemExtractorApp:
    def __init__(self, runtime: RuntimeDeps) -> None:
        self.runtime = runtime
        self.state = JobState()
        self.server: ThreadingHTTPServer | None = None


class RequestHandler(BaseHTTPRequestHandler):
    app: ChemExtractorApp

    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json_dumps_utf8(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8", errors="replace"))

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            local_config = load_local_config()
            defaults = {
                "input_dir": str(default_input_dir()),
                "output_path": str(default_output_path()),
                "llm_provider": "cloud",
                "model": DEFAULT_MODEL,
                "ollama_base_url": DEFAULT_OLLAMA_BASE_URL,
                "cloud_service_name": local_config.get("cloud_service_name") or DEFAULT_CLOUD_SERVICE_NAME,
                "cloud_model": local_config.get("cloud_model") or os.environ.get("CHEM_PDF_EXTRACTOR_MODEL") or DEFAULT_CLOUD_MODEL,
                "cloud_model_suggestions": DEFAULT_CLOUD_MODEL_SUGGESTIONS,
                "cloud_api_key": "",
                "cloud_base_url": local_config.get("cloud_base_url") or os.environ.get("CHEM_PDF_EXTRACTOR_BASE_URL") or DEFAULT_CLOUD_BASE_URL,
                "cloud_active": local_config.get("cloud_active", True),
                "recursive": True,
                "max_chars": DEFAULT_MAX_CHARS,
                "num_ctx": DEFAULT_NUM_CTX,
                "bad_row_min_fill_percent": int(BAD_ROW_MIN_FILL_RATE * 100),
            }
            from .config import DEFAULT_FIELDS
            html = render_html(defaults, DEFAULT_FIELDS)
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/api/status":
            self.send_json(self.app.state.snapshot())
            return

        if parsed.path == "/api/models":
            query = urllib.parse.parse_qs(parsed.query)
            base_url = query.get("base_url", [DEFAULT_OLLAMA_BASE_URL])[0]
            try:
                models = get_ollama_models(base_url)
                self.send_json({"ok": True, "models": models, "default_model": choose_model(DEFAULT_MODEL, models)})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc), "models": []}, status=200)
            return

        if parsed.path == "/api/config":
            self.send_json({"ok": True, "config": load_local_config()})
            return

        if parsed.path == "/api/init-config":
            local_config = load_local_config()
            raw_key = local_config.get("cloud_api_key") or os.environ.get("CHEM_PDF_EXTRACTOR_API_KEY") or os.environ.get("CHEM_EXTRACTOR_CLOUD_API_KEY") or ""
            self.send_json({"ok": True, "cloud_api_key_prefix": mask_api_key(raw_key)})
            return

        self.send_json({"ok": False, "error": "not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/config":
            try:
                config = self.read_json()
                if not str(config.get("api_key") or config.get("cloud_api_key") or "").strip():
                    existing = load_local_config()
                    config["api_key"] = existing.get("cloud_api_key", "")
                save_local_config(config)
                self.send_json({"ok": True})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)})
            return

        if parsed.path in {"/api/models", "/api/cloud-models"}:
            try:
                config = self.read_json()
                base_url = str(config.get("base_url") or DEFAULT_CLOUD_BASE_URL).strip()
                api_key = str(config.get("api_key") or "").strip()
                models = fetch_openai_compatible_models(base_url, api_key)
                default_model = DEFAULT_CLOUD_MODEL if DEFAULT_CLOUD_MODEL in models else models[0]
                self.send_json({"ok": True, "models": models, "default_model": default_model})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc), "models": []}, status=200)
            return

        if parsed.path == "/api/start":
            if self.app.state.snapshot()["running"]:
                self.send_json({"ok": False, "error": "已有任务正在运行"})
                return
            try:
                config = self.read_json()
                config.setdefault("input_dir", str(default_input_dir()))
                config.setdefault("output_path", str(default_output_path()))
                config.setdefault("llm_provider", "cloud")
                config.setdefault("model", DEFAULT_MODEL)
                config.setdefault("translate_to_chinese", True)
                config.setdefault("pdf_mode", "mineru")
                config.setdefault("max_chars", DEFAULT_MAX_CHARS)
                config.setdefault("num_ctx", DEFAULT_NUM_CTX)
                config.setdefault("llm_timeout", 0)
                config.setdefault("bad_row_min_fill_percent", int(BAD_ROW_MIN_FILL_RATE * 100))
                config.setdefault("ollama_base_url", DEFAULT_OLLAMA_BASE_URL)
                apply_cloud_config_defaults(config)
                config.setdefault("recursive", True)
                config.setdefault("auto_fallback", False)
                if str(config.get("llm_provider") or "cloud") == "cloud":
                    selected_cloud_model = str(config.get("cloud_model") or config.get("model") or "").strip()
                    if not selected_cloud_model:
                        selected_cloud_model = DEFAULT_CLOUD_MODEL
                    config["cloud_model"] = selected_cloud_model
                    config["model"] = selected_cloud_model
                thread = threading.Thread(target=_run_extraction_job_with_logging, args=(config, self.app.runtime, self.app.state), daemon=True)
                thread.start()
                self.send_json({"ok": True})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)})
            return

        if parsed.path == "/api/stop":
            self.app.state.request_stop()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/pause":
            self.app.state.request_pause()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/resume":
            self.app.state.request_resume()
            self.send_json({"ok": True})
            return

        if parsed.path == "/api/shutdown":
            self.app.state.request_stop()
            self.send_json({"ok": True})
            if self.app.server is not None:
                threading.Thread(target=self.app.server.shutdown, daemon=True).start()
            return

        self.send_json({"ok": False, "error": "not found"}, status=404)


def find_free_port(preferred_port: int) -> int:
    candidates = list(range(preferred_port, preferred_port + 50)) + [0]
    last_error: OSError | None = None
    for port in candidates:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
                return int(sock.getsockname()[1])
        except OSError as exc:
            last_error = exc
            continue
    raise RuntimeError(f"无法找到可用本地端口，最后一次错误：{last_error}")


def _run_extraction_job_with_logging(config: dict[str, Any], runtime: RuntimeDeps, state: JobState) -> None:
    try:
        run_extraction_job(config, runtime, state)
    except Exception as exc:
        log_exception(exc, context="background_extraction_thread")
        try:
            state.add_log("后台任务异常，详见 logs/crash.log")
            state_update(state, running=False, message="任务异常，详见 logs/crash.log")
        except Exception:
            pass


def start_web_app(port: int, auto_install: bool, open_browser: bool = False) -> int:
    from .config import ensure_dependencies, import_runtime_dependencies
    log_startup_event(mode="web", extra={"requested_port": port, "open_browser": open_browser})
    server: ThreadingHTTPServer | None = None
    try:
        append_diagnostic_log("startup.log", "checking dependencies")
        ensure_dependencies(auto_install=auto_install)
        append_diagnostic_log("startup.log", "importing runtime dependencies")
        runtime = import_runtime_dependencies()
        app = ChemExtractorApp(runtime)
        actual_port = find_free_port(port)
        server = ThreadingHTTPServer(("127.0.0.1", actual_port), RequestHandler)
        app.server = server
        RequestHandler.app = app
        url = f"http://127.0.0.1:{actual_port}/"
        append_diagnostic_log(
            "startup.log",
            f"local Web UI URL: {url}; selected port: {actual_port}; open_browser: {open_browser}",
        )
        print("Chem-PDF-Extractor 页面已启动：")
        print(url)
        if open_browser:
            webbrowser.open(url)
        else:
            print("请复制上面的地址到浏览器打开。")
        print('关闭浏览器标签页不会停止正在运行的本地服务；需要停止任务请点页面里的”停止任务”。')
        server.serve_forever()
        append_diagnostic_log("startup.log", "web server serve_forever ended")
    except Exception as exc:
        log_exception(exc, context="web_server")
        raise
    finally:
        if server is not None:
            server.server_close()
            append_diagnostic_log("startup.log", "web server closed")
            print("Chem-PDF-Extractor 本地服务已关闭。")
    return 0
