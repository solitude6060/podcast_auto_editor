from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

OK = "ok"
WARNING = "warning"
MISSING = "missing"


def _check(name: str, status: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"name": name, "status": status, "message": message}
    if details:
        payload["details"] = details
    return payload


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text()
    except OSError:
        return None


def _compose_checks(compose_file: Path) -> list[dict[str, Any]]:
    text = _read_text(compose_file)
    if text is None:
        return [_check("compose_file", MISSING, f"Compose file not found: {compose_file}")]

    checks = [_check("compose_file", OK, f"Compose file found: {compose_file}")]
    if "ollama:" in text and "ollama/ollama" in text:
        checks.append(_check("compose_ollama", OK, "Local Ollama service is declared."))
    else:
        checks.append(_check("compose_ollama", MISSING, "Compose file does not declare an ollama/ollama service."))

    if "127.0.0.1:11434:11434" in text:
        checks.append(_check("compose_ollama_localhost", OK, "Ollama port is bound to localhost."))
    else:
        checks.append(_check("compose_ollama_localhost", WARNING, "Ollama localhost binding was not detected; review network exposure before use."))

    has_gpu = "driver: nvidia" in text and ("capabilities: [gpu]" in text or "- gpu" in text)
    if has_gpu:
        checks.append(_check("compose_gpu", OK, "NVIDIA GPU reservation hint is present."))
    else:
        checks.append(_check("compose_gpu", MISSING, "NVIDIA GPU reservation hint is missing."))
    return checks


def _path_check(name: str, path: Path | None, label: str, required: bool) -> dict[str, Any]:
    if path is None:
        status = MISSING if required else WARNING
        return _check(name, status, f"{label} path was not provided.")
    if path.exists():
        return _check(name, OK, f"{label} exists.", {"path": str(path)})
    status = MISSING if required else WARNING
    return _check(name, status, f"{label} does not exist: {path}", {"path": str(path)})


def _minimax_check(env: dict[str, str]) -> dict[str, Any]:
    configured = bool(env.get("MINIMAX_API_KEY"))
    if configured:
        return _check("minimax_fallback", WARNING, "MINIMAX_API_KEY is configured; use only as explicit non-local fallback.", {"configured": True, "value": "<redacted>"})
    return _check("minimax_fallback", OK, "MINIMAX_API_KEY is not configured; local-first default is preserved.", {"configured": False})


def _ollama_check(ollama_url: str, timeout_s: float) -> dict[str, Any]:
    url = ollama_url.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:
            body = response.read().decode("utf-8")
    except (OSError, urllib.error.URLError) as exc:
        return _check("ollama_connectivity", WARNING, f"Ollama did not respond within {timeout_s:g}s; start compose profile ai when needed.", {"url": ollama_url, "error": str(exc)})
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return _check("ollama_connectivity", WARNING, "Ollama responded but returned invalid JSON.", {"url": ollama_url})
    model_count = len(data.get("models") or []) if isinstance(data, dict) else 0
    return _check("ollama_connectivity", OK, f"Ollama responded with {model_count} installed model(s).", {"url": ollama_url, "model_count": model_count})


def _overall_status(checks: list[dict[str, Any]]) -> str:
    if any(check["status"] == MISSING for check in checks):
        return MISSING
    if any(check["status"] == WARNING for check in checks):
        return WARNING
    return OK


def build_ai_doctor_report(
    *,
    compose_file: str | Path = "compose.yaml",
    whisper_binary: str | Path | None = None,
    whisper_model: str | Path | None = None,
    ollama_url: str = "http://127.0.0.1:11434",
    check_ollama: bool = True,
    timeout_s: float = 0.5,
    env: dict[str, str] | None = None,
    require_whisper: bool = True,
) -> dict[str, Any]:
    env = dict(os.environ if env is None else env)
    binary_path = Path(whisper_binary) if whisper_binary is not None else (Path(env["WHISPER_CPP_BINARY"]) if env.get("WHISPER_CPP_BINARY") else None)
    model_path = Path(whisper_model) if whisper_model is not None else (Path(env["WHISPER_CPP_MODEL_PATH"]) if env.get("WHISPER_CPP_MODEL_PATH") else None)

    checks: list[dict[str, Any]] = []
    checks.extend(_compose_checks(Path(compose_file)))
    if check_ollama:
        checks.append(_ollama_check(ollama_url, timeout_s))
    else:
        checks.append(_check("ollama_connectivity", WARNING, "Ollama connectivity check skipped."))
    checks.append(_path_check("whisper_cpp_binary", binary_path, "whisper.cpp binary", require_whisper))
    checks.append(_path_check("whisper_cpp_model", model_path, "whisper.cpp model", require_whisper))
    checks.append(_minimax_check(env))
    return {"schema_version": "ai-doctor.v1", "overall_status": _overall_status(checks), "checks": checks}


def format_ai_doctor_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# AI Environment Doctor",
        "",
        f"Overall status: `{report['overall_status']}`",
        "",
        "| Check | Status | Message |",
        "| --- | --- | --- |",
    ]
    for check in report.get("checks") or []:
        lines.append(f"| {check['name']} | {check['status']} | {check['message']} |")
    return "\n".join(lines) + "\n"
