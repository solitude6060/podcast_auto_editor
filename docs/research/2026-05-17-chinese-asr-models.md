# Chinese Podcast ASR / Alignment / VAD Model Research (2026-05-17)

Scope: 60-120 分鐘中文 podcast、本機 GPU（RTX 4090 24GB / Apple Silicon 16GB+）、不能上傳第三方、需要 word-level timestamp 給後製剪輯。

Triggered by user feedback (2026-05-17) citing a Chinese OSS contributor's recommendations: Qwen3-ASR for transcription, Lattifai for alignment, lifeiteng for VAD. This document captures the verification of those three claims plus the alternatives evaluated.

All URLs, licenses, and benchmarks below are sourced; where evidence is missing the entry is marked "未驗證".

---

## 1. ASR (Speech-to-text)

### 1.1 Qwen3-ASR (recommended primary)
- GitHub: https://github.com/QwenLM/Qwen3-ASR
- HF: https://huggingface.co/Qwen/Qwen3-ASR-0.6B and https://huggingface.co/Qwen/Qwen3-ASR-1.7B
- License: Apache-2.0 (both model + code)
- Released: 2026-01-29
- Chinese WER (from model card):
  - WenetSpeech (net | meeting): 1.7B = **4.97 | 5.88**; Whisper-large-v3 baseline = 9.86 | 19.11
  - AISHELL-2: 1.7B = **2.71**; Whisper-large-v3 = 5.06
  - SpeechIO: 1.7B = **2.88**
  - Fleurs-zh: 1.7B = **2.41**
  - Taiwan Mandarin CV-zh-tw: 1.7B = **3.77** (significant for our 繁中 audience)
  - Cantonese Fleurs-yue: 1.7B = **3.98**
  - 22 Chinese dialects (avg): 1.7B = 15.94
- Local install: `pip install -U qwen-asr` (transformers) or `qwen-asr[vllm]` (vLLM faster); official Docker `qwenllm/qwen3-asr:latest`. Apple Silicon MLX port: https://github.com/moona3k/mlx-qwen3-asr
- Max chunk: **20 minutes native single-segment** (README); chunk + concat for longer
- Memory: 1.7B bf16 + FlashAttention-2 fits on 24GB RTX 4090; 0.6B comfortable on 16GB Apple Silicon
- API required: **No** (local weights). Note: https://github.com/QwenLM/Qwen3-ASR-Toolkit is a separate package that wraps DashScope cloud — do not confuse
- Caveats: 1.7B larger than whisper-large-v3 (vLLM recommended for speed); 20-min chunking is the caller's responsibility for full episodes

### 1.2 Fun-ASR-Nano-2512 (2025-12, by FunAudioLLM/DAMO)
- GitHub: https://github.com/modelscope/FunASR (toolkit MIT)
- HF: https://huggingface.co/FunAudioLLM/Fun-ASR-Nano-2512 and https://huggingface.co/FunAudioLLM/Fun-ASR-MLT-Nano-2512
- License: toolkit MIT; weights = "FunASR Model License Agreement" (commercial OK, must keep attribution, anti-disparagement clause)
- Released: 2025-12
- Chinese WER:
  - AISHELL-1: **1.80** (beats Qwen3-ASR-1.7B's not-listed number)
  - AISHELL-2: **2.75** (beats Qwen3-ASR-1.7B's 2.71? — comparable)
  - WenetSpeech net | meeting: **6.01 | 6.60**
- Model size: 800M (Nano); 7.7B flagship not publicly released
- Max chunk: **30 seconds** single-segment (needs VAD pipeline)
- 26 dialects supported; 繁中/Taiwan Mandarin not separately measured
- Memory: trivial; runs on small GPUs
- Caveats: 30s segment hard limit → mandatory VAD chunking; license should be reviewed by org legal before commercial use

### 1.3 SenseVoice Small
- GitHub: https://github.com/FunAudioLLM/SenseVoice
- HF: https://huggingface.co/FunAudioLLM/SenseVoiceSmall
- License: FunAudioLLM model license (similar to Fun-ASR-Nano)
- Chinese WER: claimed beats whisper but no single benchmark table in model card (minus)
- Local: yes, CPU 70ms/10s (15× faster than whisper-large)
- Max chunk: 30s direct; built-in VAD for longer
- Model size: ~200MB
- Verdict: 已被 Fun-ASR-Nano-2512 取代 (same team, newer)

### 1.4 OmniSenseVoice (the project user actually meant by "lifeiteng/Omni…")
- GitHub: https://github.com/lifeiteng/OmniSenseVoice
- License: Apache-2.0
- **It is ASR, NOT VAD.** SenseVoice ONNX-accelerated + word-timestamp port.
- Performance: L4 GPU + ONNX RTF=0.0027 (50× speedup), LibriTTS dev-clean WER = 5.60%
- Caveats: upstream SenseVoice 30s segment limit; no Chinese podcast benchmark; no separate VAD

### 1.5 Paraformer-large / paraformer-zh
- GitHub: https://github.com/modelscope/FunASR
- HF: https://huggingface.co/funasr/Paraformer-large, https://huggingface.co/funasr/paraformer-zh
- License: toolkit MIT, model = FunASR Model License
- C/C++ port: https://github.com/lovemefan/paraformer.cpp (whisper.cpp-style)
- Verdict: 已被 SenseVoice / Fun-ASR-Nano 取代; only relevant if needing paraformer.cpp pure-CPU deployment

### 1.6 Belle-whisper-large-v3-zh (whisper fine-tune for Chinese)
- GitHub: https://github.com/LianjiaTech/BELLE, https://github.com/shuaijiang/Whisper-Finetune
- HF: https://huggingface.co/BELLE-2/Belle-whisper-large-v3-zh
- License: Apache-2.0
- Chinese CER vs vanilla whisper-large-v3:
  - AISHELL-1: 8.085 → **2.781** (-65.6%)
  - AISHELL-2: 5.475 → **3.786** (-30.8%)
  - WenetSpeech net: 11.72 → **8.865** (-24.3%)
  - WenetSpeech meeting: 20.15 → **11.246** (-44.2%)
  - HKUST dev: 28.597 → **16.440** (-42.5%)
- Local: **completely compatible with faster-whisper / whisper.cpp** (just swap weights)
- Memory: same as whisper-large-v3 (~10GB FP16 / ~3GB Q5_K_M)
- Caveats: still loses to Qwen3-ASR-1.7B in absolute WER; only trained on simplified Chinese (繁中 not verified); whisper hallucination behaviour unchanged
- Value: **lowest-friction upgrade** if keeping the faster-whisper / whisper.cpp pipeline

### 1.7 Baseline: faster-whisper / whisper.cpp + whisper-large-v3 / turbo
- Currently in our project. Vanilla whisper-large-v3 hallucinates on Chinese WenetSpeech meeting (WER 19.11%). `turbo` is **worse** for Chinese (only 4 decoder layers; HF discussion #2363 confirms low-resource-language degradation). 2026 verdict: superseded for Chinese.

---

## 2. Forced Alignment (word-level timestamps)

### 2.1 Qwen/Qwen3-ForcedAligner-0.6B
- HF: https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B
- License: Apache-2.0
- **Model card documented limit**: 5 minutes per call ("supports timestamp prediction for arbitrary units within up to 5 minutes of speech in 11 languages")
- **Reported practical accuracy degradation**: the Chinese contributor who recommended Lattifai reports their testing shows the timeline going wrong ("時間軸就混亂不堪") after ~180 seconds. The two facts are not contradictory: the 5-minute number is a documented support limit; the 180-second number is the empirical accuracy cliff in real-world Chinese audio that the model card does not surface
- 11 languages: Chinese, English, Cantonese, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish
- Local: runs locally via `Qwen3ForcedAligner.from_pretrained(...)`; no cloud required (DashScope is the optional faster path for ASR, not the aligner)
- Word/character-level alignment
- Released: ~Jan 2026 (per arxiv id 2601.21337)
- Chunking guidance: **none in the model card**
- Verdict: **Not viable for podcast (60-120 min) use case.** The documented 5-min cap is short enough that any podcast needs chunking, and the empirical 180s accuracy cliff means even chunking would degrade. Treat as a sentence-level tool, not an episode-level tool.

### 2.2 Lattifai Lattice-1 (the user's primary recommendation — verify carefully)
- SDK GitHub: https://github.com/lattifai/lattifai-python (MIT, 184 stars, active)
- HF model: https://huggingface.co/LattifAI/Lattice-1 (Apache-2.0; supports 英/中/德; Lattice-1-Alpha is English-only)
- Architecture verification (read src/lattifai/alignment/lattice1_worker.py):
  - Model is ONNX, runs **completely local** (onnxruntime + CUDA/MPS/CoreML)
  - Audio does not leave the machine during alignment
  - Built-in 60s chunking + concat; native long-audio support
- API key reality (important — README vs code contradict):
  - README says "LattifAI API Key (Required)", `.env.example` wants `LATTIFAI_API_KEY=lf_xxxx`
  - `ClientConfig.__post_init__` actually auto-resolves; no hard raise if missing
  - Model itself (ONNX) is pure local inference — no phone-home
  - But `SyncAPIClient` (from `lattifai_core`) is still on the init path for quota / usage tracking / X-Device-Auth HMAC
  - **Conclusion:** model inference doesn't need lattifai.com, but the SDK by default tries to auth. Free `lai auth trial` gives 120 min credit. For full air-gap, can load https://huggingface.co/LattifAI/Lattice-1 ONNX directly via onnxruntime, but unofficial (need to hack tokenizer/decoder)
- Long audio: streaming mode claims 20-hour support (5-min chunks); 4-hour podcast is the sweet spot
- Chinese: Lattice-1 model card lists Chinese; 繁/簡 not separated; **no public alignment-accuracy benchmark numbers** (minus)
- Caveats:
  1. SDK defaults to API key + usage telemetry (model is local but client phones home) — air-gap requires bypassing SDK
  2. Chinese alignment accuracy not published — must validate ourselves
  3. Commercial company; long-term OSS commitment uncertain (vs ctc-forced-aligner / MFA which are community-led)
  4. Depends on `lattifai-core` / `lattifai-auth` sister packages, partly hosted on `https://lattifai.github.io/pypi/simple/` extra index

### 2.3 WhisperX
- GitHub: https://github.com/m-bain/whisperX (21.9k stars, v3.8.5 = 2026-04, active)
- License: BSD-2-Clause
- Chinese alignment: torchaudio default only {en,fr,de,es,it}; Chinese requires `DEFAULT_ALIGN_MODELS_HF` with wav2vec2 Chinese phoneme model (community uses `jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn`)
- Local; <8GB GPU
- Caveats: Chinese phoneme model unofficial, quality mixed; long audio via VAD + batched inference; Chinese alignment accuracy below pure-Chinese-specialized model
- Strength: best integrated ASR + align + diarization pipeline in the OSS ecosystem; most widely deployed

### 2.4 ctc-forced-aligner (MahmoudAshraf97)
- GitHub: https://github.com/MahmoudAshraf97/ctc-forced-aligner
- License: BSD (code); **default model `MahmoudAshraf/mms-300m-1130-forced-aligner` is CC-BY-NC 4.0** → commercial use requires non-NC alternative
- MMS-300M covers 1130+ languages incl. Chinese
- Memory: claimed 5× less than torchaudio; 30s window default, handles long audio
- Caveats: default model non-commercial; Chinese accuracy not published

### 2.5 Montreal Forced Aligner (MFA) 3.x
- GitHub: https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner, models at https://github.com/MontrealCorpusTools/mfa-models
- License: MIT
- Chinese models: Standard Mandarin, Beijing Mandarin, **Taiwan Mandarin** (significant for our audience) + `mandarin_mfa` acoustic model
- Architecture: Kaldi GMM-HMM; **no GPU acceleration** — pure CPU
- Caveats: CPU-only → 120-min podcast is slow; needs pronunciation dictionary + pre-segmented text; academic workflow (strict folder structure); for pure-Han input requires syllable-level annotation
- Strength: academic gold standard; Taiwan Mandarin has dedicated dictionary

---

## 3. VAD (Voice Activity Detection)

### 3.1 silero-vad
- GitHub: https://github.com/snakers4/silero-vad
- License: **MIT** (no telemetry, no key, no registration, no expiry)
- Version: v6.2 (2025-12-10); v6 (2025-08-25) supports 6000+ languages
- Performance: JIT model <1ms CPU per 30ms+ chunk; v6 0.85-0.95 accuracy across datasets; 0.71-0.87 on noisy datasets
- Chinese: training data includes Chinese (discussion #40); strong on Mandarin podcast in practice
- Integration: faster-whisper, WhisperX, pipecat, all major pipelines have silero integration
- **Clear winner in VAD category**: MIT, zero friction, Chinese OK, ubiquitous integration

### 3.2 pyannote VAD (pyannote-audio segmentation-3.0)
- GitHub: https://github.com/pyannote/pyannote-audio
- HF: https://huggingface.co/pyannote/segmentation-3.0, https://huggingface.co/pyannote/voice-activity-detection
- License: MIT but **gated HF repo** — requires HF token + form (Company / Website). Friction for individuals; acceptable for orgs
- Chinese training: segmentation-3.0 trained on AISHELL + AliMeeting (two Chinese datasets) → outperforms silero v5 on Chinese (v6 has narrowed the gap)
- Strength: shares model with pyannote speaker-diarization-3.1 / community-1 → reuse backbone if doing diarization with pyannote
- Caveats: gated (HF login + form); PyTorch inference heavier than silero JIT

### 3.3 WebRTC VAD (py-webrtcvad)
- GitHub: https://github.com/wiseman/py-webrtcvad
- License: BSD (WebRTC upstream)
- Architecture: traditional GMM; only 10/20/30ms frame
- 2026 verdict: silero v6 strictly better (Picovoice 2025 comparison: Cobra > Silero > WebRTC AUC). Only use if needing zero-dependency / no-ML / pure-CPU

### 3.4 lifeiteng/Omni... (what the user said)
- **Reality**: https://github.com/lifeiteng/OmniSenseVoice is **ASR** (SenseVoice acceleration), NOT VAD. The user's "best-accuracy VAD" claim is **unverified**. lifeiteng also has https://github.com/lifeiteng/Aligner-SUPERB (alignment benchmark), also not VAD. No dedicated VAD repo found under `lifeiteng` account.

---

## 4. Speaker Diarization (for context — user mentioned Lattifai solving diarization + naming)

- **pyannote-audio 3.x** + https://huggingface.co/pyannote/speaker-diarization-3.1: MIT, gated; current OSS industry standard
- **pyannote/speaker-diarization-community-1**: CC-BY-4.0 (referenced in WhisperX README)
- **NVIDIA NeMo diarization**: what Lattifai integrates with
- **Lattifai diarization + naming**: uses LLM to extract speaker names from YouTube metadata (see `client.py`'s `_build_speaker_context` for `host / guest / 嘉宾 / 主持` keyword handling) — this is LLM post-processing layer; the model under the hood is still pyannote / NeMo

---

## 5. Recommendations (Chinese podcast 60-120 min)

| Position | First choice | Why | Integration difficulty | Backup |
|---|---|---|---|---|
| **ASR** | **Qwen3-ASR-1.7B** | Apache-2.0, native 20-min chunks, Chinese WER trounces whisper-large-v3 (WenetSpeech meeting 5.88 vs 19.11), Taiwan CV WER 3.77, 22 dialects, vLLM fast, Docker one-line | **Medium**: need vLLM/transformers backend; long-audio chunking + concat is the caller's job; faster-whisper call layer must be rewritten | (a) **Fun-ASR-Nano-2512** lower AISHELL, 800M model, works on 16GB Apple Silicon, but 30s segment limit needs VAD chunking. (b) **Belle-whisper-large-v3-zh** drop-in weights replacement → no pipeline change, immediate -24~65% Chinese CER |
| **Forced Alignment** | **WhisperX + Chinese wav2vec2 phoneme model** OR **Lattifai Lattice-1 (local ONNX mode)** | WhisperX: BSD-2, local, most mature ecosystem. Lattifai: native long-audio + claimed Chinese accuracy, but SDK has API-key + usage-tracking layer to watch out for | WhisperX **Low** (OSS standard); Lattifai **Medium** (SDK binds auth; full air-gap requires self-load via onnxruntime) | (a) **ctc-forced-aligner** with non-NC model. (b) **MFA mandarin/taiwan** CPU-only but most complete 繁中 dictionary. **Avoid Qwen3-ForcedAligner-0.6B** (5-min hard cap is unsuitable for podcast) |
| **VAD** | **silero-vad v6** | MIT, zero friction, Chinese OK, every pipeline already integrated, fast on CPU | **Low**: faster-whisper / WhisperX have it as a one-line flag | **pyannote segmentation-3.0** if also using pyannote diarization (shares backbone) — note gated |
| **Diarization** | **pyannote/speaker-diarization-3.1** | OSS standard, MIT, Chinese training datasets (AISHELL/AliMeeting) included; gated process acceptable | **Low** (existing pipeline already uses it) | **community-1** (CC-BY-4.0, less friction); NeMo (NVIDIA NGC) |

### 5.1 Two upgrade paths

- **Aggressive** (swap ASR + alignment together): Qwen3-ASR-1.7B + WhisperX Chinese wav2vec2 + silero-vad + pyannote 3.1. Expected Chinese WER from ~20% (whisper meeting) → ~6%. Engineering work ~ 1-2 weeks
- **Conservative** (minimum diff): Belle-whisper-large-v3-zh (drop-in weights swap) + existing faster-whisper + WhisperX align + silero VAD + pyannote. Expected CER from ~20% → ~11%. Engineering work ~ 1-2 days
- **Don't touch**: silero-vad and pyannote diarization-3.1 — both remain the 2026 standard answer

### 5.2 Response to the three user (Chinese contributor) recommendations

1. **"Drop whisper, use Qwen3-ASR"** → **Agree.** Chinese podcast evidence overwhelming. Don't forget the 20-min per-segment cap; long podcasts still need chunking.
2. **"Whisper alignment inaccurate, use Lattifai"** → **Partial agree / partial reservation.** Lattice-1 model itself is Apache + ONNX local, fine. But SDK by default binds API key + usage telemetry (even though audio doesn't upload) — for strict "nothing leaves my box" cases, bypass SDK or use WhisperX. **Qwen3-ForcedAligner-0.6B**: drop it for podcast use — model card documents 5-min support, but the empirical 180s accuracy cliff the contributor reported is the more honest signal of where it actually breaks. Either way it cannot reasonably handle a 60-120 min episode.
3. **"Use lifeiteng's OmniVAD"** → **Doesn't exist.** User mis-remembered the name. `lifeiteng/OmniSenseVoice` is ASR not VAD, and has no Chinese podcast benchmark. Keep silero-vad.

---

## 6. Recommended next steps

This research informs which Stage 1 PR-C2 (real diarization integration) and a possible Stage 2 (multi-track + real-ASR) should adopt. Suggested follow-up PRs (no commitment yet):

1. **PR-X1 (medium-risk, high-reward)** — Add Qwen3-ASR-1.7B as a `qwen3-asr` provider in `podcast_auto_editor/asr.py`, alongside existing `whisper.cpp` / `faster-whisper` providers. Chunk long audio at 20-min boundaries.
2. **PR-X2 (low-risk)** — Add `belle-whisper-large-v3-zh` as a model choice for the existing `faster-whisper` provider; lowest-friction Chinese-language improvement.
3. **PR-X3 (PR-C2 follow-up)** — Real pyannote/speaker-diarization-3.1 integration (with HF_TOKEN flow; user supplies token via env).
4. **PR-X4 (optional)** — WhisperX + Chinese wav2vec2 alignment provider as a `--with-word-timestamps` flag on `transcribe`.

Avoid until validated:
- Lattifai SDK integration (until air-gap mode is verified or accepted with usage-telemetry caveat documented).
- Qwen3-ForcedAligner-0.6B (5-min cap kills podcast use case).
- Switching VAD from silero (current/planned) — no upgrade path beats MIT + zero friction yet.

---

## 7. Primary sources

All sources listed inline in §§1-3. Cross-referenced 2026-05-17 via web search and GitHub / Hugging Face fetch. Lattifai SDK code inspected directly to verify ONNX local-inference claim.
