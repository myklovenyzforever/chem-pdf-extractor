from __future__ import annotations

import hashlib
import json
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import (
    BAD_ROWS_EXCEL_NAME,
    BAD_ROWS_JSONL_NAME,
    CACHE_DIR_NAME,
    ERROR_LOG_NAME,
    ERROR_STATS_EXCEL_NAME,
    ERROR_STATS_JSONL_NAME,
    EXPORT_EXCLUDED_COLUMNS,
    EXTRACTION_CACHE_VERSION,
    FAILED_SOURCES_DIR_NAME,
    MARKDOWN_DIR_NAME,
    PARTIAL_JSONL_NAME,
    SUSPICIOUS_ROWS_EXCEL_NAME,
    SUSPICIOUS_ROWS_JSONL_NAME,
    OUTPUT_EXCEL_NAME,
    RuntimeDeps,
    add_stat,
    bad_row_min_fill_rate_from_config,
    eta_text,
    field_instructions,
    format_duration,
    short_error,
    stage_summary,
)
from .export import (
    append_jsonl,
    export_bad_rows_excel,
    export_excel,
    export_jsonl_excel,
    load_partial_rows,
    processed_paths_from_rows,
    write_jsonl,
)
from .diagnostics import append_diagnostic_log, log_exception
from .llm import (
    build_extraction_chain,
    choose_model,
    extract_with_cloud_api,
    get_ollama_models,
    labeled_rows,
    model_order,
    pydantic_to_dict,
    translate_item_batch_to_chinese_cloud,
)
from .pdf import (
    list_pdf_files,
    markdown_artifact_path,
    mineru_images_dir_from_markdown,
    read_pdf_as_markdown_with_mode,
    safe_output_name,
    save_markdown_artifacts,
    truncate_text,
)
from .quality import (
    filter_bad_data_rows,
    log_near_duplicates,
    log_suspicious_rows,
    rows_quality_score,
    quality_retry_hint,
    translate_rows_to_chinese,
)
from .text_safety import json_dumps_utf8, utf8_safe_obj


class JobState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.running = False
        self.stop_requested = False
        self.pause_requested = False
        self.total = 0
        self.done = 0
        self.success = 0
        self.failed = 0
        self.current_file = ""
        self.message = "等待任务"
        self.started_at = ""
        self.finished_at = ""
        self.output_path = ""
        self.error_log_path = ""
        self.partial_jsonl_path = ""
        self.logs: list[str] = []

    def reset(self, output_path: Path, error_log_path: Path, partial_jsonl_path: Path) -> None:
        with self.lock:
            self.running = True
            self.stop_requested = False
            self.pause_requested = False
            self.total = 0
            self.done = 0
            self.success = 0
            self.failed = 0
            self.current_file = ""
            self.message = "任务启动中"
            self.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.finished_at = ""
            self.output_path = str(output_path)
            self.error_log_path = str(error_log_path)
            self.partial_jsonl_path = str(partial_jsonl_path)
            self.logs = []

    def add_log(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        print(line)
        append_diagnostic_log("task.log", line)
        with self.lock:
            self.logs.append(line)
            self.logs = self.logs[-300:]

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            percent = int((self.done / self.total) * 100) if self.total else 0
            return {
                "running": self.running,
                "stop_requested": self.stop_requested,
                "pause_requested": self.pause_requested,
                "total": self.total,
                "done": self.done,
                "success": self.success,
                "failed": self.failed,
                "percent": percent,
                "current_file": self.current_file,
                "message": self.message,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "output_path": self.output_path,
                "error_log_path": self.error_log_path,
                "partial_jsonl_path": self.partial_jsonl_path,
                "logs": list(self.logs),
            }

    def request_stop(self) -> None:
        with self.lock:
            self.stop_requested = True
            self.message = "正在请求停止，当前文件结束后停止"

    def request_pause(self) -> None:
        with self.lock:
            self.pause_requested = True
            self.message = "正在请求暂停，当前文件结束后暂停"

    def request_resume(self) -> None:
        with self.lock:
            self.pause_requested = False
            if self.running:
                self.message = "已继续处理"


def state_update(state: JobState, **kwargs: Any) -> None:
    with state.lock:
        for key, value in kwargs.items():
            setattr(state, key, value)


def wait_while_paused(
    state: JobState, rows: list[dict[str, Any]], output_path: Path,
    runtime: RuntimeDeps, bad_rows_jsonl_path: Path | None = None,
    bad_rows_excel_path: Path | None = None,
) -> bool:
    exported = False
    while True:
        snapshot = state.snapshot()
        if snapshot["stop_requested"]:
            return True
        if not snapshot.get("pause_requested"):
            return False
        if not exported:
            export_excel(rows, output_path, runtime)
            if bad_rows_jsonl_path is not None and bad_rows_excel_path is not None:
                export_bad_rows_excel(bad_rows_jsonl_path, bad_rows_excel_path, runtime)
            state.add_log(f"已暂停，当前结果已导出：{output_path}")
            exported = True
        state_update(state, message="已暂停，点击继续后从当前进度接着处理")
        time.sleep(0.5)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()


def extraction_cache_path(
    input_dir: Path, pdf_path: Path, config: dict[str, Any],
    fields: list[dict[str, str]], markdown: str, text_used: str,
) -> Path:
    provider = str(config.get("llm_provider") or "cloud")
    model_name = str(config.get("cloud_model") if provider == "cloud" else config.get("model") or "").strip()
    cache_key = stable_hash({
        "version": EXTRACTION_CACHE_VERSION,
        "provider": provider, "model": model_name,
        "fields": fields,
        "pdf_mode": str(config.get("pdf_mode") or ""),
        "max_chars": int(config.get("max_chars") or 0),
        "markdown_hash": hashlib.sha1(markdown.encode("utf-8", errors="ignore")).hexdigest(),
        "text_hash": hashlib.sha1(text_used.encode("utf-8", errors="ignore")).hexdigest(),
    })
    return input_dir / CACHE_DIR_NAME / safe_output_name(pdf_path.stem) / f"{cache_key}.json"


def load_extraction_cache(cache_path: Path) -> list[dict[str, Any]] | None:
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        rows = payload.get("rows")
        if isinstance(rows, list) and all(isinstance(item, dict) for item in rows):
            return rows
    except Exception:
        return None
    return None


def save_extraction_cache(cache_path: Path, rows: list[dict[str, Any]]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    slim_rows = []
    cache_excluded = set(EXPORT_EXCLUDED_COLUMNS) | {"源文件名"}
    for row in rows:
        slim_rows.append(utf8_safe_obj({key: value for key, value in row.items() if key not in cache_excluded}))
    payload = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": slim_rows,
    }
    cache_path.write_text(json_dumps_utf8(payload, indent=2), encoding="utf-8")


def add_source_metadata(
    rows: list[dict[str, Any]], *, pdf_path: Path, provider: str,
    model_name: str, pdf_mode: str, markdown_chars_total: int,
    markdown_chars_used: int, was_truncated: bool, llm_service: str = "",
) -> None:
    record_count = len(rows)
    for record_index, row in enumerate(rows, start=1):
        row["源文件名"] = pdf_path.name
        row["source_path"] = str(pdf_path)
        row["record_index"] = record_index
        row["record_count"] = record_count
        row["llm_provider"] = provider
        if provider == "ollama":
            row["ollama_model"] = model_name
        if llm_service:
            row["llm_service"] = llm_service
        row["llm_model"] = model_name
        row["pdf_to_md_mode"] = pdf_mode
        row["markdown_chars_total"] = markdown_chars_total
        row["markdown_chars_used"] = markdown_chars_used
        row["was_truncated"] = was_truncated


def log_error(error_log_path: Path, pdf_path: Path, stage: str, exc: BaseException) -> None:
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    append_jsonl(
        error_log_path.with_name(ERROR_STATS_JSONL_NAME),
        {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "源文件名": pdf_path.name, "源文件路径": str(pdf_path),
            "失败环节": stage, "错误类型": type(exc).__name__,
            "错误原因": short_error(exc),
        },
    )
    with error_log_path.open("a", encoding="utf-8") as handle:
        handle.write("=" * 80 + "\n")
        handle.write(f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        handle.write(f"file: {pdf_path}\n")
        handle.write(f"stage: {stage}\n")
        handle.write(f"error: {repr(exc)}\n")
        handle.write(traceback.format_exc())
        handle.write("\n")


def copy_failed_source(pdf_path: Path, input_dir: Path) -> Path:
    try:
        relative_path = pdf_path.relative_to(input_dir)
    except ValueError:
        relative_path = Path(pdf_path.name)
    parent_parts = [
        safe_output_name(part)
        for part in relative_path.parent.parts
        if part not in {"", "."}
    ]
    target_dir = input_dir / FAILED_SOURCES_DIR_NAME / Path(*parent_parts)
    target_path = target_dir / safe_output_name(pdf_path.name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(pdf_path, target_path)
    return target_path


def record_failure(
    *, error_log_path: Path, pdf_path: Path, input_dir: Path,
    stage: str, exc: BaseException, state: JobState | None = None,
) -> None:
    log_error(error_log_path, pdf_path, stage, exc)
    copied_path = copy_failed_source(pdf_path, input_dir)
    if state is not None:
        state.add_log(f"失败环节：{stage}；原因：{short_error(exc)}；失败源文件已复制：{copied_path}")


def process_pdf(
    pdf_path: Path, input_dir: Path, config: dict[str, Any], runtime: RuntimeDeps,
    chains: list[tuple[str, Any]] | None, fields: list[dict[str, str]],
    key_to_label: dict[str, str], error_log_path: Path,
    state: JobState | None = None, progress_label: str = "",
    stage_stats: dict[str, float] | None = None,
) -> list[dict[str, Any]] | None:
    convert_started = time.perf_counter()
    cached_markdown_path = markdown_artifact_path(input_dir, pdf_path)
    markdown = ""
    actual_pdf_mode = str(config["pdf_mode"])
    bad_row_min_fill_rate = bad_row_min_fill_rate_from_config(config)

    if cached_markdown_path.exists() and cached_markdown_path.stat().st_size > 0:
        try:
            markdown = cached_markdown_path.read_text(encoding="utf-8", errors="replace")
            if state is not None:
                state.add_log(f"复用已有MD：{progress_label} {pdf_path.name} ({len(markdown)} 字符，路径：{cached_markdown_path})")
        except Exception as exc:
            if state is not None:
                state.add_log(f"已有MD读取失败，将重新转换：{cached_markdown_path}；原因：{short_error(exc)}")

    if not markdown:
        if cached_markdown_path.exists():
            if state is not None:
                state.add_log(f"已有MD为空或不可用，将重新转换：{cached_markdown_path}")
        try:
            markdown, actual_pdf_mode = read_pdf_as_markdown_with_mode(pdf_path, str(config["pdf_mode"]), runtime)
        except Exception as exc:
            record_failure(error_log_path=error_log_path, pdf_path=pdf_path, input_dir=input_dir, stage="pdf_to_markdown", exc=exc, state=state)
            return None
        add_stat(stage_stats, "pdf_to_md", time.perf_counter() - convert_started)
        source_images_dir = mineru_images_dir_from_markdown(markdown)
        markdown_path, _ = save_markdown_artifacts(markdown, pdf_path, input_dir, source_images_dir)
        if state is not None:
            state.add_log(
                f"PDF转MD完成：{progress_label} {pdf_path.name} "
                f"({format_duration(time.perf_counter() - convert_started)}，{len(markdown)} 字符，方式：{actual_pdf_mode}，已保存：{markdown_path})"
            )
    else:
        if markdown.startswith("<!-- MinerU output:"):
            actual_pdf_mode = "mineru"
        if state is not None:
            state.add_log(f"跳过PDF转MD：{progress_label} {pdf_path.name} (耗时 {format_duration(time.perf_counter() - convert_started)})")

    text_used, was_truncated = truncate_text(markdown, int(config["max_chars"]))
    instructions = field_instructions(fields)
    last_exc: BaseException | None = None
    provider = str(config.get("llm_provider") or "cloud")
    cloud_model = str(config.get("cloud_model") or config.get("model") or "").strip()
    cache_path = extraction_cache_path(input_dir, pdf_path, config, fields, markdown, text_used)
    cached_rows = load_extraction_cache(cache_path)
    if cached_rows is not None:
        add_stat(stage_stats, "extract_cache_hit")
        if state is not None:
            state.add_log(f"复用抽取缓存：{pdf_path.name}（{len(cached_rows)} 条记录）")
        add_source_metadata(
            cached_rows, pdf_path=pdf_path, provider=provider,
            model_name=cloud_model if provider == "cloud" else str(config.get("model") or ""),
            pdf_mode=actual_pdf_mode, markdown_chars_total=len(markdown),
            markdown_chars_used=len(text_used), was_truncated=was_truncated,
            llm_service=str(config.get("cloud_service_name") or "cloud") if provider == "cloud" else "",
        )
        return cached_rows

    if provider == "cloud":
        try:
            llm_started = time.perf_counter()
            rows = extract_with_cloud_api(pdf_path, config, fields, key_to_label, text_used)
            add_stat(stage_stats, "llm_extraction", time.perf_counter() - llm_started)
            quality_retry_used = False
            retry_hint = quality_retry_hint(rows, fields, bad_row_min_fill_rate)
            if retry_hint:
                try:
                    retry_started = time.perf_counter()
                    retry_rows = extract_with_cloud_api(pdf_path, config, fields, key_to_label, text_used, quality_hint=retry_hint)
                    add_stat(stage_stats, "quality_retry", time.perf_counter() - retry_started)
                    if rows_quality_score(retry_rows, fields) > rows_quality_score(rows, fields):
                        rows = retry_rows
                        quality_retry_used = True
                        if state is not None:
                            state.add_log(f"二次抽取改善结果：{pdf_path.name}")
                except Exception as exc:
                    log_error(error_log_path, pdf_path, "cloud_quality_retry", exc)
                    if state is not None:
                        state.add_log(f"二次抽取失败，保留首次结果：{pdf_path.name}")
            add_source_metadata(
                rows, pdf_path=pdf_path, provider="cloud", model_name=cloud_model,
                pdf_mode=actual_pdf_mode, markdown_chars_total=len(markdown),
                markdown_chars_used=len(text_used), was_truncated=was_truncated,
                llm_service=str(config.get("cloud_service_name") or "cloud"),
            )
            for row in rows:
                row["quality_retry_used"] = quality_retry_used
            save_extraction_cache(cache_path, rows)
            return rows
        except Exception as exc:
            record_failure(error_log_path=error_log_path, pdf_path=pdf_path, input_dir=input_dir, stage="cloud_llm_extraction", exc=exc, state=state)
            return None

    for model_name, chain in chains or []:
        try:
            llm_started = time.perf_counter()
            result = chain.invoke({
                "file_name": pdf_path.name, "field_instructions": instructions,
                "markdown_text": text_used, "quality_hint": "",
            })
            add_stat(stage_stats, "llm_extraction", time.perf_counter() - llm_started)
            rows = labeled_rows(pydantic_to_dict(result), fields, key_to_label)
            quality_retry_used = False
            retry_hint = quality_retry_hint(rows, fields, bad_row_min_fill_rate)
            if retry_hint:
                try:
                    retry_started = time.perf_counter()
                    retry_result = chain.invoke({
                        "file_name": pdf_path.name, "field_instructions": instructions,
                        "markdown_text": text_used, "quality_hint": f"二次核查要求：\n{retry_hint}",
                    })
                    add_stat(stage_stats, "quality_retry", time.perf_counter() - retry_started)
                    retry_rows = labeled_rows(pydantic_to_dict(retry_result), fields, key_to_label)
                    if rows_quality_score(retry_rows, fields) > rows_quality_score(rows, fields):
                        rows = retry_rows
                        quality_retry_used = True
                        if state is not None:
                            state.add_log(f"二次抽取改善结果：{pdf_path.name}")
                except Exception as exc:
                    log_error(error_log_path, pdf_path, "ollama_quality_retry", exc)
                    if state is not None:
                        state.add_log(f"二次抽取失败，保留首次结果：{pdf_path.name}")
            add_source_metadata(
                rows, pdf_path=pdf_path, provider="ollama", model_name=model_name,
                pdf_mode=actual_pdf_mode, markdown_chars_total=len(markdown),
                markdown_chars_used=len(text_used), was_truncated=was_truncated,
            )
            for row in rows:
                row["quality_retry_used"] = quality_retry_used
            save_extraction_cache(cache_path, rows)
            return rows
        except Exception as exc:
            last_exc = exc
            if not config.get("auto_fallback"):
                break

    if last_exc is not None:
        record_failure(error_log_path=error_log_path, pdf_path=pdf_path, input_dir=input_dir, stage="llm_extraction", exc=last_exc, state=state)
    return None


def run_extraction_job(config: dict[str, Any], runtime: RuntimeDeps, state: JobState) -> None:
    total_started = time.perf_counter()
    input_dir = Path(config["input_dir"]).expanduser().resolve()
    output_path = Path(config["output_path"]).expanduser().resolve()
    if output_path.suffix.lower() == ".xlsx":
        output_path = output_path.with_name(OUTPUT_EXCEL_NAME)
    else:
        output_path = output_path / OUTPUT_EXCEL_NAME
    error_log_path = output_path.with_name(ERROR_LOG_NAME)
    partial_jsonl_path = output_path.with_name(PARTIAL_JSONL_NAME)
    bad_rows_jsonl_path = output_path.with_name(BAD_ROWS_JSONL_NAME)
    bad_rows_excel_path = output_path.with_name(BAD_ROWS_EXCEL_NAME)
    suspicious_jsonl_path = output_path.with_name(SUSPICIOUS_ROWS_JSONL_NAME)
    suspicious_excel_path = output_path.with_name(SUSPICIOUS_ROWS_EXCEL_NAME)
    error_stats_jsonl_path = output_path.with_name(ERROR_STATS_JSONL_NAME)
    error_stats_excel_path = output_path.with_name(ERROR_STATS_EXCEL_NAME)
    stage_stats: dict[str, float] = {}

    state.reset(output_path, error_log_path, partial_jsonl_path)
    state.add_log("任务启动")

    try:
        if not partial_jsonl_path.exists():
            for stale_path in [bad_rows_jsonl_path, bad_rows_excel_path, suspicious_jsonl_path, suspicious_excel_path, error_stats_jsonl_path, error_stats_excel_path]:
                if stale_path.exists():
                    stale_path.unlink()

        if not input_dir.exists():
            raise RuntimeError(f"输入目录不存在：{input_dir}")

        pdf_files = list_pdf_files(input_dir, bool(config.get("recursive")))
        state_update(state, total=len(pdf_files), message="已扫描 PDF 文件")
        if not pdf_files:
            raise RuntimeError(f"没有找到 PDF 文件：{input_dir}")

        fields = config.get("fields") or []
        from .config import normalize_fields as _normalize_fields, build_dynamic_model as _build_dynamic_model
        fields = _normalize_fields(fields)
        extraction_model, key_to_label = _build_dynamic_model(fields, runtime)
        bad_row_min_fill_rate = bad_row_min_fill_rate_from_config(config)

        provider = str(config.get("llm_provider") or "cloud")
        available_models: list[str] = []

        if provider == "cloud":
            if not bool(config.get("cloud_active", False)):
                raise RuntimeError('云端 API 配置未激活。请勾选"激活此配置"。')
            selected_cloud_model = str(config.get("cloud_model") or config.get("model") or "").strip()
            if not selected_cloud_model:
                raise RuntimeError("云端模型名称为空。请在页面选择一个云端模型。")
            config["cloud_model"] = selected_cloud_model
            config["model"] = selected_cloud_model
            order = [selected_cloud_model]
            chains = None
        else:
            available_models = get_ollama_models(str(config["ollama_base_url"]))
            chosen_model = choose_model(str(config["model"]), available_models)
            order = model_order(chosen_model, available_models, bool(config.get("auto_fallback")))
            chains = [
                (item, build_extraction_chain(item, str(config["ollama_base_url"]), int(config["num_ctx"]), int(config["llm_timeout"]), runtime, extraction_model))
                for item in order
            ]

        translation_batch_translator = None
        translation_model_name = ""
        if bool(config.get("translate_to_chinese", True)):
            try:
                translation_base_url = str(config.get("cloud_base_url") or "").strip()
                translation_api_key = str(config.get("cloud_api_key") or "").strip()
                translation_model_name = str(config.get("cloud_model") or config.get("model") or "deepseek-ai/DeepSeek-V4-Pro").strip()
                if not translation_base_url or not translation_api_key or not translation_model_name:
                    raise RuntimeError("云端 API KEY、BASE URL 或模型名称为空。")
                translation_batch_translator = lambda batch: translate_item_batch_to_chinese_cloud(
                    translation_base_url, translation_api_key, translation_model_name, batch, int(config.get("llm_timeout") or 0),
                )
            except Exception as exc:
                state.add_log(f"云端中文翻译不可用，将保留原文：{exc}")

        rows, processed_paths = load_partial_rows(partial_jsonl_path)
        loaded_partial_count = len(rows)
        if rows:
            rows = filter_bad_data_rows(rows, fields, error_log_path, default_pdf_path=partial_jsonl_path, state=state, log_prefix="断点结果", min_fill_rate=bad_row_min_fill_rate)
            if len(rows) != loaded_partial_count:
                write_jsonl(partial_jsonl_path, rows)
            processed_paths = processed_paths_from_rows(rows)
        completed_paths = {str(path.resolve()).casefold() for path in pdf_files} & processed_paths
        if rows:
            state.add_log(f"检测到断点结果：已载入 {len(rows)} 条记录，跳过 {len(completed_paths)} 个已完成 PDF。")
            state_update(state, success=len(completed_paths))
        state.add_log(f"PDF 数量：{len(pdf_files)}")
        state.add_log(f"LLM 提供方：{provider}")
        if provider == "cloud":
            state.add_log(f"云端服务：{config.get('cloud_service_name') or 'cloud'}")
        state.add_log(f"模型：{', '.join(order)}")
        if translation_batch_translator is not None:
            state.add_log(f"云端中文翻译模型：{translation_model_name}")
        state.add_log(f"PDF 转换方式：{config['pdf_mode']}")
        state.add_log(f"坏数据阈值：填写率低于 {bad_row_min_fill_rate:.0%} 删除")
        state.add_log(f"MD 保存目录：{input_dir / MARKDOWN_DIR_NAME}")
        state.add_log(f"失败源文件目录：{input_dir / FAILED_SOURCES_DIR_NAME}")
        state.add_log(f"字段数量：{len(fields)}")

        for index, pdf_path in enumerate(pdf_files, start=1):
            if wait_while_paused(state, rows, output_path, runtime, bad_rows_jsonl_path, bad_rows_excel_path):
                state.add_log("收到停止请求，提前结束。")
                break
            if state.snapshot()["stop_requested"]:
                state.add_log("收到停止请求，提前结束。")
                break

            if str(pdf_path.resolve()).casefold() in completed_paths:
                state.add_log(f"[{index}/{len(pdf_files)}] 跳过已完成：{pdf_path.name}")
                state_update(state, done=index)
                continue

            state_update(state, current_file=pdf_path.name, message=f"处理中：{pdf_path.name}")
            state.add_log(f"[{index}/{len(pdf_files)}] {pdf_path.name}")
            pdf_started = time.perf_counter()

            pdf_rows = process_pdf(
                pdf_path, input_dir, config, runtime, chains, fields, key_to_label,
                error_log_path, state, f"[{index}/{len(pdf_files)}]", stage_stats,
            )
            if pdf_rows is None:
                state_update(state, failed=state.snapshot()["failed"] + 1)
                state.add_log(f"失败：{pdf_path.name}（耗时 {format_duration(time.perf_counter() - pdf_started)}）")
            else:
                if translation_batch_translator is not None:
                    try:
                        translate_started = time.perf_counter()
                        translated_count = translate_rows_to_chinese(pdf_rows, fields, translation_batch_translator)
                        add_stat(stage_stats, "translation", time.perf_counter() - translate_started)
                        if translated_count:
                            state.add_log(f"中文翻译：{pdf_path.name}（{translated_count} 个单元格）")
                    except Exception as exc:
                        log_error(error_log_path, pdf_path, "cloud_chinese_translation", exc)
                        state.add_log(f"中文翻译失败，保留原文：{pdf_path.name}")
                extracted_count = len(pdf_rows)
                pdf_rows = filter_bad_data_rows(pdf_rows, fields, error_log_path, default_pdf_path=pdf_path, state=state, log_prefix=pdf_path.name, min_fill_rate=bad_row_min_fill_rate)
                if not pdf_rows:
                    state_update(state, failed=state.snapshot()["failed"] + 1)
                    state.add_log(
                        f"坏数据：{pdf_path.name}（抽取到 {extracted_count} 条记录，但填写率均低于 {bad_row_min_fill_rate:.0%}，已删除，耗时 {format_duration(time.perf_counter() - pdf_started)}）"
                    )
                    state_update(state, done=index)
                    continue
                suspicious_count = log_suspicious_rows(pdf_rows, fields, suspicious_jsonl_path, default_pdf_path=pdf_path)
                if suspicious_count:
                    add_stat(stage_stats, "suspicious_rows", suspicious_count)
                    state.add_log(f"可疑数据：{pdf_path.name}（{suspicious_count} 条，详见 {SUSPICIOUS_ROWS_EXCEL_NAME}）")
                rows.extend(pdf_rows)
                for row in pdf_rows:
                    append_jsonl(partial_jsonl_path, row)
                state_update(state, success=state.snapshot()["success"] + 1)
                state.add_log(
                    f"成功：{pdf_path.name}（{len(pdf_rows)} 条记录，耗时 {format_duration(time.perf_counter() - pdf_started)}，{eta_text(total_started, index, len(pdf_files))}）"
                )
            state_update(state, done=index)

        duplicate_count = log_near_duplicates(rows, suspicious_jsonl_path)
        if duplicate_count:
            add_stat(stage_stats, "near_duplicates", duplicate_count)
            state.add_log(f"近重复检测：发现 {duplicate_count} 条疑似重复记录，详见 {SUSPICIOUS_ROWS_EXCEL_NAME}")
        export_excel(rows, output_path, runtime)
        state.add_log(f"Excel 已导出：{output_path}")
        export_bad_rows_excel(bad_rows_jsonl_path, bad_rows_excel_path, runtime)
        if bad_rows_excel_path.exists():
            state.add_log(f"坏数据审查表已导出：{bad_rows_excel_path}")
        if export_jsonl_excel(suspicious_jsonl_path, suspicious_excel_path, runtime):
            state.add_log(f"可疑数据审查表已导出：{suspicious_excel_path}")
        if export_jsonl_excel(error_stats_jsonl_path, error_stats_excel_path, runtime):
            state.add_log(f"错误统计表已导出：{error_stats_excel_path}")
        summary = stage_summary(stage_stats)
        if summary:
            state.add_log(f"阶段耗时统计：{summary}")
        state.add_log(f"总耗时：{format_duration(time.perf_counter() - total_started)}")
        state_update(state, message="任务完成")
    except Exception as exc:
        log_exception(exc, context="run_extraction_job")
        state.add_log(f"任务异常：{exc}")
        state.add_log("完整错误详见 logs/crash.log")
        try:
            export_jsonl_excel(error_stats_jsonl_path, error_stats_excel_path, runtime)
        except Exception:
            pass
        state.add_log(f"总耗时：{format_duration(time.perf_counter() - total_started)}")
        state_update(state, message=f"任务异常：{exc}")
    finally:
        state_update(state, running=False, pause_requested=False, finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
