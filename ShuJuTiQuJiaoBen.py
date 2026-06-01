"""Chem-PDF-Extractor: local web UI for extracting chemical data from PDFs.

Default usage:
  python chem_pdf_extractor.py

The script opens a local browser page. From that page you can:
  - choose the real Ollama model used for processing
  - define up to 30 extraction fields
  - switch among three PDF-to-Markdown/text conversion modes
  - process large PDF batches with a progress bar

No cloud API is used. Ollama must be running locally.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_lib
import importlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_MODEL = "minicpm-v:latest"
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MAX_CHARS = 0
DEFAULT_NUM_CTX = 8192
DEFAULT_CLOUD_SERVICE_NAME = "silicon"
DEFAULT_CLOUD_MODEL = "deepseek-ai/DeepSeek-V4-Pro"
DEFAULT_CLOUD_BASE_URL = "https://api.siliconflow.cn/v1"
DEFAULT_CLOUD_API_KEY = ""
LOCAL_CONFIG_NAME = "config.local.json"
MAX_ARTIFACT_NAME_CHARS = 80
OUTPUT_EXCEL_NAME = "提取结果.xlsx"
ERROR_LOG_NAME = "错误日志.txt"
PARTIAL_JSONL_NAME = "提取结果.partial.jsonl"
BAD_ROWS_EXCEL_NAME = "坏数据.xlsx"
BAD_ROWS_JSONL_NAME = "坏数据.jsonl"
SUSPICIOUS_ROWS_EXCEL_NAME = "可疑数据.xlsx"
SUSPICIOUS_ROWS_JSONL_NAME = "可疑数据.jsonl"
ERROR_STATS_EXCEL_NAME = "错误统计.xlsx"
ERROR_STATS_JSONL_NAME = "错误统计.jsonl"
MARKDOWN_DIR_NAME = "md文件"
CACHE_DIR_NAME = "抽取缓存"
FAILED_SOURCES_DIR_NAME = "提取失败源文件"
BUNDLED_RUNTIME_DIR_NAME = "YiLaiHuanJing"
LEGACY_BUNDLED_RUNTIME_DIR_NAME = "运行依赖"
BAD_ROW_MIN_FILL_RATE = 0.40
BAD_ROW_EMPTY_MARKERS = {"n/a", "na", "null", "none", "-999"}
BAD_ROW_FIELD_WEIGHTS = {"required": 1.0, "recommended": 0.5, "optional": 0.0}
EXTRACTION_CACHE_VERSION = "2026-05-quality-v2"
CLOUD_RETRY_COUNT = 3
CLOUD_RETRY_BASE_DELAY_SECONDS = 2.0
CLOUD_RETRY_MAX_DELAY_SECONDS = 20.0
DEFAULT_CLOUD_MODEL_SUGGESTIONS = [
    "deepseek-ai/DeepSeek-V4-Pro",
    "deepseek-ai/DeepSeek-V4-Flash",
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-V3.2",
    "deepseek-ai/DeepSeek-V3.1-Terminus",
    "deepseek-ai/DeepSeek-R1",
    "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "deepseek-ai/DeepSeek-OCR",
    "Pro/deepseek-ai/DeepSeek-V3.2",
    "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
    "Pro/deepseek-ai/DeepSeek-V3",
    "Pro/deepseek-ai/DeepSeek-R1",
    "ByteDance-Seed/Seed-OSS-36B-Instruct",
    "MiniMaxAI/MiniMax-M2.5",
    "Pro/MiniMaxAI/MiniMax-M2.5",
    "Pro/moonshotai/Kimi-K2.6",
    "Pro/moonshotai/Kimi-K2.5",
    "Pro/zai-org/GLM-5.1",
    "Pro/zai-org/GLM-5",
    "Pro/zai-org/GLM-4.7",
    "zai-org/GLM-4.5-Air",
    "zai-org/GLM-4.5V",
    "THUDM/GLM-4-32B-0414",
    "THUDM/GLM-4-9B-0414",
    "THUDM/GLM-Z1-9B-0414",
    "Qwen/Qwen3.6-35B-A3B",
    "Qwen/Qwen3.6-27B",
    "Qwen/Qwen3.5-397B-A17B",
    "Qwen/Qwen3.5-122B-A10B",
    "Qwen/Qwen3.5-35B-A3B",
    "Qwen/Qwen3.5-27B",
    "Qwen/Qwen3.5-9B",
    "Qwen/Qwen3.5-4B",
    "Qwen/Qwen3-32B",
    "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "Qwen/Qwen3-14B",
    "Qwen/Qwen3-8B",
    "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct-128K",
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen2.5-32B-Instruct",
    "Qwen/Qwen2.5-14B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "Pro/Qwen/Qwen2.5-7B-Instruct",
    "LoRA/Qwen/Qwen2.5-72B-Instruct",
    "LoRA/Qwen/Qwen2.5-32B-Instruct",
    "LoRA/Qwen/Qwen2.5-14B-Instruct",
    "LoRA/Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen3-VL-32B-Thinking",
    "Qwen/Qwen3-VL-32B-Instruct",
    "Qwen/Qwen3-VL-30B-A3B-Thinking",
    "Qwen/Qwen3-VL-30B-A3B-Instruct",
    "Qwen/Qwen3-VL-8B-Thinking",
    "Qwen/Qwen3-VL-8B-Instruct",
    "Qwen/Qwen3-Omni-30B-A3B-Thinking",
    "Qwen/Qwen3-Omni-30B-A3B-Instruct",
    "Qwen/Qwen3-Omni-30B-A3B-Captioner",
    "Qwen/Qwen-Image",
    "Qwen/Qwen-Image-Edit",
    "Qwen/Qwen-Image-Edit-2509",
    "tencent/Hunyuan-A13B-Instruct",
    "tencent/Hunyuan-MT-7B",
    "stepfun-ai/Step-3.5-Flash",
    "inclusionAI/Ling-flash-2.0",
    "inclusionAI/Ling-mini-2.0",
    "BAAI/bge-m3",
    "Pro/BAAI/bge-m3",
    "BAAI/bge-large-zh-v1.5",
    "BAAI/bge-large-en-v1.5",
    "BAAI/bge-reranker-v2-m3",
    "Pro/BAAI/bge-reranker-v2-m3",
    "Qwen/Qwen3-Embedding-8B",
    "Qwen/Qwen3-Embedding-4B",
    "Qwen/Qwen3-Embedding-0.6B",
    "Qwen/Qwen3-Reranker-8B",
    "Qwen/Qwen3-Reranker-4B",
    "Qwen/Qwen3-Reranker-0.6B",
    "Qwen/Qwen3-VL-Embedding-8B",
    "Qwen/Qwen3-VL-Reranker-8B",
    "netease-youdao/bce-embedding-base_v1",
    "netease-youdao/bce-reranker-base_v1",
    "PaddlePaddle/PaddleOCR-VL-1.5",
    "baidu/ERNIE-Image-Turbo",
    "Kwai-Kolors/Kolors",
    "Tongyi-MAI/Z-Image",
    "Tongyi-MAI/Z-Image-Turbo",
    "Wan-AI/Wan2.2-T2V-A14B",
    "Wan-AI/Wan2.2-I2V-A14B",
    "FunAudioLLM/CosyVoice2-0.5B",
    "FunAudioLLM/SenseVoiceSmall",
    "fnlp/MOSS-TTSD-v0.5",
    "TeleAI/TeleSpeechASR",
]

MINERU_EXE = Path(os.environ.get("MINERU_EXE", "mineru"))
MINERU_OUTPUT_ROOT = Path(os.environ.get("MINERU_OUTPUT_ROOT", str(Path(__file__).resolve().parent / ".mineru_outputs")))
MINERU_DEFAULT_BACKEND = os.environ.get("MINERU_BACKEND", "pipeline")
MINERU_DEFAULT_METHOD = os.environ.get("MINERU_METHOD", "txt")
MINERU_DEFAULT_FORMULA = os.environ.get("MINERU_FORMULA", "false")
MINERU_DEFAULT_TABLE = os.environ.get("MINERU_TABLE", "false")

REQUIRED_PACKAGES = {
    "pymupdf4llm": "pymupdf4llm",
    "fitz": "pymupdf",
    "pypdf": "pypdf",
    "langchain": "langchain",
    "langchain_ollama": "langchain-ollama",
    "pydantic": "pydantic",
    "pandas": "pandas",
    "openpyxl": "openpyxl",
}

DEFAULT_FIELDS = [
    {"label": "工艺名称", "requirement": "required", "description": "文本（中文/英文）。抽取论文中的工艺、反应路线或过程名称。"},
    {"label": "原料", "requirement": "required", "description": "下拉列表。抽取主要原料、反应物或进料名称，可用分号分隔多个原料。"},
    {"label": "CAS号", "requirement": "required", "description": "文本，格式 xx-xx-x。抽取原料或核心物质 CAS 号，多个用分号分隔。"},
    {"label": "催化剂通用名", "requirement": "required", "description": "文本。抽取催化剂通用名称、简称或体系名称。"},
    {"label": "具体型号/牌号", "requirement": "recommended", "description": "文本（重要）。抽取商业牌号、型号、批号或论文中给出的具体催化剂编号。"},
    {"label": "催化剂制备方法", "requirement": "optional", "description": "文本描述。概括浸渍、沉淀、水热、焙烧、还原等制备步骤。"},
    {"label": "催化剂类型", "requirement": "recommended", "description": "下拉列表。归纳为金属、氧化物、分子筛、负载型、均相、酶、电催化剂等类型。"},
    {"label": "物理形状", "requirement": "optional", "description": "下拉列表。抽取粉末、颗粒、片状、球形、蜂窝、膜、电极等形态。"},
    {"label": "催化剂寿命", "requirement": "optional", "description": "文本。抽取寿命、稳定运行时间、循环次数、失活信息或再生信息。"},
    {"label": "反应温度（℃）", "requirement": "required", "description": "数字（℃）。只填摄氏温度数值；若原文为 K 或其他单位，换算为 ℃。"},
    {"label": "温度误差", "requirement": "recommended", "description": "数字 (℃)。抽取温度波动、误差或范围半宽；没有明确误差则留空。"},
    {"label": "反应压力（MPa）", "requirement": "required", "description": "数字（MPa）。只填 MPa 数值；若原文为 bar、atm、Pa 等，换算为 MPa。"},
    {"label": "压力误差", "requirement": "recommended", "description": "数字 (MPa)。抽取压力误差、波动或范围半宽；没有明确误差则留空。"},
    {"label": "反应规模/空速", "requirement": "recommended", "description": "数字 (h^-1)。优先抽取 GHSV、WHSV、LHSV、空速或规模；无法换算时保留原文表达。"},
    {"label": "数据类型/实验室/工业化", "requirement": "recommended", "description": "实验室小试/中试放大/工业化。根据论文实验规模和装置描述判断。"},
    {"label": "反应器形式", "requirement": "required", "description": "下拉列表。抽取固定床、釜式、管式、流化床、微反应器、电解槽、膜反应器等。"},
    {"label": "物性方法", "requirement": "required", "description": "下拉列表。抽取 GC、HPLC、GC-MS、NMR、滴定、在线分析、模拟方法或物性计算方法。"},
    {"label": "转化率（%）", "requirement": "required", "description": "数字（0-100）。抽取主要原料转化率，填百分数数值。"},
    {"label": "选择性（%）", "requirement": "required", "description": "下拉列表/数字。抽取目标产物选择性；若为数值，填百分数；若为定性分类，保留原文。"},
    {"label": "产物组成", "requirement": "required", "description": "抽取产物组成总体描述，包括主产物、副产物和组成比例来源。"},
    {"label": "产物1: 名称", "requirement": "required", "description": "文本。抽取第一种主要产物名称。"},
    {"label": "产物1: CAS号", "requirement": "required", "description": "文本。抽取第一种主要产物 CAS 号。"},
    {"label": "产物1: 数值", "requirement": "required", "description": "数字 (%)。抽取第一种产物的组成、选择性、收率或占比百分数。"},
    {"label": "产物2: 名称", "requirement": "required", "description": "文本。抽取第二种主要产物名称。"},
    {"label": "产物2: CAS号", "requirement": "required", "description": "文本。抽取第二种主要产物 CAS 号。"},
    {"label": "产物2: 数值", "requirement": "required", "description": "数字 (%)。抽取第二种产物的组成、选择性、收率或占比百分数。"},
    {"label": "产物3: 名称", "requirement": "recommended", "description": "文本。抽取第三种产物名称；没有第三种产物则留空。"},
    {"label": "产物3: 数值", "requirement": "recommended", "description": "数字 (%)。抽取第三种产物对应百分数；没有则留空。"},
    {"label": "产物4: 名称", "requirement": "optional", "description": "文本。抽取第四种产物名称；没有则留空。"},
    {"label": "产物4: 数值", "requirement": "optional", "description": "文本/数字。抽取第四种产物对应数值或原文描述；没有则留空。"},
    {"label": "数据来源", "requirement": "optional", "description": "文本。记录数据来自正文、表格、图、补充材料或具体表/图编号。"},
    {"label": "产品分离", "requirement": "recommended", "description": "文本描述。抽取分离方法、纯化步骤、收集方式或后处理条件。"},
    {"label": "反应热", "requirement": "recommended", "description": "放热/吸热/无反应热。根据原文热效应、焓变或工艺描述判断。"},
    {"label": "反应机理", "requirement": "optional", "description": "文本描述，第一句话是主要反应式；随后简述关键中间体、活性位点或机理结论。"},
    {"label": "文献出处-链接", "requirement": "required", "description": "以 http 或 https 开始的 url。优先 DOI 链接、出版社链接或论文网页。"},
    {"label": "文献题目", "requirement": "required", "description": "文本描述。抽取论文正式题目。"},
    {"label": "流程图", "requirement": "recommended", "description": "图片。若当前文本无法直接提取图片，记录流程图编号、图题、页码或简要流程描述。"},
]

CHINESE_TRANSLATION_FIELDS = {
    "工艺名称",
    "原料",
    "CAS号",
    "催化剂通用名",
    "具体型号/牌号",
    "催化剂制备方法",
    "催化剂类型",
    "物理形状",
    "催化剂寿命",
    "反应温度（℃）",
    "温度误差",
    "反应压力（MPa）",
    "压力误差",
    "反应规模/空速",
    "数据类型/实验室/工业化",
    "反应器形式",
    "物性方法",
    "转化率（%）",
    "选择性（%）",
    "产物组成",
    "产物1: 名称",
    "产物1: CAS号",
    "产物1: 数值",
    "产物2: 名称",
    "产物2: CAS号",
    "产物2: 数值",
    "产物3: 名称",
    "产物3: 数值",
    "产物4: 名称",
    "产物4: 数值",
    "数据来源",
    "产品分离",
    "反应热",
    "反应机理",
}

EXPORT_EXCLUDED_COLUMNS = [
    "source_path",
    "source_file",
    "record_index",
    "record_count",
    "llm_provider",
    "llm_service",
    "llm_model",
    "ollama_model",
    "pdf_to_md_mode",
    "markdown_chars_total",
    "markdown_chars_used",
    "was_truncated",
    "quality_retry_used",
]


def candidate_pythons() -> list[Path]:
    candidates: list[Path] = []
    bundled_python = Path(__file__).resolve().parent / BUNDLED_RUNTIME_DIR_NAME / "python" / "python.exe"
    candidates.append(bundled_python)
    legacy_bundled_python = Path(__file__).resolve().parent / LEGACY_BUNDLED_RUNTIME_DIR_NAME / "python" / "python.exe"
    candidates.append(legacy_bundled_python)
    env_python = os.environ.get("CHEM_PDF_EXTRACTOR_PYTHON") or os.environ.get("CHEM_EXTRACTOR_PYTHON")
    if env_python:
        candidates.append(Path(env_python))

    current = Path(sys.executable).resolve()
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        key = str(resolved).casefold()
        if key == str(current).casefold() or key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return unique


def python_has_required_packages(python_exe: Path) -> bool:
    if not python_exe.exists():
        return False
    code = "import " + ", ".join(REQUIRED_PACKAGES.keys())
    result = subprocess.run(
        [str(python_exe), "-c", code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def try_reexec_with_ready_python() -> None:
    if os.environ.get("CHEM_EXTRACTOR_REEXECED") == "1":
        return
    for python_exe in candidate_pythons():
        if python_has_required_packages(python_exe):
            print(f"当前 Python 缺依赖：{sys.executable}")
            print(f"找到已安装依赖的 Python：{python_exe}")
            print("正在自动切换并重启脚本...")
            sys.stdout.flush()
            sys.stderr.flush()
            os.environ["CHEM_EXTRACTOR_REEXECED"] = "1"
            os.execv(str(python_exe), [str(python_exe), str(Path(__file__).resolve()), *sys.argv[1:]])


def clean_pip_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in [
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "PIP_PROXY",
        "pip_proxy",
    ]:
        env.pop(key, None)
    return env


def find_missing_imports() -> list[str]:
    missing: list[str] = []
    for import_name, package_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ModuleNotFoundError:
            missing.append(package_name)
    return sorted(set(missing))


def run_pip_install(packages: list[str]) -> bool:
    commands = [
        [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *packages],
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-i",
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "--trusted-host",
            "pypi.tuna.tsinghua.edu.cn",
            *packages,
        ],
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-i",
            "https://mirrors.aliyun.com/pypi/simple/",
            "--trusted-host",
            "mirrors.aliyun.com",
            *packages,
        ],
    ]
    for command in commands:
        print("\n正在尝试安装依赖：")
        print(" ".join(command))
        result = subprocess.run(command, check=False, env=clean_pip_env())
        if result.returncode == 0:
            return True
    return False


def ensure_dependencies(auto_install: bool = True) -> None:
    missing = find_missing_imports()
    if not missing:
        return

    print("当前 Python 缺少依赖：", ", ".join(missing))
    try_reexec_with_ready_python()

    if auto_install:
        installed = run_pip_install(missing)
        if installed and not find_missing_imports():
            print("依赖安装完成，继续执行。")
            return

    mirror_command = (
        f'"{sys.executable}" -m pip install '
        "-i https://pypi.tuna.tsinghua.edu.cn/simple "
        "--trusted-host pypi.tuna.tsinghua.edu.cn "
        + " ".join(missing)
    )
    raise SystemExit(
        "\n依赖没有安装成功，脚本无法继续。\n"
        "你可以手动复制下面这条命令到 PowerShell 执行：\n"
        f"{mirror_command}\n"
    )


@dataclass
class RuntimeDeps:
    pd: Any
    pymupdf4llm: Any
    fitz: Any
    PdfReader: Any
    ChatPromptTemplate: Any
    ChatOllama: Any
    Field: Any
    create_model: Any


def import_runtime_dependencies() -> RuntimeDeps:
    import fitz
    import pandas as pd
    import pymupdf4llm
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama import ChatOllama
    from pydantic import Field, create_model
    from pypdf import PdfReader

    return RuntimeDeps(
        pd=pd,
        pymupdf4llm=pymupdf4llm,
        fitz=fitz,
        PdfReader=PdfReader,
        ChatPromptTemplate=ChatPromptTemplate,
        ChatOllama=ChatOllama,
        Field=Field,
        create_model=create_model,
    )


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def default_input_dir() -> Path:
    nearby = script_dir() / "input_pdfs"
    return nearby if nearby.exists() else script_dir()


def default_output_path() -> Path:
    return script_dir() / OUTPUT_EXCEL_NAME


def local_config_path() -> Path:
    return script_dir() / LOCAL_CONFIG_NAME


def normalize_local_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = raw or {}
    return {
        "cloud_service_name": str(
            raw.get("cloud_service_name")
            or raw.get("llm_service_name")
            or raw.get("service_name")
            or DEFAULT_CLOUD_SERVICE_NAME
        ).strip(),
        "cloud_api_key": str(raw.get("cloud_api_key") or raw.get("api_key") or "").strip(),
        "cloud_base_url": str(raw.get("cloud_base_url") or raw.get("base_url") or DEFAULT_CLOUD_BASE_URL).strip(),
        "cloud_model": str(raw.get("cloud_model") or raw.get("model") or DEFAULT_CLOUD_MODEL).strip(),
        "cloud_active": bool(raw.get("cloud_active", True)),
    }


def load_local_config() -> dict[str, Any]:
    path = local_config_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return normalize_local_config(data)
    except (OSError, json.JSONDecodeError):
        return {}
    return {}


def save_local_config(config: dict[str, Any]) -> Path:
    normalized = normalize_local_config(config)
    payload = {
        "llm_service_name": normalized["cloud_service_name"],
        "api_key": normalized["cloud_api_key"],
        "base_url": normalized["cloud_base_url"],
        "model": normalized["cloud_model"],
        "cloud_active": normalized["cloud_active"],
    }
    path = local_config_path()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def apply_cloud_config_defaults(config: dict[str, Any]) -> dict[str, Any]:
    local_config = load_local_config()
    env_api_key = os.environ.get("CHEM_PDF_EXTRACTOR_API_KEY") or os.environ.get("CHEM_EXTRACTOR_CLOUD_API_KEY") or ""
    defaults = {
        "cloud_service_name": local_config.get("cloud_service_name") or DEFAULT_CLOUD_SERVICE_NAME,
        "cloud_model": local_config.get("cloud_model") or os.environ.get("CHEM_PDF_EXTRACTOR_MODEL") or DEFAULT_CLOUD_MODEL,
        "cloud_base_url": local_config.get("cloud_base_url") or os.environ.get("CHEM_PDF_EXTRACTOR_BASE_URL") or DEFAULT_CLOUD_BASE_URL,
        "cloud_api_key": local_config.get("cloud_api_key") or env_api_key or DEFAULT_CLOUD_API_KEY,
        "cloud_active": local_config.get("cloud_active", True),
    }
    for key, value in defaults.items():
        if key == "cloud_active":
            config.setdefault(key, value)
        elif not str(config.get(key) or "").strip():
            config[key] = value
    return config


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}小时{minutes}分{secs}秒"
    if minutes:
        return f"{minutes}分{secs}秒"
    if seconds < 10:
        return f"{seconds:.1f}秒"
    return f"{secs}秒"


def add_stat(stats: dict[str, float] | None, key: str, value: float = 1.0) -> None:
    if stats is not None:
        stats[key] = stats.get(key, 0.0) + value


def eta_text(started_at: float, done: int, total: int) -> str:
    if done <= 0 or total <= 0 or done >= total:
        return "预计剩余 0秒"
    elapsed = time.perf_counter() - started_at
    remaining = max(0, total - done)
    eta = elapsed / done * remaining
    return f"预计剩余 {format_duration(eta)}"


def stage_summary(stats: dict[str, float]) -> str:
    if not stats:
        return ""
    parts = []
    mapping = [
        ("pdf_to_md", "PDF转MD"),
        ("llm_extraction", "LLM抽取"),
        ("quality_retry", "二次抽取"),
        ("translation", "翻译"),
    ]
    for key, label in mapping:
        value = stats.get(key, 0.0)
        if value:
            parts.append(f"{label}{format_duration(value)}")
    cache_hits = int(stats.get("extract_cache_hit", 0))
    if cache_hits:
        parts.append(f"抽取缓存命中{cache_hits}次")
    return "；".join(parts)


def get_ollama_models(base_url: str) -> list[str]:
    url = base_url.rstrip("/") + "/api/tags"
    with urllib.request.urlopen(url, timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]


def choose_model(requested_model: str, available_models: list[str]) -> str:
    if requested_model in available_models:
        return requested_model
    for model in [DEFAULT_MODEL, "qwen3.5:9b", "deepseek-r1:7b", "gemma4:e4b", "gpt-oss:20b"]:
        if model in available_models:
            return model
    if available_models:
        return available_models[0]
    raise RuntimeError("Ollama 没有可用模型，请先在 Ollama 中安装模型。")


def model_order(primary_model: str, available_models: list[str], auto_fallback: bool) -> list[str]:
    if not auto_fallback:
        return [primary_model]
    candidates = [primary_model, DEFAULT_MODEL, "qwen3.5:9b", "deepseek-r1:7b", "gemma4:e4b", "gpt-oss:20b"]
    out: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item in available_models and item not in seen:
            out.append(item)
            seen.add(item)
    return out or [primary_model]


def infer_field_type(label: str, description: str) -> str:
    text = f"{label} {description}".lower()
    desc = description.strip().lower()
    if desc.startswith("数字") or "只填" in text:
        return "float"
    return "str"


def normalize_requirement(value: Any) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "必填": "required",
        "required": "required",
        "建议": "recommended",
        "推荐": "recommended",
        "recommended": "recommended",
        "选填": "optional",
        "可选": "optional",
        "optional": "optional",
    }
    return mapping.get(text, "optional")


def requirement_label(value: str) -> str:
    return {"required": "必填", "recommended": "建议", "optional": "选填"}.get(value, "选填")


def requirement_rule(value: str) -> str:
    if value == "required":
        return "【必填】必须优先检索全文、表格、图注和补充材料中的相关信息，尽最大努力抽取；只有原文确实不存在或无法判断时才留空，严禁编造"
    if value == "recommended":
        return "【建议】尽量抽取；若原文没有明确给出或无法可靠判断，可以留空"
    return "【选填】有明确证据时抽取；没有就留空"


def normalize_fields(fields: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    source = fields or DEFAULT_FIELDS
    normalized: list[dict[str, str]] = []
    for item in source:
        label = str(item.get("label", "")).strip()
        if not label:
            continue
        description = str(item.get("description", "")).strip() or label
        field_type = str(item.get("type") or infer_field_type(label, description)).strip().lower()
        if field_type not in {"str", "float", "int"}:
            field_type = infer_field_type(label, description)
        requirement = normalize_requirement(item.get("requirement"))
        normalized.append(
            {
                "label": label,
                "type": field_type,
                "requirement": requirement,
                "description": description,
            }
        )

    if not normalized:
        first = DEFAULT_FIELDS[0]
        description = str(first.get("description", "")).strip() or str(first.get("label", "字段")).strip()
        normalized = [
            {
                "label": str(first.get("label", "字段")).strip() or "字段",
                "type": str(first.get("type") or infer_field_type(str(first.get("label", "")), description)),
                "requirement": normalize_requirement(first.get("requirement")),
                "description": description,
            }
        ]

    used: dict[str, int] = {}
    for item in normalized:
        label = item["label"]
        used[label] = used.get(label, 0) + 1
        if used[label] > 1:
            item["label"] = f"{label} ({used[label]})"
    return normalized


def python_type(type_name: str) -> type:
    # 统一用字符串承接 LLM 输出，避免缺失值空白导致 float/int 校验失败。
    return str


def missing_rule(type_name: str) -> str:
    if type_name in {"float", "int"}:
        return "缺失时留空；若有数据，只输出纯数字"
    return "缺失时留空，不要输出 N/A、null、-999 或自行编造内容"


def build_dynamic_model(fields: list[dict[str, str]], runtime: RuntimeDeps):
    record_fields: dict[str, Any] = {}
    key_to_label: dict[str, str] = {}
    for index, item in enumerate(fields, start=1):
        key = f"field_{index:02d}"
        key_to_label[key] = item["label"]
        desc = (
            f"字段名：{item['label']}。"
            f"字段要求：{requirement_rule(item.get('requirement', 'optional'))}。"
            f"字段说明：{item['description']}。"
            f"{missing_rule(item['type'])}。"
            "中英文文献均可抽取，保留原文中最清楚的表达。"
        )
        record_fields[key] = (python_type(item["type"]), runtime.Field(default="", description=desc))
    record_model = runtime.create_model("ExtractionRecord", **record_fields)
    model = runtime.create_model(
        "ExtractionResult",
        records=(
            list[record_model],
            runtime.Field(
                default_factory=list,
                description=(
                    "抽取到的数据记录列表。同一篇文献中如果有多个工艺、催化剂、实验条件、"
                    "数据表行或可独立成行的结果，就拆成多条 records；只有一条时也放在列表中。"
                ),
            ),
        ),
    )
    return model, key_to_label


def field_instructions(fields: list[dict[str, str]]) -> str:
    lines = []
    for index, item in enumerate(fields, start=1):
        requirement = item.get("requirement", "optional")
        lines.append(
            f"{index}. {item['label']} [{requirement_label(requirement)}]: "
            f"{item['description']}；{requirement_rule(requirement)}；{missing_rule(item['type'])}"
        )
    return "\n".join(lines)


def build_extraction_chain(
    model_name: str,
    base_url: str,
    num_ctx: int,
    llm_timeout: int,
    runtime: RuntimeDeps,
    extraction_model: Any,
):
    client_kwargs = {} if llm_timeout <= 0 else {"timeout": llm_timeout}
    llm = runtime.ChatOllama(
        model=model_name,
        temperature=0,
        num_ctx=num_ctx,
        num_predict=1024,
        keep_alive="30m",
        base_url=base_url,
        sync_client_kwargs=client_kwargs,
    )
    structured_llm = llm.with_structured_output(extraction_model)
    prompt = runtime.ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是专业的化工领域学术数据抽取助手。请阅读从 PDF 转换得到的 Markdown 或文本，"
                "严格按照结构化输出字段抽取数据。文献可能是中文、英文或中英混合。"
                "只能依据原文，不要编造。任何字段缺失时留空，不要填 N/A、null 或 -999。"
                "如果同一篇文献包含多个工艺、催化剂、实验条件、表格行或独立结果，"
                "请在 records 中拆成多条记录；只有一条结果时也输出一条 records。",
            ),
            (
                "human",
                "文件名：{file_name}\n\n"
                "需要抽取的字段：\n{field_instructions}\n\n"
                "{quality_hint}\n\n"
                "PDF 转换文本如下，可能已截断：\n\n{markdown_text}",
            ),
        ]
    )
    return prompt | structured_llm


def pydantic_to_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if isinstance(result, dict):
        return result
    raise TypeError(f"无法转换 LLM 返回值：{type(result)!r}")


def message_content(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content)


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


MISSING_TEXT_MARKERS = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "nil",
    "nan",
    "not mentioned",
    "not reported",
    "not available",
    "unknown",
    "未提及",
    "未报道",
    "无",
    "空",
    "-999",
}


def clean_extracted_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and float(value) == -999:
        return ""
    if isinstance(value, (list, tuple, set)):
        parts = [clean_extracted_value(item) for item in value]
        return "；".join(part for part in parts if part)
    if isinstance(value, dict):
        compact = {str(k): clean_extracted_value(v) for k, v in value.items()}
        compact = {k: v for k, v in compact.items() if v}
        if not compact:
            return ""
        return json.dumps(compact, ensure_ascii=False)
    text = str(value).strip()
    return "" if text.casefold() in MISSING_TEXT_MARKERS else text


def normalize_cloud_value(value: Any, field_type: str) -> Any:
    text = clean_extracted_value(value)
    if not text:
        return ""
    if field_type == "str":
        return text
    number_match = re.search(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
    try:
        if field_type == "int":
            return int(float(number_match.group(0) if number_match else text))
        return float(number_match.group(0) if number_match else text)
    except (TypeError, ValueError):
        return ""


def has_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def should_translate_to_chinese(field_name: str, value: Any) -> bool:
    text = clean_extracted_value(value)
    if not text:
        return False
    if field_name not in CHINESE_TRANSLATION_FIELDS:
        return False
    if "CAS号" in field_name or field_name == "CAS号":
        return False
    if text.startswith(("http://", "https://", "doi.org/")):
        return False
    if has_chinese(text):
        return False
    compact = text.replace(",", "").strip()
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?\s*(?:%|°c|℃|k|mpa|bar|atm|pa|h\^-?1|h-1)?", compact, flags=re.IGNORECASE):
        return False
    if re.fullmatch(r"\d{2,7}-\d{2}-\d", compact):
        return False
    return True


def parse_translation_payload(raw: dict[str, Any]) -> dict[str, str]:
    translated: dict[str, str] = {}
    for item in raw.get("items", []):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "").strip()
        value = clean_extracted_value(item.get("translation"))
        if item_id and value:
            translated[item_id] = value
    return translated


def translate_rows_to_chinese(
    rows: list[dict[str, Any]],
    fields: list[dict[str, str]],
    batch_translator: Any,
    batch_size: int = 24,
) -> int:
    target_labels = [item["label"] for item in fields if item["label"] in CHINESE_TRANSLATION_FIELDS]
    pending: list[dict[str, str]] = []
    refs: list[tuple[str, dict[str, Any], str]] = []
    counter = 1
    for row in rows:
        for label in target_labels:
            value = row.get(label, "")
            if not should_translate_to_chinese(label, value):
                continue
            item_id = f"t{counter}"
            counter += 1
            pending.append({"id": item_id, "field": label, "text": str(value).strip()})
            refs.append((item_id, row, label))

    changed = 0
    translations: dict[str, str] = {}
    for start in range(0, len(pending), batch_size):
        translations.update(batch_translator(pending[start : start + batch_size]))

    for item_id, row, label in refs:
        translated = translations.get(item_id, "")
        if translated:
            row[label] = translated
            changed += 1
    return changed


def cloud_chat_completion(
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    llm_timeout: int,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    last_exc: BaseException | None = None

    for attempt in range(CLOUD_RETRY_COUNT):
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            if llm_timeout and llm_timeout > 0:
                response_ctx = urllib.request.urlopen(request, timeout=llm_timeout)
            else:
                response_ctx = urllib.request.urlopen(request)
            with response_ctx as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            return payload["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            last_exc = exc
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if not retryable or attempt >= CLOUD_RETRY_COUNT - 1:
                body_text = ""
                try:
                    body_text = exc.read().decode("utf-8", errors="replace")
                except Exception:
                    pass
                raise RuntimeError(f"云端 API HTTP {exc.code}: {tail_text(body_text)}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError) as exc:
            last_exc = exc
            if attempt >= CLOUD_RETRY_COUNT - 1:
                raise RuntimeError(f"云端 API 请求失败：{short_error(exc)}") from exc

        delay = min(CLOUD_RETRY_MAX_DELAY_SECONDS, CLOUD_RETRY_BASE_DELAY_SECONDS * (2**attempt))
        time.sleep(delay)

    raise RuntimeError(f"云端 API 请求失败：{short_error(last_exc) if last_exc else 'unknown error'}")


def translate_item_batch_to_chinese_cloud(
    base_url: str,
    api_key: str,
    model: str,
    items: list[dict[str, str]],
    llm_timeout: int,
) -> dict[str, str]:
    if not items:
        return {}
    messages = [
        {
            "role": "system",
            "content": (
                "你是化工文献数据清洗助手。请把用户给出的 JSON 数组中每个 text 翻译成简洁、准确的中文。"
                "只翻译自然语言和英文术语，保留化学式、CAS 号、数字、单位、百分号、型号和牌号。"
                "催化剂、反应器、物性方法、反应热、反应机理等术语要用化工领域常用中文。"
                "不要解释，不要补充原文没有的信息。"
                "只输出合法 JSON 对象，格式为 {\"items\":[{\"id\":\"...\",\"translation\":\"...\"}]}。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(items, ensure_ascii=False),
        },
    ]
    content = cloud_chat_completion(base_url, api_key, model, messages, llm_timeout)
    return parse_translation_payload(extract_json_object(content))


def parse_model_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    models: list[str] = []
    seen: set[str] = set()
    for item in data:
        if isinstance(item, str):
            model_id = item
        elif isinstance(item, dict):
            model_id = str(item.get("id") or item.get("name") or "").strip()
        else:
            continue
        if model_id and model_id not in seen:
            models.append(model_id)
            seen.add(model_id)
    return models


def fetch_cloud_models_once(base_url: str, api_key: str, query: str = "") -> list[str]:
    url = base_url.rstrip("/") + "/models" + query
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    return parse_model_ids(payload)


def get_cloud_models(base_url: str, api_key: str) -> list[str]:
    if not base_url:
        raise RuntimeError("LLM BASE URL 为空。")
    if not api_key:
        raise RuntimeError("LLM API KEY 为空。")

    errors: list[str] = []
    for query in ["?type=text&sub_type=chat", ""]:
        try:
            models = fetch_cloud_models_once(base_url, api_key, query)
            if models:
                return models
        except Exception as exc:
            errors.append(str(exc))

    details = "；".join(errors[-2:])
    raise RuntimeError(f"没有读取到云端模型列表。{details}")


def extract_with_cloud_api(
    pdf_path: Path,
    config: dict[str, Any],
    fields: list[dict[str, str]],
    key_to_label: dict[str, str],
    markdown_text: str,
    quality_hint: str = "",
) -> list[dict[str, Any]]:
    api_key = str(config.get("cloud_api_key") or "").strip()
    base_url = str(config.get("cloud_base_url") or "").strip()
    model = str(config.get("cloud_model") or config.get("model") or "").strip()
    if not api_key:
        raise RuntimeError("云端 API KEY 为空。请在页面填写 LLM API KEY。")
    if not base_url:
        raise RuntimeError("云端 BASE URL 为空。")
    if not model:
        raise RuntimeError("云端模型名称为空。")

    schema_lines = []
    for index, item in enumerate(fields, start=1):
        schema_lines.append(
            f'- "field_{index:02d}": {item["label"]} [{requirement_label(item.get("requirement", "optional"))}]，'
            f'{item["description"]}，{requirement_rule(item.get("requirement", "optional"))}，{missing_rule(item["type"])}'
        )

    messages = [
        {
            "role": "system",
            "content": (
                "你是专业的化工领域学术数据抽取助手。文献可能是中文、英文或中英混合。"
                "你必须只根据原文抽取，不要编造。"
                "只输出一个合法 JSON 对象，不要输出 Markdown，不要解释。"
                "JSON 顶层必须是 records 数组，例如 {\"records\":[{\"field_01\":\"...\"}]}。"
                "同一篇文献如果包含多个工艺、催化剂、实验条件、表格行或独立结果，就输出多条 records。"
                "任何字段缺失时留空字符串，不要输出 N/A、null 或 -999。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"文件名：{pdf_path.name}\n\n"
                "请按下面 JSON key 抽取字段：\n"
                + "\n".join(schema_lines)
                + (f"\n\n二次核查要求：\n{quality_hint}\n" if quality_hint else "")
                + "\n\nPDF 转换文本如下，可能已截断：\n\n"
                + markdown_text
            ),
        },
    ]
    content = cloud_chat_completion(base_url, api_key, model, messages, int(config.get("llm_timeout") or 0))
    raw = extract_json_object(content)
    return labeled_rows(raw, fields, key_to_label)


def tail_text(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


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

    # MinerU/fastText 在 Windows 上容易被中文虚拟环境或临时路径绊倒，输入输出统一走 ASCII 工作目录。
    safe_input = input_dir / "input.pdf"
    shutil.copy2(pdf_path, safe_input)

    command = [
        mineru_command,
        "-p",
        str(safe_input),
        "-o",
        str(output_dir),
        "-b",
        os.environ.get("MINERU_BACKEND", MINERU_DEFAULT_BACKEND),
        "-m",
        os.environ.get("MINERU_METHOD", MINERU_DEFAULT_METHOD),
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
        command,
        cwd=str(job_root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if result.returncode != 0:
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        raise RuntimeError(f"MinerU 解析失败，工作目录：{job_root}\n{tail_text(combined)}")

    markdown_files = sorted(output_dir.rglob("*.md"), key=lambda path: path.stat().st_size, reverse=True)
    if not markdown_files:
        generated = "\n".join(str(path) for path in output_dir.rglob("*"))
        raise FileNotFoundError(f"MinerU 未生成 Markdown 文件，工作目录：{job_root}\n已生成文件：\n{generated}")

    markdown_path = markdown_files[0]
    content = markdown_path.read_text(encoding="utf-8", errors="replace")
    return f"<!-- MinerU output: {markdown_path} -->\n\n{content}"


def markdown_text_char_count(markdown: str) -> int:
    return len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]", markdown))


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


RELEVANT_TEXT_KEYWORDS = (
    "abstract",
    "experiment",
    "experimental",
    "method",
    "materials",
    "results",
    "discussion",
    "table",
    "figure",
    "scheme",
    "catalyst",
    "reaction",
    "temperature",
    "pressure",
    "conversion",
    "selectivity",
    "yield",
    "gas hourly space velocity",
    "ghsv",
    "whsv",
    "工艺",
    "实验",
    "方法",
    "结果",
    "表",
    "图",
    "催化",
    "反应",
    "温度",
    "压力",
    "转化率",
    "选择性",
    "产率",
    "空速",
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


def short_error(exc: BaseException, limit: int = 500) -> str:
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def failed_source_path(input_dir: Path, pdf_path: Path) -> Path:
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
    return target_dir / safe_output_name(pdf_path.name)


def copy_failed_source(pdf_path: Path, input_dir: Path) -> Path:
    target_path = failed_source_path(input_dir, pdf_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf_path, target_path)
    return target_path


def record_failure(
    *,
    error_log_path: Path,
    pdf_path: Path,
    input_dir: Path,
    stage: str,
    exc: BaseException,
    state: JobState | None = None,
) -> None:
    log_error(error_log_path, pdf_path, stage, exc)
    copied_path = copy_failed_source(pdf_path, input_dir)
    if state is not None:
        state.add_log(f"失败环节：{stage}；原因：{short_error(exc)}；失败源文件已复制：{copied_path}")


def log_error(error_log_path: Path, pdf_path: Path, stage: str, exc: BaseException) -> None:
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    append_jsonl(
        error_log_path.with_name(ERROR_STATS_JSONL_NAME),
        {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "源文件名": pdf_path.name,
            "源文件路径": str(pdf_path),
            "失败环节": stage,
            "错误类型": type(exc).__name__,
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


def is_filled_cell(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return False
        return text.casefold() not in BAD_ROW_EMPTY_MARKERS
    return True


def field_weight(field: dict[str, str]) -> float:
    return BAD_ROW_FIELD_WEIGHTS.get(field.get("requirement", "optional"), 0.0)


def row_quality_stats(row: dict[str, Any], fields: list[dict[str, str]]) -> dict[str, Any]:
    filled_count = 0
    filled_weight = 0.0
    total_weight = 0.0
    missing_required: list[str] = []
    missing_recommended: list[str] = []

    for item in fields:
        label = item["label"]
        requirement = item.get("requirement", "optional")
        filled = is_filled_cell(row.get(label))
        if filled:
            filled_count += 1
        weight = field_weight(item)
        total_weight += weight
        if filled:
            filled_weight += weight
        elif requirement == "required":
            missing_required.append(label)
        elif requirement == "recommended":
            missing_recommended.append(label)

    weighted_rate = filled_weight / total_weight if total_weight else 1.0
    simple_rate = filled_count / len(fields) if fields else 1.0
    return {
        "filled_count": filled_count,
        "field_count": len(fields),
        "filled_weight": filled_weight,
        "total_weight": total_weight,
        "weighted_rate": weighted_rate,
        "simple_rate": simple_rate,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
    }


def calculate_fill_rate(row: dict[str, Any], fields: list[dict[str, str]]) -> float:
    """Return the weighted fill rate used by the bad-row filter."""
    return float(row_quality_stats(row, fields)["weighted_rate"])


def normalize_bad_row_min_fill_rate(value: Any = None) -> float:
    if value is None or value == "":
        return BAD_ROW_MIN_FILL_RATE
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return BAD_ROW_MIN_FILL_RATE
    if numeric > 1:
        numeric = numeric / 100.0
    return max(0.0, min(1.0, numeric))


def bad_row_min_fill_rate_from_config(config: dict[str, Any]) -> float:
    return normalize_bad_row_min_fill_rate(
        config.get("bad_row_min_fill_percent", config.get("bad_row_min_fill_rate", BAD_ROW_MIN_FILL_RATE))
    )


def row_is_bad_data(row: dict[str, Any], fields: list[dict[str, str]], min_fill_rate: float = BAD_ROW_MIN_FILL_RATE) -> bool:
    stats = row_quality_stats(row, fields)
    return bool(stats["total_weight"]) and float(stats["weighted_rate"]) < min_fill_rate


def is_bad_data(row: dict[str, Any], fields: list[dict[str, str]], min_fill_rate: float = BAD_ROW_MIN_FILL_RATE) -> bool:
    """Compatibility wrapper for tests and downstream integrations."""
    return row_is_bad_data(row, fields, min_fill_rate)


def rows_quality_score(rows: list[dict[str, Any]], fields: list[dict[str, str]]) -> float:
    if not rows:
        return 0.0
    return sum(float(row_quality_stats(row, fields)["weighted_rate"]) for row in rows) / len(rows)


def quality_retry_hint(rows: list[dict[str, Any]], fields: list[dict[str, str]], min_fill_rate: float = BAD_ROW_MIN_FILL_RATE) -> str:
    if not rows:
        return (
            "上一次没有抽取到有效 records。请重点核查标题、摘要、实验方法、表格、图注和结果部分，"
            "尽量补齐必填字段；原文确实没有的信息仍然留空，禁止编造。"
        )
    problem_lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        stats = row_quality_stats(row, fields)
        missing_required = stats["missing_required"]
        if missing_required or float(stats["weighted_rate"]) < min_fill_rate:
            problem_lines.append(
                f"第 {index} 条记录加权填写率 {float(stats['weighted_rate']):.1%}；"
                f"缺失必填字段：{', '.join(missing_required) if missing_required else '无'}；"
                f"缺失建议字段：{', '.join(stats['missing_recommended'][:10]) if stats['missing_recommended'] else '无'}。"
            )
    if not problem_lines:
        return ""
    return (
        "上一次抽取结果质量偏低，请重新阅读全文中的实验方法、表格、表注、图注和结果讨论，"
        "优先补齐必填字段。不要编造；原文确实没有的信息仍然留空。\n"
        + "\n".join(problem_lines[:8])
    )


def log_bad_data_row(
    error_log_path: Path,
    pdf_path: Path,
    *,
    row_number: int,
    stats: dict[str, Any],
    row: dict[str, Any],
    min_fill_rate: float = BAD_ROW_MIN_FILL_RATE,
) -> None:
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    preview = {
        key: value
        for key, value in row.items()
        if key not in EXPORT_EXCLUDED_COLUMNS and is_filled_cell(value)
    }
    preview_text = json.dumps(preview, ensure_ascii=False)
    if len(preview_text) > 3000:
        preview_text = preview_text[:2997] + "..."
    bad_rows_path = error_log_path.with_name(BAD_ROWS_JSONL_NAME)
    review_row = {
        "源文件名": pdf_path.name,
        "源文件路径": str(pdf_path),
        "记录序号": row_number,
        "加权填写率": round(float(stats["weighted_rate"]), 4),
        "普通填写率": round(float(stats["simple_rate"]), 4),
        "已填字段数": int(stats["filled_count"]),
        "总字段数": int(stats["field_count"]),
        "已填权重": round(float(stats["filled_weight"]), 3),
        "总权重": round(float(stats["total_weight"]), 3),
        "缺失必填字段": "；".join(stats["missing_required"]),
        "缺失建议字段": "；".join(stats["missing_recommended"]),
    }
    for key, value in row.items():
        if key not in EXPORT_EXCLUDED_COLUMNS:
            review_row[key] = value
    append_jsonl(bad_rows_path, review_row)
    append_jsonl(
        error_log_path.with_name(ERROR_STATS_JSONL_NAME),
        {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "源文件名": pdf_path.name,
            "源文件路径": str(pdf_path),
            "失败环节": "bad_data_low_fill_rate",
            "错误类型": "BadDataLowFillRate",
            "错误原因": (
                f"加权填写率 {float(stats['weighted_rate']):.1%} 低于 {min_fill_rate:.0%}，"
                f"缺失必填字段：{'；'.join(stats['missing_required']) or '无'}"
            ),
        },
    )
    with error_log_path.open("a", encoding="utf-8") as handle:
        handle.write("=" * 80 + "\n")
        handle.write(f"time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        handle.write(f"file: {pdf_path}\n")
        handle.write("stage: bad_data_low_fill_rate\n")
        handle.write(
            "error: "
            f"坏数据行已删除；第 {row_number} 条记录填写率 "
            f"{float(stats['weighted_rate']):.1%}，低于 {min_fill_rate:.0%} "
            f"阈值；已填写 {int(stats['filled_count'])}/{int(stats['field_count'])} 个抽取字段，"
            f"缺失必填字段：{'；'.join(stats['missing_required']) or '无'}。\n"
        )
        handle.write(f"bad_rows_file: {bad_rows_path}\n")
        handle.write(f"row_preview: {preview_text}\n")
        handle.write("\n")


def filter_bad_data_rows(
    rows: list[dict[str, Any]],
    fields: list[dict[str, str]],
    error_log_path: Path,
    *,
    default_pdf_path: Path,
    state: "JobState | None" = None,
    log_prefix: str = "",
    min_fill_rate: float = BAD_ROW_MIN_FILL_RATE,
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    removed = 0
    for row_number, row in enumerate(rows, start=1):
        stats = row_quality_stats(row, fields)
        if row_is_bad_data(row, fields, min_fill_rate):
            source_path = str(row.get("source_path") or "").strip()
            pdf_path = Path(source_path) if source_path else default_pdf_path
            log_bad_data_row(
                error_log_path,
                pdf_path,
                row_number=row_number,
                stats=stats,
                row=row,
                min_fill_rate=min_fill_rate,
            )
            removed += 1
            continue
        kept.append(row)
    if removed and state is not None:
        prefix = f"{log_prefix} " if log_prefix else ""
        state.add_log(f"{prefix}坏数据过滤：删除 {removed} 行（填写率低于 {min_fill_rate:.0%}），详见 {ERROR_LOG_NAME}")
    return kept


def split_multi_values(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;；,，、\s]+", text) if item.strip()]


def parse_numbers(value: Any) -> list[float]:
    text = clean_extracted_value(value)
    if not text:
        return []
    numbers: list[float] = []
    for match in re.findall(r"[-+]?\d+(?:\.\d+)?", text):
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    return numbers


def is_valid_cas(cas: str) -> bool:
    if not re.fullmatch(r"\d{2,7}-\d{2}-\d", cas):
        return False
    digits = cas.replace("-", "")
    check_digit = int(digits[-1])
    body = digits[:-1][::-1]
    checksum = sum((index + 1) * int(digit) for index, digit in enumerate(body)) % 10
    return checksum == check_digit


def validate_row_values(row: dict[str, Any], fields: list[dict[str, str]]) -> list[str]:
    issues: list[str] = []
    for item in fields:
        label = item["label"]
        value = row.get(label)
        text = clean_extracted_value(value)
        if not text:
            continue
        compact_label = label.replace(" ", "")

        if "CAS" in compact_label:
            candidates = [part for part in split_multi_values(text) if "-" in part or part.lower() != "cas"]
            if candidates and not any(is_valid_cas(part) for part in candidates):
                issues.append(f"{label}: CAS号格式或校验位可疑（{text}）")

        if "文献出处" in compact_label or "链接" in compact_label:
            if not text.startswith(("http://", "https://")):
                issues.append(f"{label}: 链接不是 http/https 开头（{text}）")

        if "温度" in compact_label:
            numbers = parse_numbers(value)
            if not numbers:
                issues.append(f"{label}: 未识别到温度数字（{text}）")
            elif any(number < -273.15 or number > 2000 for number in numbers):
                issues.append(f"{label}: 温度数值超出常规范围（{text}）")

        if "压力" in compact_label:
            numbers = parse_numbers(value)
            if not numbers:
                issues.append(f"{label}: 未识别到压力数字（{text}）")
            elif any(number < 0 or number > 1000 for number in numbers):
                issues.append(f"{label}: 压力数值超出常规范围（{text}）")

        if any(keyword in compact_label for keyword in ["转化率", "选择性", "产率"]):
            numbers = parse_numbers(value)
            if not numbers:
                issues.append(f"{label}: 未识别到百分比数字（{text}）")
            elif any(number < 0 or number > 100 for number in numbers):
                issues.append(f"{label}: 百分比数值不在 0-100 范围内（{text}）")
    return issues


def log_suspicious_rows(
    rows: list[dict[str, Any]],
    fields: list[dict[str, str]],
    suspicious_jsonl_path: Path,
    *,
    default_pdf_path: Path,
    issue_type: str = "value_validation",
) -> int:
    count = 0
    for row_number, row in enumerate(rows, start=1):
        issues = validate_row_values(row, fields)
        if not issues:
            continue
        source_path = str(row.get("source_path") or "").strip()
        pdf_path = Path(source_path) if source_path else default_pdf_path
        review_row = {
            "问题类型": issue_type,
            "源文件名": pdf_path.name,
            "源文件路径": str(pdf_path),
            "记录序号": row_number,
            "问题说明": "；".join(issues),
        }
        for key, value in row.items():
            if key not in EXPORT_EXCLUDED_COLUMNS:
                review_row[key] = value
        append_jsonl(suspicious_jsonl_path, review_row)
        count += 1
    return count


def clean_duplicate_value(value: Any) -> str:
    text = clean_extracted_value(value).lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，,;；。:.：%（）()]+", "", text)
    return text


def find_label_by_keywords(row: dict[str, Any], keywords: list[str]) -> str:
    for label in row:
        if any(keyword in label for keyword in keywords):
            value = clean_duplicate_value(row.get(label))
            if value:
                return value
    return ""


def duplicate_signature(row: dict[str, Any]) -> tuple[str, ...] | None:
    values = [
        find_label_by_keywords(row, ["工艺名称"]),
        find_label_by_keywords(row, ["催化剂通用名", "催化剂"]),
        find_label_by_keywords(row, ["反应温度", "温度"]),
        find_label_by_keywords(row, ["反应压力", "压力"]),
        find_label_by_keywords(row, ["转化率"]),
        find_label_by_keywords(row, ["选择性"]),
    ]
    nonempty = [value for value in values if value]
    if len(nonempty) < 4:
        return None
    return tuple(values)


def log_near_duplicates(rows: list[dict[str, Any]], suspicious_jsonl_path: Path) -> int:
    seen: dict[tuple[str, ...], dict[str, Any]] = {}
    duplicate_count = 0
    for row_number, row in enumerate(rows, start=1):
        signature = duplicate_signature(row)
        if signature is None:
            continue
        first = seen.get(signature)
        if first is None:
            seen[signature] = row
            continue
        review_row = {
            "问题类型": "near_duplicate",
            "源文件名": row.get("源文件名") or Path(str(row.get("source_path") or "")).name,
            "源文件路径": str(row.get("source_path") or ""),
            "记录序号": row_number,
            "问题说明": f"疑似与较早记录重复；签名={signature}",
            "首条源文件名": first.get("源文件名") or Path(str(first.get("source_path") or "")).name,
            "首条源文件路径": str(first.get("source_path") or ""),
        }
        for key, value in row.items():
            if key not in EXPORT_EXCLUDED_COLUMNS:
                review_row[key] = value
        append_jsonl(suspicious_jsonl_path, review_row)
        duplicate_count += 1
    return duplicate_count


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
    state: JobState,
    rows: list[dict[str, Any]],
    output_path: Path,
    runtime: RuntimeDeps,
    bad_rows_jsonl_path: Path | None = None,
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


def raw_records(raw: dict[str, Any]) -> list[dict[str, Any]]:
    records = raw.get("records")
    if isinstance(records, list):
        return [item for item in records if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


def blank_labeled_row(fields: list[dict[str, str]], key_to_label: dict[str, str]) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for index, _item in enumerate(fields, start=1):
        key = f"field_{index:02d}"
        row[key_to_label[key]] = ""
    return row


def labeled_rows(
    raw: dict[str, Any],
    fields: list[dict[str, str]],
    key_to_label: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in raw_records(raw):
        row: dict[str, Any] = {}
        for index, item in enumerate(fields, start=1):
            key = f"field_{index:02d}"
            label = key_to_label[key]
            row[label] = normalize_cloud_value(record.get(key), item["type"])
        rows.append(row)
    return rows or [blank_labeled_row(fields, key_to_label)]


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def processed_paths_from_rows(rows: list[dict[str, Any]]) -> set[str]:
    processed_paths: set[str] = set()
    for row in rows:
        source_path = str(row.get("source_path") or "").strip()
        if source_path:
            processed_paths.add(str(Path(source_path).resolve()).casefold())
    return processed_paths


def load_partial_rows(path: Path) -> tuple[list[dict[str, Any]], set[str]]:
    rows: list[dict[str, Any]] = []
    processed_paths: set[str] = set()
    if not path.exists():
        return rows, processed_paths
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
                source_path = str(row.get("source_path") or "").strip()
                if source_path:
                    processed_paths.add(str(Path(source_path).resolve()).casefold())
    return rows, processed_paths


def export_bad_rows_excel(bad_rows_jsonl_path: Path, bad_rows_excel_path: Path, runtime: RuntimeDeps) -> None:
    bad_rows = load_jsonl_rows(bad_rows_jsonl_path)
    if not bad_rows:
        return
    bad_rows_excel_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = runtime.pd.DataFrame(bad_rows)
    dataframe.to_excel(bad_rows_excel_path, index=False)


def export_jsonl_excel(jsonl_path: Path, excel_path: Path, runtime: RuntimeDeps) -> bool:
    rows = load_jsonl_rows(jsonl_path)
    if not rows:
        return False
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    runtime.pd.DataFrame(rows).to_excel(excel_path, index=False)
    return True


def export_excel(rows: list[dict[str, Any]], output_path: Path, runtime: RuntimeDeps) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        dataframe = runtime.pd.DataFrame(rows)
        dataframe = dataframe.drop(columns=EXPORT_EXCLUDED_COLUMNS, errors="ignore")
        dataframe = dataframe.replace(
            ["N/A", "n/a", "NA", "na", "null", "None", "-999", -999],
            "",
        )
    else:
        dataframe = runtime.pd.DataFrame([{"message": f"没有成功提取到任何结果，请查看 {ERROR_LOG_NAME}"}])
    dataframe.to_excel(output_path, index=False)


def export_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    """Export rows to CSV with internal metadata columns removed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clean_rows = []
    for row in rows:
        clean_rows.append({key: value for key, value in row.items() if key not in EXPORT_EXCLUDED_COLUMNS})
    if not clean_rows:
        clean_rows = [{"message": f"没有成功提取到任何结果，请查看 {ERROR_LOG_NAME}"}]
    fieldnames: list[str] = []
    for row in clean_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)


def add_source_metadata(
    rows: list[dict[str, Any]],
    *,
    pdf_path: Path,
    provider: str,
    model_name: str,
    pdf_mode: str,
    markdown_chars_total: int,
    markdown_chars_used: int,
    was_truncated: bool,
    llm_service: str = "",
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


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()


def extraction_cache_path(
    input_dir: Path,
    pdf_path: Path,
    config: dict[str, Any],
    fields: list[dict[str, str]],
    markdown: str,
    text_used: str,
) -> Path:
    provider = str(config.get("llm_provider") or "cloud")
    model_name = str(config.get("cloud_model") if provider == "cloud" else config.get("model") or "").strip()
    cache_key = stable_hash(
        {
            "version": EXTRACTION_CACHE_VERSION,
            "provider": provider,
            "model": model_name,
            "fields": fields,
            "pdf_mode": str(config.get("pdf_mode") or ""),
            "max_chars": int(config.get("max_chars") or 0),
            "markdown_hash": hashlib.sha1(markdown.encode("utf-8", errors="ignore")).hexdigest(),
            "text_hash": hashlib.sha1(text_used.encode("utf-8", errors="ignore")).hexdigest(),
        }
    )
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
        slim_rows.append({key: value for key, value in row.items() if key not in cache_excluded})
    payload = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": slim_rows,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def process_pdf(
    pdf_path: Path,
    input_dir: Path,
    config: dict[str, Any],
    runtime: RuntimeDeps,
    chains: list[tuple[str, Any]] | None,
    fields: list[dict[str, str]],
    key_to_label: dict[str, str],
    error_log_path: Path,
    state: JobState | None = None,
    progress_label: str = "",
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
                state.add_log(
                    "复用已有MD："
                    f"{progress_label} {pdf_path.name} "
                    f"({len(markdown)} 字符，路径：{cached_markdown_path})"
                )
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
            record_failure(
                error_log_path=error_log_path,
                pdf_path=pdf_path,
                input_dir=input_dir,
                stage="pdf_to_markdown",
                exc=exc,
                state=state,
            )
            return None
        add_stat(stage_stats, "pdf_to_md", time.perf_counter() - convert_started)
        source_images_dir = mineru_images_dir_from_markdown(markdown)
        markdown_path, _ = save_markdown_artifacts(markdown, pdf_path, input_dir, source_images_dir)
        if state is not None:
            state.add_log(
                "PDF转MD完成："
                f"{progress_label} {pdf_path.name} "
                f"({format_duration(time.perf_counter() - convert_started)}，"
                f"{len(markdown)} 字符，方式：{actual_pdf_mode}，已保存：{markdown_path})"
            )
    else:
        if markdown.startswith("<!-- MinerU output:"):
            actual_pdf_mode = "mineru"
        if state is not None:
            state.add_log(
                "跳过PDF转MD："
                f"{progress_label} {pdf_path.name} "
                f"(耗时 {format_duration(time.perf_counter() - convert_started)})"
            )

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
            cached_rows,
            pdf_path=pdf_path,
            provider=provider,
            model_name=cloud_model if provider == "cloud" else str(config.get("model") or ""),
            pdf_mode=actual_pdf_mode,
            markdown_chars_total=len(markdown),
            markdown_chars_used=len(text_used),
            was_truncated=was_truncated,
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
                    retry_rows = extract_with_cloud_api(
                        pdf_path,
                        config,
                        fields,
                        key_to_label,
                        text_used,
                        quality_hint=retry_hint,
                    )
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
                rows,
                pdf_path=pdf_path,
                provider="cloud",
                model_name=cloud_model,
                pdf_mode=actual_pdf_mode,
                markdown_chars_total=len(markdown),
                markdown_chars_used=len(text_used),
                was_truncated=was_truncated,
                llm_service=str(config.get("cloud_service_name") or "cloud"),
            )
            for row in rows:
                row["quality_retry_used"] = quality_retry_used
            save_extraction_cache(cache_path, rows)
            return rows
        except Exception as exc:
            record_failure(
                error_log_path=error_log_path,
                pdf_path=pdf_path,
                input_dir=input_dir,
                stage="cloud_llm_extraction",
                exc=exc,
                state=state,
            )
            return None

    for model_name, chain in chains or []:
        try:
            llm_started = time.perf_counter()
            result = chain.invoke(
                {
                    "file_name": pdf_path.name,
                    "field_instructions": instructions,
                    "markdown_text": text_used,
                    "quality_hint": "",
                }
            )
            add_stat(stage_stats, "llm_extraction", time.perf_counter() - llm_started)
            rows = labeled_rows(pydantic_to_dict(result), fields, key_to_label)
            quality_retry_used = False
            retry_hint = quality_retry_hint(rows, fields, bad_row_min_fill_rate)
            if retry_hint:
                try:
                    retry_started = time.perf_counter()
                    retry_result = chain.invoke(
                        {
                            "file_name": pdf_path.name,
                            "field_instructions": instructions,
                            "markdown_text": text_used,
                            "quality_hint": f"二次核查要求：\n{retry_hint}",
                        }
                    )
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
                rows,
                pdf_path=pdf_path,
                provider="ollama",
                model_name=model_name,
                pdf_mode=actual_pdf_mode,
                markdown_chars_total=len(markdown),
                markdown_chars_used=len(text_used),
                was_truncated=was_truncated,
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
        record_failure(
            error_log_path=error_log_path,
            pdf_path=pdf_path,
            input_dir=input_dir,
            stage="llm_extraction",
            exc=last_exc,
            state=state,
        )
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
            for stale_path in [
                bad_rows_jsonl_path,
                bad_rows_excel_path,
                suspicious_jsonl_path,
                suspicious_excel_path,
                error_stats_jsonl_path,
                error_stats_excel_path,
            ]:
                if stale_path.exists():
                    stale_path.unlink()

        if not input_dir.exists():
            raise RuntimeError(f"输入目录不存在：{input_dir}")

        pdf_files = list_pdf_files(input_dir, bool(config.get("recursive")))
        state_update(state, total=len(pdf_files), message="已扫描 PDF 文件")
        if not pdf_files:
            raise RuntimeError(f"没有找到 PDF 文件：{input_dir}")

        fields = normalize_fields(config.get("fields"))
        extraction_model, key_to_label = build_dynamic_model(fields, runtime)
        bad_row_min_fill_rate = bad_row_min_fill_rate_from_config(config)

        provider = str(config.get("llm_provider") or "cloud")
        available_models: list[str] = []

        if provider == "cloud":
            if not bool(config.get("cloud_active", False)):
                raise RuntimeError("云端 API 配置未激活。请勾选“激活此配置”。")
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
                (
                    item,
                    build_extraction_chain(
                        item,
                        str(config["ollama_base_url"]),
                        int(config["num_ctx"]),
                        int(config["llm_timeout"]),
                        runtime,
                        extraction_model,
                    ),
                )
                for item in order
            ]

        translation_batch_translator = None
        translation_model_name = ""
        if bool(config.get("translate_to_chinese", True)):
            try:
                translation_base_url = str(config.get("cloud_base_url") or "").strip()
                translation_api_key = str(config.get("cloud_api_key") or "").strip()
                translation_model_name = str(config.get("cloud_model") or config.get("model") or DEFAULT_CLOUD_MODEL).strip()
                if not translation_base_url or not translation_api_key or not translation_model_name:
                    raise RuntimeError("云端 API KEY、BASE URL 或模型名称为空。")
                translation_batch_translator = lambda batch: translate_item_batch_to_chinese_cloud(
                    translation_base_url,
                    translation_api_key,
                    translation_model_name,
                    batch,
                    int(config.get("llm_timeout") or 0),
                )
            except Exception as exc:
                state.add_log(f"云端中文翻译不可用，将保留原文：{exc}")

        rows, processed_paths = load_partial_rows(partial_jsonl_path)
        loaded_partial_count = len(rows)
        if rows:
            rows = filter_bad_data_rows(
                rows,
                fields,
                error_log_path,
                default_pdf_path=partial_jsonl_path,
                state=state,
                log_prefix="断点结果",
                min_fill_rate=bad_row_min_fill_rate,
            )
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
                pdf_path,
                input_dir,
                config,
                runtime,
                chains,
                fields,
                key_to_label,
                error_log_path,
                state,
                f"[{index}/{len(pdf_files)}]",
                stage_stats,
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
                pdf_rows = filter_bad_data_rows(
                    pdf_rows,
                    fields,
                    error_log_path,
                    default_pdf_path=pdf_path,
                    state=state,
                    log_prefix=pdf_path.name,
                    min_fill_rate=bad_row_min_fill_rate,
                )
                if not pdf_rows:
                    state_update(state, failed=state.snapshot()["failed"] + 1)
                    state.add_log(
                        f"坏数据：{pdf_path.name}（抽取到 {extracted_count} 条记录，但填写率均低于 {bad_row_min_fill_rate:.0%}，已删除，耗时 {format_duration(time.perf_counter() - pdf_started)}）"
                    )
                    state_update(state, done=index)
                    continue
                suspicious_count = log_suspicious_rows(
                    pdf_rows,
                    fields,
                    suspicious_jsonl_path,
                    default_pdf_path=pdf_path,
                )
                if suspicious_count:
                    add_stat(stage_stats, "suspicious_rows", suspicious_count)
                    state.add_log(f"可疑数据：{pdf_path.name}（{suspicious_count} 条，详见 {SUSPICIOUS_ROWS_EXCEL_NAME}）")
                rows.extend(pdf_rows)
                for row in pdf_rows:
                    append_jsonl(partial_jsonl_path, row)
                state_update(state, success=state.snapshot()["success"] + 1)
                state.add_log(
                    f"成功：{pdf_path.name}（{len(pdf_rows)} 条记录，耗时 {format_duration(time.perf_counter() - pdf_started)}，"
                    f"{eta_text(total_started, index, len(pdf_files))}）"
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
        state.add_log(f"任务异常：{exc}")
        try:
            export_jsonl_excel(error_stats_jsonl_path, error_stats_excel_path, runtime)
        except Exception:
            pass
        state.add_log(f"总耗时：{format_duration(time.perf_counter() - total_started)}")
        state_update(state, message=f"任务异常：{exc}")
    finally:
        state_update(state, running=False, pause_requested=False, finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


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


HTML_PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Chem-PDF-Extractor</title>
  <style>
    :root {
      --bg: #eef2f6;
      --panel: #ffffff;
      --panel-soft: #f8fafc;
      --text: #172033;
      --muted: #667085;
      --line: #d7dde8;
      --line-strong: #c5cfdd;
      --blue: #1f6feb;
      --green: #0f8a5f;
      --red: #c2410c;
      --focus: rgba(31, 111, 235, .18);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      color: var(--text);
      background: var(--bg);
      min-width: 360px;
      overflow-x: hidden;
    }
    header { display: none; }
    header h1 {
      font-size: 20px;
      margin: 0;
      font-weight: 800;
      letter-spacing: 0;
      color: #111827;
    }
    header h1::before {
      content: "";
      display: inline-block;
      width: 10px;
      height: 22px;
      margin-right: 10px;
      border-radius: 999px;
      background: var(--blue);
      vertical-align: -4px;
    }
    main { width: 100%; max-width: 1680px; margin: 0 auto; padding: 12px 16px; overflow-x: hidden; }
    .top-grid {
      display: grid;
      grid-template-columns: minmax(0, 3fr) minmax(0, 3fr) minmax(0, 4fr);
      gap: 14px;
      align-items: stretch;
      margin-bottom: 12px;
      height: min(760px, calc(100vh - 24px));
      overflow: hidden;
    }
    .config-stack {
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-width: 0;
      height: 100%;
      overflow: hidden;
    }
    .left-stack {
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-width: 0;
      height: 100%;
      overflow: hidden;
    }
    .app-logo {
      flex: 0 0 auto;
      display: flex;
      align-items: center;
      gap: 10px;
      min-height: 48px;
      padding: 0 4px;
      color: #0f172a;
      font-size: 22px;
      font-weight: 800;
      line-height: 1;
    }
    .app-logo::before {
      content: "";
      width: 10px;
      height: 26px;
      border-radius: 999px;
      background: var(--blue);
      flex: 0 0 auto;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 12px;
      box-shadow: none;
      position: relative;
      overflow: hidden;
    }
    section::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: #dbe7f7;
    }
    .top-grid section, .config-stack section, .left-stack section { margin-bottom: 0; }
    .log-panel {
      min-height: 100%;
      min-width: 0;
    }
    .task-panel {
      flex: 1 1 0;
      display: flex;
      flex-direction: column;
      min-height: 0;
      min-width: 0;
      overflow: hidden;
    }
    .task-panel > .small { margin-top: auto; }
    .api-panel, .progress-panel { min-height: 0; min-width: 0; }
    .api-panel {
      flex: 0 0 auto;
      overflow: hidden;
    }
    .progress-panel {
      flex: 1 1 0;
      display: flex;
      flex-direction: column;
    }
    .log-panel {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .fields-panel {
      margin-bottom: 0;
      overflow-x: auto;
    }
    h2 {
      font-size: 15px;
      margin: 0 0 12px;
      padding-left: 10px;
      border-left: 3px solid var(--blue);
      line-height: 1.2;
    }
    .top-grid h2 { font-size: 18px; }
    .top-grid label { font-size: 13px; }
    .top-grid input, .top-grid select, .top-grid button { font-size: 15px; }
    label { display: block; font-size: 12px; color: var(--muted); margin: 8px 0 5px; font-weight: 650; }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      min-height: 34px;
      padding: 7px 10px;
      font-size: 14px;
      background: #fbfdff;
      color: var(--text);
      transition: border-color .15s ease, box-shadow .15s ease;
    }
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: var(--blue);
      box-shadow: none;
    }
    textarea { min-height: 54px; resize: vertical; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .row > div { display: flex; flex-direction: column; }
    .row > div > label { height: 42px; display: flex; align-items: flex-end; line-height: 1.25; }
    .inline-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; align-items: center; }
    .checks { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 10px; color: var(--muted); font-size: 13px; }
    .checks label { display: inline-flex; align-items: center; gap: 6px; margin: 0; }
    .checks input { width: auto; }
    .cloud-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 12px;
    }
    .cloud-actions .checks { margin-top: 0; }
    .cloud-actions button { flex: 0 0 auto; }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--text);
      border-radius: 6px;
      min-height: 34px;
      padding: 7px 12px;
      cursor: pointer;
      font-weight: 600;
      transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease, background .12s ease;
    }
    button:hover:not(:disabled) { border-color: var(--line-strong); background: #f8fafc; }
    button.primary { background: var(--blue); border-color: var(--blue); color: #fff; }
    button.primary:hover:not(:disabled) { background: #195ec7; border-color: #195ec7; }
    button.danger { background: #fff; border-color: #fecaca; color: var(--red); }
    button.danger:hover:not(:disabled) { background: #fff7ed; border-color: #fdba74; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .actions { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
    .action-row { display: flex; gap: 10px; flex-wrap: wrap; }
    .action-row + .action-row { margin-top: 8px; }
    table { width: 100%; min-width: 1080px; table-layout: fixed; border-collapse: collapse; font-size: 13px; }
    .field-name-col { width: 28%; }
    .requirement-col { width: 7%; }
    .field-desc-col { width: 56%; }
    .move-col { width: 6%; }
    .remove-col { width: 3%; }
    th, td { border-bottom: 1px solid var(--line); padding: 8px 6px; vertical-align: top; }
    th { text-align: left; color: var(--muted); font-weight: 650; background: var(--panel-soft); }
    td.requirement { width: 96px; }
    td.move { width: 86px; white-space: nowrap; text-align: center; }
    td.remove { width: 48px; text-align: right; }
    .field-input { padding: 7px; }
    .mini-btn { padding: 6px 8px; min-width: 34px; }
    .progress-wrap { height: 14px; background: #e4e9f1; border-radius: 999px; overflow: hidden; border: 1px solid #d4dce8; }
    .progress-bar { height: 100%; width: 0%; background: var(--blue); transition: width .25s ease; }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin: 12px 0;
    }
    .progress-panel .stats { grid-template-columns: repeat(2, 1fr); }
    .stat {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: var(--panel-soft);
      box-shadow: none;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .stat b { display: block; flex: 0 0 auto; font-size: 24px; line-height: 1; color: #10213f; }
    .stat span { color: var(--muted); font-size: 13px; line-height: 1.2; }
    .status-box {
      min-height: 82px;
      max-height: 82px;
      margin-top: 8px;
      display: grid;
      grid-template-rows: repeat(3, 1fr);
      align-content: start;
    }
    .status-line {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    pre {
      height: 320px;
      overflow: auto;
      margin: 0;
      padding: 12px;
      background: #0b1020;
      color: #00ff66;
      border-radius: 8px;
      border: 1px solid #0f8a5f;
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
      text-shadow: none;
    }
    pre::-webkit-scrollbar { width: 12px; }
    pre::-webkit-scrollbar-track { background: #111827; border-left: 1px solid #1f2937; }
    pre::-webkit-scrollbar-thumb { background: #7a7f87; border-radius: 999px; border: 2px solid #111827; }
    pre::-webkit-scrollbar-thumb:hover { background: #9ca3af; }
    .log-panel pre {
      flex: 1;
      min-height: 0;
      height: auto;
    }
    .small { color: var(--muted); font-size: 12px; line-height: 1.45; }
    @media (max-width: 980px) {
      .top-grid { grid-template-columns: repeat(2, minmax(320px, 1fr)); }
      .log-panel { grid-column: 1 / -1; }
    }
    @media (max-width: 760px) {
      body { overflow-x: auto; }
      main { overflow-x: visible; }
      .top-grid { grid-template-columns: 1fr; height: auto; min-height: 0; overflow: visible; }
      .stats { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <main>
    <div class="top-grid">
      <div class="left-stack">
        <div class="app-logo">Chem-PDF-Extractor</div>
        <section class="task-panel">
          <h2>任务设置</h2>
          <label>PDF 输入目录</label>
          <input id="inputDir" />
          <label>Excel 输出路径</label>
          <input id="outputPath" />
          <label>LLM 提供方</label>
          <select id="llmProvider" onchange="onProviderChange()">
            <option value="cloud">云端 OpenAI-compatible API</option>
            <option value="ollama">本地 Ollama</option>
          </select>
          <div class="row">
            <div>
              <label>本地 Ollama 模型</label>
              <select id="model"></select>
            </div>
            <div>
              <label>PDF 到 Markdown / 文本方式</label>
              <select id="pdfMode">
                <option value="mineru">MinerU pipeline Markdown（推荐：质量优先）</option>
                <option value="auto">自动选择（先快后精）</option>
                <option value="pymupdf4llm">pymupdf4llm 高保真 Markdown</option>
                <option value="pymupdf_text">PyMuPDF 普通文本</option>
                <option value="pypdf_text">pypdf 普通文本</option>
              </select>
            </div>
          </div>
          <div class="row">
            <div>
              <label>上传最大字符数（0 表示不截断）</label>
              <input id="maxChars" type="number" value="0" min="0" />
            </div>
            <div>
              <label>Ollama num_ctx</label>
              <input id="numCtx" type="number" value="8192" min="1024" />
            </div>
          </div>
          <div class="row">
            <div>
              <label>LLM 超时秒数（0 表示不限制）</label>
              <input id="llmTimeout" type="number" value="0" min="0" />
            </div>
            <div>
              <label>错误百分比（低于此百分比判为坏数据）</label>
              <input id="badRowMinFillPercent" type="number" value="40" min="0" max="100" step="1" />
            </div>
          </div>
          <label>Ollama 地址</label>
          <input id="ollamaBaseUrl" value="http://127.0.0.1:11434" />
          <div class="checks">
            <label><input id="recursive" type="checkbox" /> 递归处理子文件夹</label>
            <label><input id="autoFallback" type="checkbox" /> 模型失败时尝试备选模型</label>
          </div>
          <div class="actions">
            <div class="action-row">
              <button class="primary" id="startBtn" onclick="startJob()">开始处理</button>
            </div>
            <div class="action-row">
              <button id="pauseBtn" onclick="pauseJob()">暂停任务</button>
              <button id="resumeBtn" onclick="resumeJob()">继续任务</button>
              <button class="danger" id="stopBtn" onclick="stopJob()">停止任务</button>
            </div>
          </div>
        </section>
      </div>

      <div class="config-stack">
        <section id="cloudPanel" class="api-panel" style="display:none;">
          <h2>编辑 LLM API 配置</h2>
          <label>LLM 服务名称 <span style="color:#d92d20">*</span></label>
          <input id="cloudServiceName" placeholder="例如：silicon / deepseek / openrouter" />
          <label>模型名称</label>
          <div class="inline-row">
            <select id="cloudModel">
              __DEFAULT_CLOUD_MODEL_OPTIONS__
            </select>
            <button type="button" onclick="loadCloudModels()">读取云端模型</button>
          </div>
          <label>LLM API KEY</label>
          <input id="cloudApiKey" type="password" autocomplete="off" placeholder="YOUR_API_KEY_HERE" />
          <label>LLM BASE URL</label>
          <input id="cloudBaseUrl" placeholder="https://api.siliconflow.cn/v1" />
          <div class="cloud-actions">
            <div class="checks">
              <label><input id="cloudActive" type="checkbox" /> 激活此配置（云端模式必须勾选）</label>
            </div>
            <button type="button" onclick="saveLocalConfig()">保存本地配置</button>
            <button type="button" onclick="loadModels()">刷新模型</button>
          </div>
          <p class="small">兼容 SiliconFlow、DeepSeek、OpenRouter 等 OpenAI-compatible 接口。仓库不内置真实 Key；可在页面填写并保存到本地 config.local.json，运行日志和 Excel 不记录 Key。</p>
        </section>

        <section class="progress-panel">
          <h2>进度</h2>
          <div class="progress-wrap"><div id="progressBar" class="progress-bar"></div></div>
          <div class="stats">
            <div class="stat"><b id="done">0</b><span>已处理</span></div>
            <div class="stat"><b id="total">0</b><span>总数</span></div>
            <div class="stat"><b id="success">0</b><span>成功</span></div>
            <div class="stat"><b id="failed">0</b><span>失败</span></div>
          </div>
          <div class="status-box">
            <div id="message" class="status-line">等待任务</div>
            <div id="currentFile" class="status-line"></div>
            <div id="outputInfo" class="status-line"></div>
          </div>
        </section>
      </div>

        <section class="log-panel">
          <h2>运行日志</h2>
          <pre id="logs"></pre>
        </section>
    </div>

        <section class="fields-panel">
          <h2>抽取字段</h2>
          <table>
            <colgroup>
              <col class="field-name-col" />
              <col class="requirement-col" />
              <col class="field-desc-col" />
              <col class="move-col" />
              <col class="remove-col" />
            </colgroup>
            <thead>
              <tr><th>字段名</th><th class="requirement">要求</th><th>字段说明</th><th class="move">排序</th><th class="remove"></th></tr>
            </thead>
            <tbody id="fieldsBody"></tbody>
          </table>
          <div class="actions">
            <button onclick="addField()">添加字段</button>
            <button onclick="resetFields()">恢复默认字段</button>
          </div>
          <p class="small">说明：后台会根据字段名和说明自动判断输出格式；必填字段会要求 AI 优先检索并尽最大努力抽取。</p>
        </section>
  </main>

  <script>
    const defaultFields = __DEFAULT_FIELDS_JSON__;
    const defaults = __DEFAULT_CONFIG_JSON__;

    function fieldRow(field = {label: "", requirement: "optional", description: ""}) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><input class="field-input label" value="${escapeHtml(field.label || "")}" placeholder="例如：催化剂" /></td>
        <td class="requirement">
          <select class="field-input requirement-select">
            <option value="required">必填</option>
            <option value="recommended">建议</option>
            <option value="optional">选填</option>
          </select>
        </td>
        <td><textarea class="field-input desc" placeholder="告诉模型这个字段要提取什么">${escapeHtml(field.description || "")}</textarea></td>
        <td class="move">
          <button type="button" class="mini-btn" title="上移" onclick="moveField(this, -1)">上</button>
          <button type="button" class="mini-btn" title="下移" onclick="moveField(this, 1)">下</button>
        </td>
        <td class="remove"><button onclick="removeField(this)">删</button></td>
      `;
      tr.querySelector(".requirement-select").value = field.requirement || "optional";
      return tr;
    }

    function escapeHtml(text) {
      return String(text).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
    }

    function moveField(button, direction) {
      const row = button.closest("tr");
      if (!row) return;
      if (direction < 0 && row.previousElementSibling) {
        row.parentNode.insertBefore(row, row.previousElementSibling);
      }
      if (direction > 0 && row.nextElementSibling) {
        row.parentNode.insertBefore(row.nextElementSibling, row);
      }
    }

    function removeField(button) {
      button.closest("tr").remove();
    }

    function addField(field) {
      const body = document.getElementById("fieldsBody");
      body.appendChild(fieldRow(field));
    }

    function resetFields() {
      const body = document.getElementById("fieldsBody");
      body.innerHTML = "";
      defaultFields.forEach(addField);
    }

    function collectFields() {
      return Array.from(document.querySelectorAll("#fieldsBody tr")).map(row => ({
        label: row.querySelector(".label").value.trim(),
        requirement: row.querySelector(".requirement-select").value,
        description: row.querySelector(".desc").value.trim()
      })).filter(item => item.label)
        .map(({label, requirement, description}) => ({label, requirement, description}));
    }

    async function loadModels() {
      const baseUrl = document.getElementById("ollamaBaseUrl").value.trim();
      const select = document.getElementById("model");
      select.innerHTML = "";
      try {
        const res = await fetch("/api/models?base_url=" + encodeURIComponent(baseUrl));
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || "模型读取失败");
        data.models.forEach(name => {
          const opt = document.createElement("option");
          opt.value = name;
          opt.textContent = name;
          select.appendChild(opt);
        });
        if (data.default_model) select.value = data.default_model;
      } catch (err) {
        const opt = document.createElement("option");
        opt.value = defaults.model;
        opt.textContent = defaults.model;
        select.appendChild(opt);
        alert("无法读取 Ollama 模型：" + err.message);
      }
    }

    function fillCloudModelSuggestions(models, selectedValue = "") {
      const select = document.getElementById("cloudModel");
      const previous = selectedValue || select.value;
      select.innerHTML = "";
      models.forEach(name => {
        const opt = document.createElement("option");
        opt.value = name;
        opt.textContent = name;
        select.appendChild(opt);
      });
      if (previous && models.includes(previous)) select.value = previous;
      else if (models.length) select.value = models[0];
    }

    async function loadCloudModels() {
      const baseUrl = document.getElementById("cloudBaseUrl").value.trim();
      const apiKey = document.getElementById("cloudApiKey").value.trim();
      const modelSelect = document.getElementById("cloudModel");
      const previousModel = modelSelect.value;
      if (!baseUrl || !apiKey) {
        alert("请先填写 LLM BASE URL 和 LLM API KEY。");
        return;
      }
      try {
        const res = await fetch("/api/cloud-models", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({base_url: baseUrl, api_key: apiKey})
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || "云端模型读取失败");
        fillCloudModelSuggestions(data.models || [], previousModel);
        if (data.default_model && (data.models || []).includes(data.default_model) && !previousModel) {
          modelSelect.value = data.default_model;
        }
        alert("已读取云端模型：" + (data.models || []).length + " 个。");
      } catch (err) {
        alert("无法读取云端模型：" + err.message);
      }
    }

    async function saveLocalConfig() {
      const payload = {
        llm_service_name: document.getElementById("cloudServiceName").value.trim(),
        api_key: document.getElementById("cloudApiKey").value.trim(),
        base_url: document.getElementById("cloudBaseUrl").value.trim(),
        model: document.getElementById("cloudModel").value.trim(),
        cloud_active: document.getElementById("cloudActive").checked
      };
      try {
        const res = await fetch("/api/config", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || "保存失败");
        alert("已保存到本地 config.local.json。该文件已加入 .gitignore，不应上传 GitHub。");
      } catch (err) {
        alert("本地配置保存失败：" + err.message);
      }
    }

    function onProviderChange() {
      const provider = document.getElementById("llmProvider").value;
      const cloudPanel = document.getElementById("cloudPanel");
      cloudPanel.style.display = provider === "cloud" ? "block" : "none";
      document.getElementById("autoFallback").disabled = provider === "cloud";
    }

    async function startJob() {
      const provider = document.getElementById("llmProvider").value;
      if (provider === "cloud" && !document.getElementById("cloudActive").checked) {
        alert("请先勾选“激活此配置”，再使用云端 API。");
        return;
      }
      const selectedModel = provider === "cloud"
        ? document.getElementById("cloudModel").value.trim()
        : document.getElementById("model").value;
      const payload = {
        input_dir: document.getElementById("inputDir").value.trim(),
        output_path: document.getElementById("outputPath").value.trim(),
        llm_provider: provider,
        model: selectedModel,
        translate_to_chinese: true,
        cloud_service_name: document.getElementById("cloudServiceName").value.trim(),
        cloud_model: document.getElementById("cloudModel").value.trim(),
        cloud_api_key: document.getElementById("cloudApiKey").value.trim(),
        cloud_base_url: document.getElementById("cloudBaseUrl").value.trim(),
        cloud_active: document.getElementById("cloudActive").checked,
        pdf_mode: document.getElementById("pdfMode").value,
        max_chars: Number(document.getElementById("maxChars").value || 0),
        num_ctx: Number(document.getElementById("numCtx").value || 8192),
        llm_timeout: Number(document.getElementById("llmTimeout").value || 0),
        bad_row_min_fill_percent: Number(document.getElementById("badRowMinFillPercent").value || 40),
        ollama_base_url: document.getElementById("ollamaBaseUrl").value.trim(),
        recursive: document.getElementById("recursive").checked,
        auto_fallback: document.getElementById("autoFallback").checked,
        fields: collectFields()
      };
      const res = await fetch("/api/start", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
      const data = await res.json();
      if (!data.ok) alert(data.error || "启动失败");
      pollStatus();
    }

    async function stopJob() {
      await fetch("/api/stop", {method: "POST"});
      pollStatus();
    }

    async function pauseJob() {
      await fetch("/api/pause", {method: "POST"});
      pollStatus();
    }

    async function resumeJob() {
      await fetch("/api/resume", {method: "POST"});
      pollStatus();
    }

    async function pollStatus() {
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        document.getElementById("progressBar").style.width = (data.percent || 0) + "%";
        document.getElementById("done").textContent = data.done || 0;
        document.getElementById("total").textContent = data.total || 0;
        document.getElementById("success").textContent = data.success || 0;
        document.getElementById("failed").textContent = data.failed || 0;
        document.getElementById("message").textContent = data.message || "";
        document.getElementById("currentFile").textContent = data.current_file ? "当前文件：" + data.current_file : "";
        document.getElementById("outputInfo").textContent = data.output_path ? "输出：" + data.output_path + " | 错误日志：" + data.error_log_path : "";
        document.getElementById("logs").textContent = (data.logs || []).join("\n");
        document.getElementById("startBtn").disabled = !!data.running;
        document.getElementById("stopBtn").disabled = !data.running;
        document.getElementById("pauseBtn").disabled = !data.running || !!data.pause_requested;
        document.getElementById("resumeBtn").disabled = !data.running || !data.pause_requested;
      } catch (err) {
        document.getElementById("message").textContent = "无法连接本地服务。";
      }
    }

    function init() {
      document.getElementById("inputDir").value = defaults.input_dir;
      document.getElementById("outputPath").value = defaults.output_path;
      document.getElementById("llmProvider").value = defaults.llm_provider || "cloud";
      document.getElementById("ollamaBaseUrl").value = defaults.ollama_base_url;
      document.getElementById("cloudServiceName").value = defaults.cloud_service_name;
      fillCloudModelSuggestions(defaults.cloud_model_suggestions || [], defaults.cloud_model);
      document.getElementById("cloudApiKey").value = defaults.cloud_api_key || "";
      document.getElementById("cloudBaseUrl").value = defaults.cloud_base_url;
      document.getElementById("cloudActive").checked = defaults.cloud_active !== false;
      document.getElementById("recursive").checked = defaults.recursive !== false;
      document.getElementById("maxChars").value = defaults.max_chars;
      document.getElementById("numCtx").value = defaults.num_ctx;
      document.getElementById("llmTimeout").value = "0";
      document.getElementById("badRowMinFillPercent").value = defaults.bad_row_min_fill_percent;
      resetFields();
      onProviderChange();
      loadModels();
      pollStatus();
      setInterval(pollStatus, 1000);
    }
    init();
  </script>
</body>
</html>
"""


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
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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
                "cloud_api_key": local_config.get("cloud_api_key") or os.environ.get("CHEM_PDF_EXTRACTOR_API_KEY") or os.environ.get("CHEM_EXTRACTOR_CLOUD_API_KEY") or DEFAULT_CLOUD_API_KEY,
                "cloud_base_url": local_config.get("cloud_base_url") or os.environ.get("CHEM_PDF_EXTRACTOR_BASE_URL") or DEFAULT_CLOUD_BASE_URL,
                "cloud_active": local_config.get("cloud_active", True),
                "recursive": True,
                "max_chars": DEFAULT_MAX_CHARS,
                "num_ctx": DEFAULT_NUM_CTX,
                "bad_row_min_fill_percent": int(BAD_ROW_MIN_FILL_RATE * 100),
            }
            html = HTML_PAGE.replace("__DEFAULT_FIELDS_JSON__", json.dumps(DEFAULT_FIELDS, ensure_ascii=False))
            html = html.replace("__DEFAULT_CONFIG_JSON__", json.dumps(defaults, ensure_ascii=False))
            model_options = "\n".join(
                f'                <option value="{html_lib.escape(model)}">{html_lib.escape(model)}</option>'
                for model in DEFAULT_CLOUD_MODEL_SUGGESTIONS
            )
            html = html.replace("__DEFAULT_CLOUD_MODEL_OPTIONS__", model_options)
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

        self.send_json({"ok": False, "error": "not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/config":
            try:
                config = self.read_json()
                save_local_config(config)
                self.send_json({"ok": True})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)})
            return

        if parsed.path == "/api/cloud-models":
            try:
                config = self.read_json()
                base_url = str(config.get("base_url") or DEFAULT_CLOUD_BASE_URL).strip()
                api_key = str(config.get("api_key") or "").strip()
                models = get_cloud_models(base_url, api_key)
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
                thread = threading.Thread(target=run_extraction_job, args=(config, self.app.runtime, self.app.state), daemon=True)
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


def start_web_app(port: int, auto_install: bool) -> int:
    ensure_dependencies(auto_install=auto_install)
    runtime = import_runtime_dependencies()
    app = ChemExtractorApp(runtime)
    actual_port = find_free_port(port)
    server = ThreadingHTTPServer(("127.0.0.1", actual_port), RequestHandler)
    app.server = server
    RequestHandler.app = app

    url = f"http://127.0.0.1:{actual_port}/"
    print(f"Chem-PDF-Extractor 页面已启动：{url}")
    print("关闭浏览器标签页不会停止正在运行的本地服务；需要停止任务请点页面里的“停止任务”。")
    webbrowser.open(url)

    try:
        server.serve_forever()
    finally:
        server.server_close()
        print("Chem-PDF-Extractor 本地服务已关闭。")
    return 0


def run_cli(args: argparse.Namespace) -> int:
    ensure_dependencies(auto_install=not args.no_auto_install)
    runtime = import_runtime_dependencies()
    state = JobState()
    local_cloud_config = load_local_config()
    config = {
        "input_dir": args.input_dir or str(default_input_dir()),
        "output_path": args.output or str(default_output_path()),
        "llm_provider": args.llm_provider,
        "model": args.cloud_model if args.llm_provider == "cloud" and args.model == DEFAULT_MODEL else args.model,
        "translate_to_chinese": not args.no_translate_to_chinese,
        "cloud_service_name": args.cloud_service_name or local_cloud_config.get("cloud_service_name") or DEFAULT_CLOUD_SERVICE_NAME,
        "cloud_model": args.cloud_model or local_cloud_config.get("cloud_model") or DEFAULT_CLOUD_MODEL,
        "cloud_api_key": (
            args.cloud_api_key
            or local_cloud_config.get("cloud_api_key")
            or os.environ.get("CHEM_PDF_EXTRACTOR_API_KEY", "")
            or os.environ.get("CHEM_EXTRACTOR_CLOUD_API_KEY", "")
            or DEFAULT_CLOUD_API_KEY
        ),
        "cloud_base_url": args.cloud_base_url or local_cloud_config.get("cloud_base_url") or DEFAULT_CLOUD_BASE_URL,
        "cloud_active": args.cloud_active or args.llm_provider == "cloud",
        "pdf_mode": args.pdf_mode,
        "max_chars": args.max_chars,
        "num_ctx": args.num_ctx,
        "llm_timeout": args.llm_timeout,
        "bad_row_min_fill_percent": args.bad_row_min_fill_percent,
        "ollama_base_url": args.ollama_base_url,
        "recursive": args.recursive,
        "auto_fallback": args.auto_fallback,
        "fields": DEFAULT_FIELDS,
    }
    run_extraction_job(config, runtime, state)
    snapshot = state.snapshot()
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chem-PDF-Extractor")
    parser.add_argument("--cli", action="store_true", help="不启动网页，直接用命令行参数处理。")
    parser.add_argument("--port", type=int, default=8766, help="网页端口，默认 8766。")
    parser.add_argument("--input-dir", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--llm-provider", default="cloud", choices=["ollama", "cloud"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--no-translate-to-chinese", action="store_true")
    parser.add_argument("--cloud-service-name", default=DEFAULT_CLOUD_SERVICE_NAME)
    parser.add_argument("--cloud-model", default=DEFAULT_CLOUD_MODEL)
    parser.add_argument("--cloud-api-key", default="")
    parser.add_argument("--cloud-base-url", default=DEFAULT_CLOUD_BASE_URL)
    parser.add_argument("--cloud-active", action="store_true")
    parser.add_argument("--pdf-mode", default="mineru", choices=["auto", "mineru", "pymupdf4llm", "pymupdf_text", "pypdf_text"])
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--num-ctx", type=int, default=DEFAULT_NUM_CTX)
    parser.add_argument("--llm-timeout", type=int, default=0, help="0 表示不限制。")
    parser.add_argument("--bad-row-min-fill-percent", type=float, default=BAD_ROW_MIN_FILL_RATE * 100)
    parser.add_argument("--ollama-base-url", default=DEFAULT_OLLAMA_BASE_URL)
    parser.set_defaults(recursive=True)
    parser.add_argument("--recursive", dest="recursive", action="store_true")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false")
    parser.add_argument("--auto-fallback", action="store_true")
    parser.add_argument("--no-auto-install", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cli:
        return run_cli(args)
    return start_web_app(args.port, auto_install=not args.no_auto_install)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n用户中断。")
