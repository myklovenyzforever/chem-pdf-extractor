from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .config import ERROR_LOG_NAME, EXPORT_EXCLUDED_COLUMNS, RuntimeDeps
from .text_safety import json_dumps_utf8, utf8_safe_obj


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json_dumps_utf8(row) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json_dumps_utf8(row) + "\n")


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
    dataframe = runtime.pd.DataFrame(utf8_safe_obj(bad_rows))
    dataframe.to_excel(bad_rows_excel_path, index=False)


def export_jsonl_excel(jsonl_path: Path, excel_path: Path, runtime: RuntimeDeps) -> bool:
    rows = load_jsonl_rows(jsonl_path)
    if not rows:
        return False
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    runtime.pd.DataFrame(utf8_safe_obj(rows)).to_excel(excel_path, index=False)
    return True


def export_excel(rows: list[dict[str, Any]], output_path: Path, runtime: RuntimeDeps) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        dataframe = runtime.pd.DataFrame(utf8_safe_obj(rows))
        dataframe = dataframe.drop(columns=EXPORT_EXCLUDED_COLUMNS, errors="ignore")
        dataframe = dataframe.replace(["N/A", "n/a", "NA", "na", "null", "None", "-999", -999], "")
    else:
        dataframe = runtime.pd.DataFrame(
            utf8_safe_obj([{"message": f"没有成功提取到任何结果，请查看 {ERROR_LOG_NAME}"}])
        )
    dataframe.to_excel(output_path, index=False)


def export_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clean_rows = []
    for row in rows:
        clean_rows.append({key: value for key, value in row.items() if key not in EXPORT_EXCLUDED_COLUMNS})
    clean_rows = utf8_safe_obj(clean_rows)
    if not clean_rows:
        clean_rows = utf8_safe_obj([{"message": f"没有成功提取到任何结果，请查看 {ERROR_LOG_NAME}"}])
    fieldnames: list[str] = []
    for row in clean_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)
