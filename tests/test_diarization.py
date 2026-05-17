import json
from pathlib import Path

import pytest

from podcast_auto_editor.diarization import (
    SCHEMA_VERSION,
    DiarizationError,
    DiarizationProviderError,
    MockDiarizationProvider,
    PyannoteDiarizationProvider,
    diarize_to_file,
    normalize_speaker_segments,
)


def _write_config(tmp_path: Path) -> tuple[Path, Path]:
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt fake-audio")
    config_path = tmp_path / "diar.json"
    config_path.write_text(json.dumps({
        "segments": [
            {"start": 0.0, "end": 5.0, "speaker_id": "spk0", "confidence": 0.95},
            {"start": 5.0, "end": 10.0, "speaker_id": "spk1", "confidence": 0.92},
        ]
    }))
    return audio, config_path


def test_mock_diarization_returns_configured_segments(tmp_path):
    audio, config_path = _write_config(tmp_path)

    provider = MockDiarizationProvider(config_path=config_path)
    segments = provider.diarize(audio)

    assert len(segments) == 2
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] == 5.0
    assert segments[0]["speaker_id"] == "spk0"
    assert segments[0]["confidence"] == 0.95
    assert segments[1]["speaker_id"] == "spk1"


def test_mock_diarization_returns_empty_list_without_config(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    provider = MockDiarizationProvider()
    assert provider.diarize(audio) == []


def test_normalize_speaker_segments_validates_required_fields():
    valid = normalize_speaker_segments([
        {"start": 0.0, "end": 1.0, "speaker_id": "spk0", "confidence": 0.8}
    ])
    assert valid[0]["speaker_id"] == "spk0"

    with pytest.raises(DiarizationError, match="speaker_id"):
        normalize_speaker_segments([{"start": 0.0, "end": 1.0, "confidence": 0.8}])

    with pytest.raises(DiarizationError, match="start"):
        normalize_speaker_segments([{"end": 1.0, "speaker_id": "spk0", "confidence": 0.8}])

    with pytest.raises(DiarizationError, match="end"):
        normalize_speaker_segments([{"start": 1.0, "end": 0.5, "speaker_id": "spk0", "confidence": 0.8}])


def test_normalize_speaker_segments_rejects_negative_start():
    """Triple-review (Gemini LOW + MiniMax CRITICAL + Codex MEDIUM):
    start < 0 must be rejected, mirroring transcript.py:59."""
    with pytest.raises(DiarizationError, match="start"):
        normalize_speaker_segments([{"start": -0.5, "end": 1.0, "speaker_id": "spk0"}])


def test_normalize_speaker_segments_rejects_non_finite_timestamps():
    """Triple-review (Codex MEDIUM): NaN / inf must not slip through `float(value)`."""
    nan = float("nan")
    inf = float("inf")
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": nan, "end": 1.0, "speaker_id": "spk0"}])
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": 0.0, "end": inf, "speaker_id": "spk0"}])


def test_normalize_speaker_segments_rejects_boolean_timestamps():
    """Triple-review (Codex MEDIUM): bool is a subtype of int; the validator
    must reject it explicitly so `True` (=1.0) and `False` (=0.0) do not
    silently map to seconds."""
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": True, "end": 1.0, "speaker_id": "spk0"}])
    with pytest.raises(DiarizationError):
        normalize_speaker_segments([{"start": 0.0, "end": False, "speaker_id": "spk0"}])


def test_normalize_speaker_segments_clamps_confidence():
    out = normalize_speaker_segments([
        {"start": 0.0, "end": 1.0, "speaker_id": "spk0", "confidence": 1.5},
        {"start": 1.0, "end": 2.0, "speaker_id": "spk1", "confidence": -0.2},
    ])
    assert out[0]["confidence"] == 1.0
    assert out[1]["confidence"] == 0.0


def test_diarize_to_file_writes_canonical_schema(tmp_path):
    audio, config_path = _write_config(tmp_path)
    out = tmp_path / "speaker_segments.v1.json"

    result = diarize_to_file(audio, out, provider="mock", config_path=config_path)

    assert result == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert len(data["segments"]) == 2
    assert data["segments"][0]["speaker_id"] == "spk0"


def test_diarize_to_file_writes_empty_segments_artefact(tmp_path):
    """Triple-review (MiniMax MEDIUM): the empty-segments path through
    `diarize_to_file` (no --config given) must produce a valid artefact
    with `segments: []`, not an error or a missing file."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "out.json"

    result = diarize_to_file(audio, out, provider="mock")

    assert result == out
    data = json.loads(out.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["segments"] == []


def test_mock_provider_wraps_invalid_json_as_diarization_error(tmp_path):
    """Triple-review (Gemini MEDIUM): malformed mock config JSON must
    surface as a clean DiarizationError so the CLI handler can convert
    it to a non-zero exit, not bubble up as a JSONDecodeError traceback."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    config = tmp_path / "bad.json"
    config.write_text("{not valid json")

    provider = MockDiarizationProvider(config_path=config)
    with pytest.raises(DiarizationError):
        provider.diarize(audio)


def test_mock_provider_wraps_missing_config_as_diarization_error(tmp_path):
    """Triple-review (Gemini MEDIUM): a missing config file must surface as
    a DiarizationError, not a raw FileNotFoundError."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    missing = tmp_path / "does-not-exist.json"

    provider = MockDiarizationProvider(config_path=missing)
    with pytest.raises(DiarizationError):
        provider.diarize(audio)


def test_diarize_to_file_rejects_unknown_provider(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "out.json"
    with pytest.raises(DiarizationError, match="unknown provider"):
        diarize_to_file(audio, out, provider="not-a-real-provider")


def test_pyannote_provider_raises_clear_error_when_called(tmp_path):
    """Until pyannote.audio is installed, calling the adapter must raise a
    clear DiarizationProviderError so users know how to proceed."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationProviderError) as exc_info:
        provider.diarize(audio)
    msg = str(exc_info.value).lower()
    assert "pyannote" in msg or "deferred" in msg, msg


def test_pyannote_provider_via_diarize_to_file_raises_clear_error(tmp_path):
    """End-to-end: CLI-equivalent flow via diarize_to_file must surface the
    pyannote provider error, not silently write an empty artefact."""
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "out.json"
    with pytest.raises(DiarizationProviderError):
        diarize_to_file(audio, out, provider="pyannote")
    assert not out.exists()


# ---------------------------------------------------------------------------
# PR-C2: pyannote real-integration tests (no actual pyannote install needed)
# ---------------------------------------------------------------------------


def _make_fake_turn(start: float, end: float):
    """Return a minimal object that mimics a pyannote Segment."""

    class _FakeTurn:
        def __init__(self, s, e):
            self.start = s
            self.end = e

    return _FakeTurn(start, end)


def _make_fake_annotation(turns):
    """Return a fake pyannote Annotation whose itertracks(yield_label=True)
    yields (turn, track, label) triples matching the given list of
    (start, end, speaker_id) tuples."""

    class _FakeAnnotation:
        def __init__(self, turn_list):
            self._turns = turn_list

        def itertracks(self, yield_label=False):
            for start, end, label in self._turns:
                yield _make_fake_turn(start, end), None, label

    return _FakeAnnotation(turns)


def _fake_pyannote_module(pipeline_instance):
    """Build a minimal fake pyannote.audio module whose Pipeline.from_pretrained
    returns the given pipeline_instance."""
    import types

    mod = types.ModuleType("pyannote.audio")

    class _FakePipeline:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            return pipeline_instance

    mod.Pipeline = _FakePipeline
    return mod


def test_pyannote_provider_raises_clear_error_when_dependency_missing(tmp_path, monkeypatch):
    """When pyannote.audio is not importable, provider must raise
    DiarizationProviderError naming the diarize-pyannote install
    instructions and must not include any token value in the message."""
    import sys

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")

    # Ensure pyannote.audio is not importable
    monkeypatch.setitem(sys.modules, "pyannote", None)
    monkeypatch.setitem(sys.modules, "pyannote.audio", None)

    # Set a sentinel token value that must not appear in error messages
    monkeypatch.setenv("HF_TOKEN", "pae_test_sentinel_xyz")

    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationProviderError) as exc_info:
        provider.diarize(audio)

    msg = str(exc_info.value)
    assert "diarize-pyannote" in msg, f"Expected 'diarize-pyannote' install hint in: {msg!r}"
    assert "pae_test_sentinel_xyz" not in msg, f"Token sentinel leaked into error: {msg!r}"


def test_pyannote_provider_raises_clear_error_when_hf_token_missing(tmp_path, monkeypatch):
    """When pyannote.audio is importable but HF_TOKEN is absent and no
    local token file is usable, provider must raise DiarizationProviderError
    directing the user to set HF_TOKEN."""
    import sys
    import types

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")

    monkeypatch.delenv("HF_TOKEN", raising=False)

    # Build a fake pyannote.audio whose Pipeline.from_pretrained raises
    # a EnvironmentError/OSError when no token is available.
    class _NoTokenPipeline:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            raise OSError(
                "401 Client Error: Unauthorized. "
                "Make sure you have access to pyannote/speaker-diarization-3.1 "
                "and that your token is valid."
            )

    fake_mod = types.ModuleType("pyannote.audio")
    fake_mod.Pipeline = _NoTokenPipeline

    monkeypatch.setitem(sys.modules, "pyannote.audio", fake_mod)
    # Also patch the parent so `import pyannote.audio` resolves
    parent = types.ModuleType("pyannote")
    parent.audio = fake_mod
    monkeypatch.setitem(sys.modules, "pyannote", parent)

    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationProviderError) as exc_info:
        provider.diarize(audio)

    msg = str(exc_info.value)
    assert "HF_TOKEN" in msg, f"Expected HF_TOKEN guidance in: {msg!r}"


def test_pyannote_provider_raises_clear_error_when_license_not_accepted(tmp_path, monkeypatch):
    """When Pipeline.from_pretrained raises a gated-repo/license error,
    provider must raise DiarizationProviderError pointing to the 3.1
    license URL and HF_TOKEN setup."""
    import sys
    import types

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")

    monkeypatch.setenv("HF_TOKEN", "pae_test_sentinel_xyz")

    class _GatedRepoPipeline:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            raise OSError(
                "403 Client Error: Forbidden. "
                "Access to model pyannote/speaker-diarization-3.1 is restricted. "
                "You must accept the model's license to access it."
            )

    fake_mod = types.ModuleType("pyannote.audio")
    fake_mod.Pipeline = _GatedRepoPipeline
    parent = types.ModuleType("pyannote")
    parent.audio = fake_mod
    monkeypatch.setitem(sys.modules, "pyannote.audio", fake_mod)
    monkeypatch.setitem(sys.modules, "pyannote", parent)

    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationProviderError) as exc_info:
        provider.diarize(audio)

    msg = str(exc_info.value)
    assert "huggingface.co/pyannote/speaker-diarization-3.1" in msg, (
        f"Expected license URL in: {msg!r}"
    )
    assert "HF_TOKEN" in msg, f"Expected HF_TOKEN guidance in: {msg!r}"
    assert "pae_test_sentinel_xyz" not in msg, f"Token sentinel leaked into error: {msg!r}"


def test_pyannote_provider_preserves_speaker_segments_schema_version(tmp_path, monkeypatch):
    """diarize_to_file with provider='pyannote' and a fake pipeline must
    write a JSON artefact with schema_version == 'speaker_segments.v1'."""
    import sys
    import types

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "speaker_segments.v1.json"

    annotation = _make_fake_annotation([
        (0.0, 2.0, "SPEAKER_00"),
        (2.0, 4.0, "SPEAKER_01"),
    ])

    class _OkPipeline:
        def __call__(self, path):
            return annotation

    fake_pipeline = _OkPipeline()

    class _OkPipelineClass:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            return fake_pipeline

    fake_mod = types.ModuleType("pyannote.audio")
    fake_mod.Pipeline = _OkPipelineClass
    parent = types.ModuleType("pyannote")
    parent.audio = fake_mod
    monkeypatch.setitem(sys.modules, "pyannote.audio", fake_mod)
    monkeypatch.setitem(sys.modules, "pyannote", parent)

    monkeypatch.setenv("HF_TOKEN", "pae_test_sentinel_xyz")

    result = diarize_to_file(audio, out, provider="pyannote")

    data = json.loads(result.read_text())
    assert data["schema_version"] == SCHEMA_VERSION
    assert "pae_test_sentinel_xyz" not in result.read_text()


def test_pyannote_provider_normalizes_output_start_before_end(tmp_path, monkeypatch):
    """Every segment returned via the pyannote provider must have numeric
    start, numeric end, and start < end."""
    import sys
    import types

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    out = tmp_path / "out.json"

    annotation = _make_fake_annotation([
        (0.5, 3.5, "SPEAKER_00"),
        (4.0, 7.2, "SPEAKER_01"),
    ])

    class _OkPipeline:
        def __call__(self, path):
            return annotation

    class _OkPipelineClass:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            return _OkPipeline()

    fake_mod = types.ModuleType("pyannote.audio")
    fake_mod.Pipeline = _OkPipelineClass
    parent = types.ModuleType("pyannote")
    parent.audio = fake_mod
    monkeypatch.setitem(sys.modules, "pyannote.audio", fake_mod)
    monkeypatch.setitem(sys.modules, "pyannote", parent)

    monkeypatch.setenv("HF_TOKEN", "tok")

    result = diarize_to_file(audio, out, provider="pyannote")
    data = json.loads(result.read_text())

    for seg in data["segments"]:
        assert isinstance(seg["start"], (int, float))
        assert isinstance(seg["end"], (int, float))
        assert seg["start"] < seg["end"]


def test_pyannote_provider_rejects_invalid_turn_as_diarization_error(tmp_path, monkeypatch):
    """A zero-length or negative pyannote turn must surface as DiarizationError
    (not DiarizationProviderError) because normalization raises it."""
    import sys
    import types

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")

    # zero-length turn: start == end
    annotation = _make_fake_annotation([(1.0, 1.0, "SPEAKER_00")])

    class _BadPipeline:
        def __call__(self, path):
            return annotation

    class _BadPipelineClass:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            return _BadPipeline()

    fake_mod = types.ModuleType("pyannote.audio")
    fake_mod.Pipeline = _BadPipelineClass
    parent = types.ModuleType("pyannote")
    parent.audio = fake_mod
    monkeypatch.setitem(sys.modules, "pyannote.audio", fake_mod)
    monkeypatch.setitem(sys.modules, "pyannote", parent)

    monkeypatch.setenv("HF_TOKEN", "tok")

    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationError) as exc_info:
        provider.diarize(audio)

    # Must be DiarizationError but NOT DiarizationProviderError subclass
    assert type(exc_info.value) is DiarizationError


def test_pyannote_provider_does_not_leak_hf_token_to_error_or_artifact(tmp_path, monkeypatch):
    """HF_TOKEN sentinel must not appear in exception text or JSON artifact,
    whether via failure path or success path."""
    import sys
    import types

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")
    SENTINEL = "pae_test_sentinel_xyz"
    monkeypatch.setenv("HF_TOKEN", SENTINEL)

    # --- Failure path: verify sentinel absent from exception ---
    class _FailPipelineClass:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            raise OSError("403 Forbidden: access restricted")

    fail_mod = types.ModuleType("pyannote.audio")
    fail_mod.Pipeline = _FailPipelineClass
    parent = types.ModuleType("pyannote")
    parent.audio = fail_mod
    monkeypatch.setitem(sys.modules, "pyannote.audio", fail_mod)
    monkeypatch.setitem(sys.modules, "pyannote", parent)

    provider = PyannoteDiarizationProvider()
    with pytest.raises(DiarizationProviderError) as exc_info:
        provider.diarize(audio)
    assert SENTINEL not in str(exc_info.value), (
        f"Token sentinel leaked into exception: {exc_info.value!r}"
    )

    # --- Success path: verify sentinel absent from artifact ---
    annotation = _make_fake_annotation([(0.0, 1.0, "SPEAKER_00")])

    class _OkPipeline:
        def __call__(self, path):
            return annotation

    class _OkPipelineClass:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            return _OkPipeline()

    ok_mod = types.ModuleType("pyannote.audio")
    ok_mod.Pipeline = _OkPipelineClass
    ok_parent = types.ModuleType("pyannote")
    ok_parent.audio = ok_mod
    monkeypatch.setitem(sys.modules, "pyannote.audio", ok_mod)
    monkeypatch.setitem(sys.modules, "pyannote", ok_parent)

    out = tmp_path / "out.json"
    # Reset provider (new instance so cached pipeline doesn't carry over)
    result = diarize_to_file(audio, out, provider="pyannote")
    artifact_text = result.read_text()
    assert SENTINEL not in artifact_text, (
        f"Token sentinel leaked into artifact: {artifact_text!r}"
    )


def test_pyannote_pipeline_is_constructed_once_per_provider_instance(tmp_path, monkeypatch):
    """Pipeline.from_pretrained must be called exactly once even when
    diarize() is called multiple times on the same provider instance."""
    import sys
    import types

    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF\x24WAVEfmt")

    annotation = _make_fake_annotation([(0.0, 1.0, "SPEAKER_00")])
    call_count = {"n": 0}

    class _CountingPipeline:
        def __call__(self, path):
            return annotation

    class _CountingPipelineClass:
        @staticmethod
        def from_pretrained(model_id, use_auth_token=None):
            call_count["n"] += 1
            return _CountingPipeline()

    fake_mod = types.ModuleType("pyannote.audio")
    fake_mod.Pipeline = _CountingPipelineClass
    parent = types.ModuleType("pyannote")
    parent.audio = fake_mod
    monkeypatch.setitem(sys.modules, "pyannote.audio", fake_mod)
    monkeypatch.setitem(sys.modules, "pyannote", parent)

    monkeypatch.setenv("HF_TOKEN", "tok")

    provider = PyannoteDiarizationProvider()
    provider.diarize(audio)
    provider.diarize(audio)

    assert call_count["n"] == 1, (
        f"Expected pipeline to be constructed once, got {call_count['n']}"
    )
