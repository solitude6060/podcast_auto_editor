# 變更紀錄

本文件記錄重要使用者可見變更。

## 尚未發布

### 新增
- 本機優先 podcast auto-editor MVP。
- 可回復 timeline、preview、diff、recovery artifacts。
- transcript、subtitle、chapter 輸出。
- export profiles：archive WAV、podcast stereo MP3、podcast mono MP3。
- review session：accept / reject / undo 決策可 replay。
- 靜態 HTML report。
- GitHub Actions 使用 uv 跑 pytest 與 compileall。
- 新增 `podcast_auto_editor ai draft`：以 timeline + transcript 產生 review-only `ai/ai-draft.v1.json`，並支援 `--dry-prompt` / `--dry-run` 離線輸出。
- `podcast_auto_editor explain --with-ai` 新增 AI 解釋欄位（含 `ai_explanation`），並支援 `--dry-prompt` 安全模式。
- `review serve` dashboard 整合 AI 草稿連結與 artifacts/context（API + HTML）資訊。
- 新增本機 AI stack e2e 腳本：`scripts/e2e-docker-ai-stack.sh` 及對應腳本測試。
- `podcast-auto-editor recipe export/apply`：把整個 run 目錄打包成可攜帶的 `recipe.v1.json`，可在同一份原始音檔上重放。Apply 時會驗證來源音檔 sha256，要繞過驗證請加 `--allow-media-drift`。recipe 內含 accepted timeline、config 快照、AI draft（如有），下游工具與協作者可以重現一模一樣的剪輯結果。
- 新增 ASR provider `qwen3-asr-local`，對應 [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)（Apache-2.0）。lazy-import `qwen-asr`，base install 不變重。沒裝 dep 或 dep API 跟預期不一樣時拋清楚的 `ASRProviderError`。長音檔（>20 分鐘）切片是 caller 責任，模型卡明訂。
- 中文 ASR drop-in：`faster-whisper-local --model BELLE-2/Belle-whisper-large-v3-zh`（Apache-2.0）。對比 vanilla `whisper-large-v3` 的 CER 在 AISHELL / WenetSpeech / HKUST 上降 -24~-66%。新增 regression test 確認 HuggingFace 模型 id 會 unchanged 傳給底層 WhisperModel。中文 ASR 全景見 `docs/research/2026-05-17-chinese-asr-models.md`。
- 新增 `podcast-auto-editor quickstart [--out <dir>] [--episode-id demo]`：一鍵 demo — 產生 demo fixtures、跑 pipeline 對著合成靜音範例、印出產生的 run 目錄跟建議的後續指令（`report` / `review serve`）。沒裝 ffmpeg 會 fail-fast 並提示。
- 新增 `scripts/install.sh`：Linux + uv 安裝腳本。冪等（跑兩次也沒事）；`uv` 不在 PATH 時 fail 並指向 uv 官方安裝文件；沒有 `ffmpeg` 時跳過 demo fixture 產生。macOS / WSL 路徑只在 README 文件記但尚未驗證。
- 新增 operation type `backchannel_cut`：對應短短的附和詞（"right"、"mhm"、"對對對"）。render 安全規則跟 `speech_cut` 一樣 — 永遠 proposed、不會 auto-accept、要 manual review + preview/diff/recovery artefacts。`detect_backchannel_candidates(transcript_segments, speaker_aggression=...)` 產生這類操作；`detect_speech_cleanup_candidates` 也新增同樣的 `speaker_aggression={"spk0": "off"}` 參數，可以讓主持人的附和詞風格保留，只剪掉來賓的填詞。
- `ai draft --speaker-segments speaker_segments.v1.json --speaker-label spk0=Host --speaker-label spk1=Guest`：如果有 speaker_segments，AI draft prompt 會帶上 `Speakers:` 區塊，讓 LLM 把章節歸給特定講者。產生的 chapters 會帶選擇性的 `speaker_id` 欄位（LLM 沒歸時為 null）。向後相容：沒給 speaker_segments 的舊 run，prompt 跟輸出維持原樣。
- 新增 `podcast-auto-editor diarize INPUT --provider mock|pyannote --out speaker_segments.v1.json --config X.json`：產生 `speaker_segments.v1.json`，給後續的 per-speaker AI 草稿引述、per-speaker filler 偵測使用。`mock` provider 讀 JSON config 後直接返回對應 segments，完全離線（不上網、不需要 HuggingFace token）。`pyannote` adapter 已經佈線完成，目前一律拋 `DiarizationProviderError`，訊息會區分「dependency missing（沒裝）」跟「integration deferred 到 PR-C2（裝了但實機整合等後續 PR）」。`transcript.v1` cue 可以選擇性帶上 `speaker_id` 欄位，validation 會保留它過去。
- Review dashboard 新增單一操作的詳情 endpoint：`GET /api/operation/<id>`，回傳跟 `/api/status` 的 `next` 一樣的標準欄位（operation_id、type、state、risk、confidence、source、detector、reason_code、evidence_text、required_review、preview_ref、removed_ref、decision_commands）。狀態 endpoint 新增篩選參數 `GET /api/status?filter=<type>`，可以先掃完所有 silence-cut 再處理 retake-cut。瀏覽器鍵盤快捷鍵：`a` accept、`r` reject、`u` undo、`j` 跳到下一個待審。`k` 目前是 `j` 的 forward alias，真正的「回到上一個」要等後續 PR。游標在 reviewer / note 輸入欄時快捷鍵會自動暫停。`/api/operation/<id>` 的 path guard 會在比對前先把 percent-encoded 變形（`%2e%2e`、`%2F…`）跟控制字元跟 `.`/`..` 擋掉。

### 變更
- 尚未正式發布；發布前需更新版本與驗證結果。

### 修正
- 尚未正式發布。
- `ai draft` 加入 `--dry-run` 互斥/別名行為，並對齊 `--no-net` 安全路徑。
- `review serve` 在含 AI 草稿時會保留對 dashboard 的可見連結，避免 API/HTML 資訊斷層。
