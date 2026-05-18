import json
from pathlib import Path

import podcast_auto_editor.cli as cli
from podcast_auto_editor.asr import ASRProviderError, StubTranscriptProvider, transcribe_to_file
from podcast_auto_editor.cli import main


def test_stub_provider_returns_valid_transcript_segments(tmp_path):
    provider = StubTranscriptProvider()

    payload = provider.transcribe(tmp_path / "episode.wav")

    assert payload["schema_version"] == "transcript.v1"
    assert payload["provider"] == "stub"
    assert payload["segments"] == [{"start": 0.0, "end": 1.0, "text": "Stub transcript for episode"}]


def test_transcribe_to_file_validates_and_writes_transcript(tmp_path):
    out = tmp_path / "transcript.json"

    path = transcribe_to_file(tmp_path / "episode.wav", out, provider_name="stub")

    assert path == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == "transcript.v1"
    assert data["segments"][0]["text"] == "Stub transcript for episode"
    assert data["segments"][0]["start"] == 0.0


def test_transcribe_to_file_rejects_unknown_provider_without_writing(tmp_path):
    out = tmp_path / "transcript.json"

    try:
        transcribe_to_file(tmp_path / "episode.wav", out, provider_name="missing")
    except ASRProviderError as exc:
        assert "unknown transcript provider" in str(exc)
    else:
        raise AssertionError("expected provider error")

    assert not out.exists()


def test_transcribe_to_file_rejects_invalid_provider_output_without_writing(tmp_path, monkeypatch):
    class BadProvider:
        name = "bad"

        def transcribe(self, input_path, **options):
            return {"schema_version": "transcript.v1", "segments": [{"start": 1.0, "end": 0.5, "text": "bad"}]}

    monkeypatch.setattr("podcast_auto_editor.asr.PROVIDERS", {"bad": BadProvider})
    out = tmp_path / "transcript.json"

    try:
        transcribe_to_file(tmp_path / "episode.wav", out, provider_name="bad")
    except ASRProviderError as exc:
        assert "segment[0].end must be after start" in str(exc)
    else:
        raise AssertionError("expected validation error")

    assert not out.exists()


def test_transcribe_cli_writes_stub_transcript(tmp_path, capsys):
    out = tmp_path / "transcript.json"

    assert main(["transcribe", str(tmp_path / "episode.wav"), "--provider", "stub", "--out", str(out)]) == 0

    assert capsys.readouterr().out.strip() == str(out)
    assert json.loads(out.read_text())["segments"][0]["text"] == "Stub transcript for episode"


def test_transcribe_cli_reports_provider_errors(tmp_path, capsys):
    out = tmp_path / "transcript.json"

    assert main(["transcribe", str(tmp_path / "episode.wav"), "--provider", "missing", "--out", str(out)]) == 1

    assert "unknown transcript provider" in capsys.readouterr().err
    assert not out.exists()


def test_provider_names_include_optional_faster_whisper():
    from podcast_auto_editor.asr import provider_names

    assert "stub" in provider_names()
    assert "faster-whisper-local" in provider_names()


def test_faster_whisper_provider_missing_dependency_does_not_write(tmp_path, monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "faster_whisper":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    out = tmp_path / "transcript.json"

    try:
        transcribe_to_file(tmp_path / "episode.wav", out, provider_name="faster-whisper-local")
    except ASRProviderError as exc:
        assert "faster-whisper-local requires optional package faster-whisper" in str(exc)
    else:
        raise AssertionError("expected missing dependency error")

    assert not out.exists()


def test_faster_whisper_provider_normalizes_segments(tmp_path, monkeypatch):
    import sys
    import types

    calls = {}

    class Segment:
        start = 0.25
        end = 1.5
        text = " hello world "

    class WhisperModel:
        def __init__(self, model, device="auto", compute_type="auto"):
            calls["init"] = {"model": model, "device": device, "compute_type": compute_type}

        def transcribe(self, input_path, beam_size=5):
            calls["transcribe"] = {"input_path": str(input_path), "beam_size": beam_size}
            return [Segment()], object()

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=WhisperModel))

    transcript = cli.transcribe_to_file(
        tmp_path / "episode.wav",
        tmp_path / "transcript.json",
        provider_name="faster-whisper-local",
        model="large-v3",
        device="cuda",
        compute_type="float16",
    )

    data = json.loads(transcript.read_text())
    assert calls["init"] == {"model": "large-v3", "device": "cuda", "compute_type": "float16"}
    assert calls["transcribe"]["beam_size"] == 5
    assert data["provider"] == "faster-whisper-local"
    assert data["segments"] == [{"start": 0.25, "end": 1.5, "text": "hello world"}]


def test_faster_whisper_provider_accepts_belle_whisper_zh_drop_in(tmp_path, monkeypatch):
    """PR-X1: BELLE-2/Belle-whisper-large-v3-zh is wire-compatible with
    faster-whisper. The provider must pass the HuggingFace model id through
    unchanged so users can drop in the Chinese-fine-tuned weights via
    `--model BELLE-2/Belle-whisper-large-v3-zh` without code changes."""
    import sys
    import types

    captured = {}

    class Segment:
        start = 0.0
        end = 1.0
        text = "你好"

    class WhisperModel:
        def __init__(self, model, device="auto", compute_type="auto"):
            captured["model"] = model

        def transcribe(self, input_path, beam_size=5):
            return [Segment()], object()

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=WhisperModel))

    cli.transcribe_to_file(
        tmp_path / "episode.wav",
        tmp_path / "transcript.json",
        provider_name="faster-whisper-local",
        model="BELLE-2/Belle-whisper-large-v3-zh",
        device="cuda",
        compute_type="float16",
    )

    assert captured["model"] == "BELLE-2/Belle-whisper-large-v3-zh"


def test_transcribe_wrapper_returns_only_canonical_fields(tmp_path, monkeypatch):
    """PR #47 review HIGH (Codex): asr.transcribe() wraps provider output and
    rebuilds the payload with ONLY {schema_version, provider, source_media,
    segments}. Provider-specific metadata such as `model`, `device`, and
    `compute_type` is intentionally dropped. This pins the wrapper contract so
    callers (and tests) do not assume provider-supplied fields survive.

    If a future change wants to preserve provider metadata in transcript.v1
    artifacts, that change is a separate PR with its own plan + schema bump.
    """
    # Use the stub provider; assert wrapper output keys
    from podcast_auto_editor import asr

    payload = asr.transcribe(tmp_path / "x.wav", provider_name="stub")
    assert set(payload.keys()) == {"schema_version", "provider", "source_media", "segments"}
    assert payload["schema_version"] == "transcript.v1"
    assert payload["provider"] == "stub"


def test_transcribe_cli_passes_faster_whisper_options(tmp_path, monkeypatch):
    captured = {}

    def fake_transcribe_to_file(input_path, out_path, provider_name="stub", **options):
        captured["input_path"] = str(input_path)
        captured["out_path"] = str(out_path)
        captured["provider_name"] = provider_name
        captured["options"] = options
        Path(out_path).write_text(json.dumps({"schema_version": "transcript.v1", "segments": [{"start": 0.0, "end": 1.0, "text": "ok"}]}))
        return Path(out_path)

    monkeypatch.setattr(cli, "transcribe_to_file", fake_transcribe_to_file)
    out = tmp_path / "transcript.json"

    assert main([
        "transcribe",
        str(tmp_path / "episode.wav"),
        "--provider",
        "faster-whisper-local",
        "--model",
        "large-v3",
        "--device",
        "cuda",
        "--compute-type",
        "float16",
        "--out",
        str(out),
    ]) == 0

    assert captured["provider_name"] == "faster-whisper-local"
    assert captured["options"] == {"model": "large-v3", "device": "cuda", "compute_type": "float16"}


def test_provider_names_include_qwen3_asr_local():
    """PR-X2: Qwen3-ASR provider registered as `qwen3-asr-local`."""
    from podcast_auto_editor.asr import provider_names

    assert "qwen3-asr-local" in provider_names()


def test_qwen3_asr_provider_missing_dependency_does_not_write(tmp_path, monkeypatch):
    """When `qwen_asr` is not installed, transcribe_to_file must raise
    ASRProviderError with a clear install hint AND not write any output."""
    import sys

    monkeypatch.setitem(sys.modules, "qwen_asr", None)  # type: ignore[arg-type]
    out = tmp_path / "transcript.json"
    try:
        cli.transcribe_to_file(
            tmp_path / "episode.wav",
            out,
            provider_name="qwen3-asr-local",
        )
    except Exception as exc:
        assert "qwen-asr" in str(exc).lower()
    else:
        raise AssertionError("expected ASRProviderError when qwen_asr import fails")
    assert not out.exists(), "transcribe_to_file must not write when provider raises"


def test_qwen3_asr_provider_normalizes_segments(tmp_path, monkeypatch):
    """Triple-review HIGH (Codex upstream verification): real `qwen-asr`
    exposes `Qwen3ASRModel.from_pretrained(...).transcribe(...)`, NOT a
    module-level `qwen_asr.transcribe(...)`. Test stubs the class API."""
    import sys
    import types

    captured: dict = {}

    class FakeQwen3ASRModel:
        @classmethod
        def from_pretrained(cls, model_id):
            captured["from_pretrained"] = model_id
            return cls()

        def transcribe(self, audio, language=None):
            captured["audio"] = audio
            captured["language"] = language
            return [
                {"start": 0.0, "end": 1.25, "text": "你好"},
                {"start": 1.25, "end": 2.5, "text": "歡迎收聽"},
            ]

    fake_module = types.SimpleNamespace(Qwen3ASRModel=FakeQwen3ASRModel)
    monkeypatch.setitem(sys.modules, "qwen_asr", fake_module)

    out = tmp_path / "transcript.json"
    cli.transcribe_to_file(
        tmp_path / "episode.wav",
        out,
        provider_name="qwen3-asr-local",
        model="Qwen/Qwen3-ASR-1.7B",
        language="zh",
    )

    data = json.loads(out.read_text())
    assert data["provider"] == "qwen3-asr-local"
    assert data["segments"] == [
        {"start": 0.0, "end": 1.25, "text": "你好"},
        {"start": 1.25, "end": 2.5, "text": "歡迎收聽"},
    ]
    assert captured["from_pretrained"] == "Qwen/Qwen3-ASR-1.7B"
    assert captured["language"] == "zh"


def test_qwen3_asr_provider_rejects_non_list_response(tmp_path, monkeypatch):
    """Triple-review HIGH: if the real qwen_asr API returns a dict or
    other non-list shape (e.g., `{"text": "...", "segments": [...]}`),
    the provider must raise ASRProviderError, NOT silently write
    `{segments: []}` to disk."""
    import sys
    import types

    class FakeQwen3ASRModel:
        @classmethod
        def from_pretrained(cls, model_id):  # noqa: ARG003
            return cls()

        def transcribe(self, audio, language=None):  # noqa: ARG002
            return {"text": "你好", "words": [{"start": 0.0, "end": 1.0, "text": "你好"}]}

    fake_module = types.SimpleNamespace(Qwen3ASRModel=FakeQwen3ASRModel)
    monkeypatch.setitem(sys.modules, "qwen_asr", fake_module)

    out = tmp_path / "transcript.json"
    try:
        cli.transcribe_to_file(
            tmp_path / "episode.wav",
            out,
            provider_name="qwen3-asr-local",
        )
    except Exception as exc:
        assert "shape" in str(exc).lower() or "list" in str(exc).lower()
    else:
        raise AssertionError("expected ASRProviderError on unexpected qwen-asr response shape")
    assert not out.exists()


def test_qwen3_asr_provider_rejects_module_without_qwen3asrmodel(tmp_path, monkeypatch):
    """If a future qwen_asr release renames its entry point, surface a clear
    error instead of an AttributeError traceback."""
    import sys
    import types

    monkeypatch.setitem(sys.modules, "qwen_asr", types.SimpleNamespace())

    out = tmp_path / "transcript.json"
    try:
        cli.transcribe_to_file(
            tmp_path / "episode.wav",
            out,
            provider_name="qwen3-asr-local",
        )
    except Exception as exc:
        msg = str(exc).lower()
        assert "qwen3asrmodel" in msg or "qwen-asr" in msg
    else:
        raise AssertionError("expected ASRProviderError when qwen_asr lacks Qwen3ASRModel class")
    assert not out.exists()


def test_provider_names_include_optional_whisper_cpp():
    from podcast_auto_editor.asr import provider_names

    assert "whisper-cpp-local" in provider_names()


def test_whisper_cpp_provider_requires_binary_and_model_without_writing(tmp_path):
    import sys

    out = tmp_path / "transcript.json"

    try:
        transcribe_to_file(tmp_path / "episode.wav", out, provider_name="whisper-cpp-local")
    except ASRProviderError as exc:
        assert "whisper-cpp-local requires --binary" in str(exc)
    else:
        raise AssertionError("expected missing binary error")

    try:
        transcribe_to_file(
            tmp_path / "episode.wav",
            out,
            provider_name="whisper-cpp-local",
            binary=str(Path(sys.executable)),
        )
    except ASRProviderError as exc:
        assert "whisper-cpp-local requires --model-path" in str(exc)
    else:
        raise AssertionError("expected missing model error")

    assert not out.exists()


def test_whisper_cpp_provider_parses_json_segments(tmp_path):
    binary = tmp_path / "fake-whisper-cli.py"
    model = tmp_path / "ggml-large-v3-q5_0.bin"
    output = tmp_path / "transcript.json"
    model.write_text("model")
    binary.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys\n"
        "prefix = sys.argv[sys.argv.index('-of') + 1]\n"
        "pathlib.Path(prefix + '.json').write_text(json.dumps({\n"
        "    'transcription': [\n"
        "        {'offsets': {'from': 250, 'to': 1500}, 'text': ' hello world '},\n"
        "    ]\n"
        "}))\n"
    )
    binary.chmod(0o755)

    transcribe_to_file(
        tmp_path / "episode.wav",
        output,
        provider_name="whisper-cpp-local",
        binary=str(binary),
        model_path=str(model),
        language="en",
        threads=4,
    )

    data = json.loads(output.read_text())
    assert data["provider"] == "whisper-cpp-local"
    assert data["segments"] == [{"start": 0.25, "end": 1.5, "text": "hello world"}]


def test_whisper_cpp_provider_rejects_invalid_json_without_writing(tmp_path):
    binary = tmp_path / "fake-whisper-cli.py"
    model = tmp_path / "ggml-large-v3-q5_0.bin"
    output = tmp_path / "transcript.json"
    model.write_text("model")
    binary.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "prefix = sys.argv[sys.argv.index('-of') + 1]\n"
        "pathlib.Path(prefix + '.json').write_text('{not json')\n"
    )
    binary.chmod(0o755)

    try:
        transcribe_to_file(
            tmp_path / "episode.wav",
            output,
            provider_name="whisper-cpp-local",
            binary=str(binary),
            model_path=str(model),
        )
    except ASRProviderError as exc:
        assert "invalid whisper.cpp JSON output" in str(exc)
    else:
        raise AssertionError("expected invalid JSON error")

    assert not output.exists()


def test_transcribe_cli_passes_whisper_cpp_options(tmp_path, monkeypatch):
    captured = {}

    def fake_transcribe_to_file(input_path, out_path, provider_name="stub", **options):
        captured["input_path"] = str(input_path)
        captured["out_path"] = str(out_path)
        captured["provider_name"] = provider_name
        captured["options"] = options
        Path(out_path).write_text(json.dumps({"schema_version": "transcript.v1", "segments": [{"start": 0.0, "end": 1.0, "text": "ok"}]}))
        return Path(out_path)

    monkeypatch.setattr(cli, "transcribe_to_file", fake_transcribe_to_file)
    out = tmp_path / "transcript.json"

    assert main([
        "transcribe",
        str(tmp_path / "episode.wav"),
        "--provider",
        "whisper-cpp-local",
        "--binary",
        "/opt/whisper.cpp/build/bin/whisper-cli",
        "--model-path",
        "/models/ggml-large-v3-q5_0.bin",
        "--language",
        "zh",
        "--threads",
        "8",
        "--out",
        str(out),
    ]) == 0

    assert captured["provider_name"] == "whisper-cpp-local"
    assert captured["options"] == {
        "binary": "/opt/whisper.cpp/build/bin/whisper-cli",
        "model_path": "/models/ggml-large-v3-q5_0.bin",
        "language": "zh",
        "threads": 8,
    }
