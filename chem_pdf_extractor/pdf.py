from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .config import (
    MARKDOWN_DIR_NAME,
    MAX_ARTIFACT_NAME_CHARS,
    MINERU_DEFAULT_BACKEND,
    MINERU_DEFAULT_FORMULA,
    MINERU_DEFAULT_METHOD,
    MINERU_DEFAULT_TABLE,
    MINERU_EXE,
    MINERU_OUTPUT_ROOT,
    RuntimeDeps,
    short_error,
)


def safe_output_name(name: str, max_chars: int = MAX_ARTIFACT_NAME_CHARS) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", name).strip().strip(".")
    if len(cleaned) > max_chars:
        digest = hashlib.sha1(cleaned.encode("utf-8", errors="ignore")).hexdigest()[:8]
        cleaned = f"{cleaned[: max_chars - 9].rstrip()}-{digest}"
    return cleaned or "document"


def markdown_artifact_dir(input_dir: Path, pdf_path: Path) -> Path:
    try:
        relative_path = pdf_path.relative_to(input_dir)
    except ValueError:
        relative_path = Path(pdf_path.name)
    parent_parts = [
        safe_output_name(part)
        for part in relative_path.parent.parts
        if part not in {"", "."}
    ]
    return input_dir / MARKDOWN_DIR_NAME / Path(*parent_parts) / safe_output_name(pdf_path.stem)


def markdown_artifact_path(input_dir: Path, pdf_path: Path) -> Path:
    return markdown_artifact_dir(input_dir, pdf_path) / f"{safe_output_name(pdf_path.stem)}.md"


def copy_image_artifacts(source_images_dir: Path | None, target_images_dir: Path) -> None:
    if source_images_dir is None or not source_images_dir.exists():
        return
    for item in source_images_dir.iterdir():
        target = target_images_dir / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        elif item.is_file():
            shutil.copy2(item, target)


def mineru_images_dir_from_markdown(markdown: str) -> Path | None:
    match = re.match(r"\s*<!-- MinerU output: (.*?) -->", markdown)
    if not match:
        return None
    markdown_path = Path(match.group(1).strip())
    output_root = markdown_path.parent.parent
    candidates = [
        markdown_path.parent / "images",
        output_root / "images",
        *output_root.rglob("images"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def save_markdown_artifacts(
    markdown: str,
    pdf_path: Path,
    input_dir: Path,
    source_images_dir: Path | None = None,
) -> tuple[Path, Path]:
    artifact_dir = markdown_artifact_dir(input_dir, pdf_path)
    images_dir = artifact_dir / "images"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = markdown_artifact_path(input_dir, pdf_path)
    markdown_path.write_text(markdown, encoding="utf-8")
    copy_image_artifacts(source_images_dir, images_dir)
    return markdown_path, images_dir


def markdown_text_char_count(markdown: str) -> int:
    return len(re.findall(r"[A-Za-z0-9一-鿿]", markdown))


def markdown_table_line_count(markdown: str) -> int:
    return sum(1 for line in markdown.splitlines() if line.count("|") >= 2)


def markdown_needs_mineru(markdown: str) -> bool:
    char_count = markdown_text_char_count(markdown)
    if char_count < 1200:
        return True
    lower = markdown.lower()
    table_mentions = lower.count("table") + lower.count("表")
    if table_mentions >= 2 and markdown_table_line_count(markdown) < 2:
        return True
    image_mentions = len(re.findall(r"!\[|<image|\.(?:png|jpg|jpeg)", lower))
    return image_mentions >= 3 and char_count < 8000


def run_mineru_to_markdown(pdf_path: Path) -> str:
    mineru_command = str(MINERU_EXE)
    if not MINERU_EXE.exists() and shutil.which(mineru_command) is None:
        raise FileNotFoundError(
            f"未找到 MinerU 可执行文件：{MINERU_EXE}。请确认 MinerU 已部署，或设置 MINERU_EXE 环境变量。"
        )
    job_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}_{abs(hash(str(pdf_path))) % 1000000:06d}"
    job_root = MINERU_OUTPUT_ROOT / job_id
    input_dir = job_root / "input"
    output_dir = job_root / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_input = input_dir / "input.pdf"
    shutil.copy2(pdf_path, safe_input)
    command = [
        mineru_command, "-p", str(safe_input), "-o", str(output_dir),
        "-b", os.environ.get("MINERU_BACKEND", MINERU_DEFAULT_BACKEND),
        "-m", os.environ.get("MINERU_METHOD", MINERU_DEFAULT_METHOD),
    ]
    formula = os.environ.get("MINERU_FORMULA", MINERU_DEFAULT_FORMULA)
    if formula:
        command.extend(["-f", formula])
    table = os.environ.get("MINERU_TABLE", MINERU_DEFAULT_TABLE)
    if table:
        command.extend(["-t", table])
    env = os.environ.copy()
    env.setdefault("MINERU_MODEL_SOURCE", "modelscope")
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    env.setdefault("PYTHONUTF8", "1")
    timeout_raw = os.environ.get("MINERU_TIMEOUT_SECONDS", "").strip()
    timeout = int(timeout_raw) if timeout_raw.isdigit() and int(timeout_raw) > 0 else None
    result = subprocess.run(
        command, cwd=str(job_root), env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    if result.returncode != 0:
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        raise RuntimeError(f"MinerU 解析失败，工作目录：{job_root}\n{combined[-4000:]}")
    markdown_files = sorted(output_dir.rglob("*.md"), key=lambda path: path.stat().st_size, reverse=True)
    if not markdown_files:
        generated = "\n".join(str(path) for path in output_dir.rglob("*"))
        raise FileNotFoundError(f"MinerU 未生成 Markdown 文件，工作目录：{job_root}\n已生成文件：\n{generated}")
    markdown_path = markdown_files[0]
    content = markdown_path.read_text(encoding="utf-8", errors="replace")
    return f"<!-- MinerU output: {markdown_path} -->\n\n{content}"


RELEVANT_TEXT_KEYWORDS = (
    "abstract", "experiment", "experimental", "method", "materials",
    "results", "discussion", "table", "figure", "scheme", "catalyst",
    "reaction", "temperature", "pressure", "conversion", "selectivity",
    "yield", "gas hourly space velocity", "ghsv", "whsv",
    "工艺", "实验", "方法", "结果", "表", "图", "催化", "反应",
    "温度", "压力", "转化率", "选择性", "产率", "空速",
)


def relevant_line_score(line: str) -> int:
    stripped = line.strip()
    if not stripped:
        return 0
    lower = stripped.lower()
    score = 0
    if "|" in stripped:
        score += 3
    if re.match(r"^\s{0,3}#{1,6}\s+", stripped):
        score += 2
    for keyword in RELEVANT_TEXT_KEYWORDS:
        if keyword in lower:
            score += 2
    return score


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False
    head_budget = max(4000, int(max_chars * 0.35))
    tail_budget = max(1500, int(max_chars * 0.08))
    middle_budget = max_chars - head_budget - tail_budget
    if middle_budget <= 0:
        return text[:max_chars], True
    pieces: list[str] = [text[:head_budget]]
    used = head_budget
    seen: set[str] = set()
    for line in text.splitlines():
        if relevant_line_score(line) <= 0:
            continue
        cleaned = line.strip()
        if not cleaned or cleaned in seen:
            continue
        addition = "\n" + line
        if used + len(addition) > head_budget + middle_budget:
            break
        pieces.append(addition)
        seen.add(cleaned)
        used += len(addition)
    tail = text[-tail_budget:]
    result = "\n\n<!-- 末尾片段 -->\n\n".join(["".join(pieces), tail])
    return result[:max_chars], True


def list_pdf_files(input_dir: Path, recursive: bool) -> list[Path]:
    from .config import CACHE_DIR_NAME, FAILED_SOURCES_DIR_NAME
    pattern = "**/*.pdf" if recursive else "*.pdf"
    excluded_dirs = {MARKDOWN_DIR_NAME, FAILED_SOURCES_DIR_NAME, CACHE_DIR_NAME}
    pdf_files = []
    for path in input_dir.glob(pattern):
        try:
            relative_parts = path.relative_to(input_dir).parts
        except ValueError:
            relative_parts = path.parts
        if any(part in excluded_dirs for part in relative_parts):
            continue
        pdf_files.append(path)
    return sorted(pdf_files, key=lambda path: str(path).casefold())


def read_pdf_as_markdown_with_mode(pdf_path: Path, mode: str, runtime: RuntimeDeps) -> tuple[str, str]:
    if mode == "auto":
        fast_markdown = ""
        fast_error: BaseException | None = None
        try:
            fast_markdown = runtime.pymupdf4llm.to_markdown(str(pdf_path))
            if not markdown_needs_mineru(fast_markdown):
                return fast_markdown, "pymupdf4llm"
        except Exception as exc:
            fast_error = exc
        try:
            mineru_markdown = run_mineru_to_markdown(pdf_path)
            return mineru_markdown, "mineru"
        except Exception as exc:
            if fast_markdown:
                return (
                    "<!-- Auto mode kept pymupdf4llm because MinerU failed. "
                    f"error: {short_error(exc)} -->\n\n{fast_markdown}",
                    "pymupdf4llm",
                )
            fallback = read_pdf_as_markdown_with_mode(pdf_path, "pymupdf_text", runtime)[0]
            return (
                "<!-- Auto mode fallback to pymupdf_text. "
                f"pymupdf4llm_error: {short_error(fast_error) if fast_error else ''}; "
                f"mineru_error: {short_error(exc)} -->\n\n{fallback}",
                "pymupdf_text",
            )
    if mode == "mineru":
        try:
            return run_mineru_to_markdown(pdf_path), "mineru"
        except Exception as exc:
            fallback = runtime.pymupdf4llm.to_markdown(str(pdf_path))
            return (
                "<!-- MinerU failed; fallback to pymupdf4llm. "
                f"error: {short_error(exc)} -->\n\n{fallback}"
            ), "pymupdf4llm"
    if mode == "pymupdf4llm":
        return runtime.pymupdf4llm.to_markdown(str(pdf_path)), "pymupdf4llm"
    if mode == "pymupdf_text":
        chunks: list[str] = []
        with runtime.fitz.open(str(pdf_path)) as doc:
            for page_index, page in enumerate(doc, start=1):
                chunks.append(f"\n\n# Page {page_index}\n\n")
                chunks.append(page.get_text("text") or "")
        return "".join(chunks), "pymupdf_text"
    if mode == "pypdf_text":
        reader = runtime.PdfReader(str(pdf_path), strict=False)
        chunks = []
        for page_index, page in enumerate(reader.pages, start=1):
            chunks.append(f"\n\n# Page {page_index}\n\n")
            chunks.append(page.extract_text() or "")
        return "".join(chunks), "pypdf_text"
    raise ValueError(f"未知 PDF 转换方式：{mode}")


def read_pdf_as_markdown(pdf_path: Path, mode: str, runtime: RuntimeDeps) -> str:
    return read_pdf_as_markdown_with_mode(pdf_path, mode, runtime)[0]
