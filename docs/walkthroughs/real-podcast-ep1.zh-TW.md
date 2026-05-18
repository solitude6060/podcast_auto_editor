# 真實 Podcast 操作說明：EP1

English version: `docs/walkthroughs/real-podcast-ep1.md`

## 目標

用本機 WAV 錄音執行 PR-A2 第一階段流程，維持與 `quickstart` 相同的離線/模擬預設值。
目的是確認 pipeline 能夠讀取真實錄音，並產生 review-session、recipe、AI 草稿等成品，
不需要把私人媒體檔案提交進 repo。

真實中文 ASR（X2.1 — 已上線）的操作說明見下方各節。對齊（X3.1— WhisperX）與語者分離（C2 — pyannote）有各自的 runbook：`docs/runbooks/whisperx-alignment-setup.md`、`docs/runbooks/pyannote-setup.md`。預設仍使用 stub 模式，需個別啟用才會跑真實 provider。

## 輸入

使用本機 WAV 檔案。EP1 煙霧測試預設掛載路徑：

```bash
/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav
```

請勿將 `/media/` 路徑下的檔案提交至 repo。

## 端對端指令

```bash
bash scripts/walkthrough-real-podcast.sh \
  --audio "/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav"
```

等效的直接 CLI 指令：

```bash
uv run python -m podcast_auto_editor quickstart \
  --real-audio "/media/ma/1AF83466F83441F5/startup/ep1-test-soundtrack-20260429/Untitled_1 #06.wav" \
  --out runs/walkthrough \
  --episode-id ep1-real
```

## 預期成品路徑

腳本執行後會列印以下路徑：

```text
review-session.json: runs/walkthrough/runs/ep1-real/review-session.json
recipe.v1.json:      runs/walkthrough/runs/ep1-real/recipe.v1.json
ai-draft.v1.json:    runs/walkthrough/runs/ep1-real/ai/ai-draft.v1.json
```

核心執行成品在：

```text
runs/walkthrough/runs/ep1-real/timeline.proposed.v1.json
runs/walkthrough/runs/ep1-real/timeline.accepted.v1.json
runs/walkthrough/runs/ep1-real/exports/transcript.json
```

若錄音通過現有的發布品質關卡，發布成品會寫入 `runs/walkthrough/runs/ep1-real/exports/`。
若未通過，腳本會印出警告並繼續寫入檢查成品；此時不代表錄音已具備發布品質。

## 開啟 Dashboard

執行完成後開啟本機審閱 dashboard：

```bash
uv run python -m podcast_auto_editor review serve runs/walkthrough/runs/ep1-real
```

預設網址：`http://127.0.0.1:8765`

## 中文 ASR：使用 Belle 模型（PR-X2.1）

透過 `faster-whisper-local` 提供者搭配 `Belle-whisper-large-v3-zh` 模型，
對中文（普通話）Podcast 進行真實語音識別，不需要修改任何公開 API：

```bash
podcast-auto-editor transcribe path/to/zh-episode.wav \
  --provider faster-whisper-local \
  --model BELLE-2/Belle-whisper-large-v3-zh \
  --device cuda \
  --compute-type float16 \
  --out runs/ep/transcript.json
```

注意事項：
- 模型授權為 Apache-2.0，不需要 HuggingFace 驗證金鑰。
- 可使用 CPU 回退（`--device cpu --compute-type int8`），但速度約為即時的五分之一；
  large-v3 權重約 3 GB，強烈建議使用 CUDA GPU。

### 驗證

執行環境變數控制的整合測試（預設 CI 自動跳過，這是設計如此）：

```bash
PAE_BELLE_REAL=1 PAE_BELLE_REAL_AUDIO=/path/to/zh_sample.wav \
    uv run --group dev pytest tests/test_asr_belle_real.py -v
```

此測試需要已安裝 `faster-whisper`，且 Belle 模型已下載至本機或存在於 HuggingFace 快取。
未設定 `PAE_BELLE_REAL=1` 時，該測試會自動跳過，不影響一般測試套件的執行。

## 備注

- `--real-audio` 會驗證輸入檔案存在、是一般檔案且副檔名為 `.wav`。
- 輸入 WAV 會被硬連結或複製到 `runs/walkthrough/raw/ep1-real.wav`；原始 `/media/` 檔案不會被修改。
- 以相同 `--out` 重新執行 `scripts/walkthrough-real-podcast.sh` 時，該輸出目錄會先被刪除再重建。
- 此 walkthrough 預設使用 stub 逐字稿提供者與乾跑 AI 草稿模式。
- 出現發布品質關卡警告代表 PR-A2 的檢查成品已產生，但主控和匯出的就緒狀態仍需另行跟進。
- PR-X2.1 的 env-gated 測試（`PAE_BELLE_REAL=1`）僅驗證 Belle 模型可以載入並產出非空 transcript，並未驗證中文解碼品質；中文品質需要操作者對照原始錄音進行人工檢查。
