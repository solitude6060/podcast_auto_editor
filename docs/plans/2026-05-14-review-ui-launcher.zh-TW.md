# 本機審閱 UI 啟動器

## 目標
完成 UI-4 桌面包裝準備階段，但不加入桌面框架依賴：產生本機 launcher 檔案，用來啟動指定 run directory 的 localhost review UI。

## 範圍
- 新增 POSIX shell script 與 optional Linux `.desktop` file 的 launcher 產生工具。
- 新增 `review launcher <run_dir> --out <script> [--desktop-out <file>]` CLI 指令。
- Host validation 維持 localhost-only。
- 產生的 launcher 屬於本機 artifacts，不是要提交的 run output。
- 更新英文與繁體中文使用文件。

## 驗收條件
- 產生的 shell launcher 會啟動 `python -m podcast_auto_editor review serve <run_dir>`，且 host/port 只用 localhost 範圍。
- Launcher 會安全 quote 含空白或 shell metacharacters 的路徑。
- Optional `.desktop` file 指向產生的 launcher，且設定為非 terminal。
- 無效 host 會在寫檔前被拒絕。
- `uv` 測試與 compileall 全部通過。
