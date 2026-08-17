# 競品景觀 — Podcast 自動後製工具（2026-08 更新）

查閱日期：2026-08-17  
取代：`docs/research/2026-05-17-competitor-landscape.md`（2026-05-17）  
觀察角度：本機優先、上線前可審查（`timeline.v1` + 逐項預覽）、可放進 git 的剪輯配方、音訊優先 WAV/MP3/M4A、可選 MP4。  
本產品不做：取代 DAW（數位音訊工作站）、雲端錄音、聲音克隆、上架／RSS 上傳。

## 方法

- 事實只採用一手來源：官方產品／定價／文件頁、官方 GitHub 儲存庫、官方隱私權政策、官方部落格、Adobe 網域上的 Community 貼文。
- GitHub star 數取自 2026-08-17 抓到的儲存庫頁面。未抓到的頁面不填星數。
- 美元價格只在官方頁面有渲染出數字時才記錄。僅存在於 JavaScript、靜態 HTML 看不到的金額，標為「抓到的 HTML 未顯示」。
- 二手評論（部落格、彙整站）標為補充，不用來當價格或星數來源。
- Reddit：這次沒有抓到可引用的討論串網址。2026-05 調查裡的 Reddit 說法，不當作本次的現行證據。
- 英文正本：`docs/research/2026-08-17-competitor-landscape.md`。

## 相對 2026-05-17 的變化

| 變化 | 證據 | 對本專案的後果 |
|---|---|---|
| Auphonic 於 2026-03-26 推出官方 CLI（命令列介面），流程是上傳、處理、下載 | https://auphonic.com/blog/2026/03/26/auphonic-cli/ | 「有 CLI + 配方」不再是獨特的*介面*。本機、不上傳、可放進 git 的 `timeline.v1` 仍是。 |
| Auphonic Automatic Cutting 支援影片；Auphonic Editor 可逐段啟用／停用剪輯，並匯出 cut list（剪輯清單：EDL / FCPXML / Reaper / Audacity / Audition） | https://auphonic.com/blog/2026/04/15/automatic-video-cutting/ | 「逐段審查」不再只對雲端處理器成立。EDL／Reaper 互換格式已是基本能力。 |
| Adobe Podcast（2026-03）新增音源分離滑桿、stem（分軌）下載、Studio 錄影、多軌匯入 | https://podcast.adobe.com/en/guides/whats-new-in-adobe-podcast-march-2026 | Enhance 仍是免費／低價降噪的比較基準；仍要上傳，仍有每日上限。 |
| Premiere Pro 測試版新增 Separate Crosstalk（串音分離，每秒 1 Generative Credit）與內建 AI Assistant | https://community.adobe.com/announcements-732/now-in-beta-separate-crosstalk-in-premiere-1634070 ；https://community.adobe.com/announcements-727/meet-your-new-assistant-editor-ai-assistant-in-premiere-pro-is-now-in-public-beta-1629317 | 串音分離是工作室痛點，本專案尚未處理。按秒計費。 |
| ElevenLabs Studio 3.0 用 Voice Isolator + Speech Correction（聲音克隆）行銷 podcast 清理 | https://elevenlabs.io/studio | 生成／克隆產品。超出範圍。 |
| Castmagic 官方年繳標價為 Hobby 每月 $19／Starter $48／Team $139 | https://www.castmagic.io/pricing | 低於 2026-05 調查的 $39／$99／$299。仍不是音訊剪輯器。 |
| Resound 官方定價為免費 20 分鐘／Creator $15（4 小時）／Studio $60（30 小時） | https://www.resound.fm/pricing | 逐項 Cut／Keep 仍在；免費額度是 20 分鐘，不是五月寫的每月 1 小時。 |
| Riverside 公開方案為 Pro／Grow／Webinar（Grow 取代五月的 Live 名稱） | https://riverside.com/pricing | 仍是錄音 + 雲端剪輯。Magic Audio 匯出要付費方案。 |
| 出現若干本機 OSS「Descript 替代」（星數很少） | 見第 2 節 GitHub 頁 | 印證本機審查這條縫；沒有產品同時提供可放進 git 的 `timeline.v1` + 把台灣華語當一等公民。 |
| 商業 ASR（自動語音辨識）語言表：Descript、Cleanvoice 仍未列中文／台灣華語 | https://www.descript.com/pricing ；https://cleanvoice.ai/filler-words/ | 這次最硬的語言缺口證據。 |

---

## 1. 商業產品

每張卡片：名稱、網址、授權或定價（來源 + 2026-08-17）、本機或雲端、實際做什麼、重疊、對方較強處、Podcast Auto Editor 獨有或缺少什麼。

### 1.1 Descript

- **網址**：https://www.descript.com/pricing（定價與功能表）；https://www.descript.com/security（儲存／隱私）
- **定價（官方，2026-08-17）**：Free $0 — 每月 60 媒體分鐘、一次性 100 AI credits。Hobbyist 每人每月 $16／$24（年繳／月繳）— 10 媒體小時、每月 400 credits。Creator $24／$35 — 30 小時、800 credits。Business $50／$65 — 40 小時、1500 credits。Enterprise 另議。兩套計量：媒體小時（匯入／錄製）與 AI credits（Underlord、Studio Sound、filler 移除等）。
- **本機或雲端**：雲端。官方安全頁：專案檔、逐字稿、中繼資料存在 Descript 伺服器（AWS／Google Cloud）。轉寫可能走 Rev 或他們基礎設施內的 Whisper。Custom Voice 訓練使用 Google Cloud。
- **實際做什麼**：以文字當時間軸的音訊／影片剪輯器。官方表列 Studio Sound、Remove Filler Words、Shorten Word Gaps、Edit for Clarity、Remove Retakes、章節、節目說明／社群草稿、AI 語音／自訂聲音克隆、Rooms 遠端錄音、字幕、翻譯／配音。轉寫標榜 25 種語言：Catalan、Croatian、Czech、Danish、Dutch、English (US)、Finnish、French (FR)、German、Greek、Hindi、Hungarian、Italian、Latvian、Lithuanian、Malay、Norwegian、Polish、Portuguese (BR)、Romanian、Slovak、Slovenian、Spanish (US)、Swedish、Turkish。**該表沒有中文。**
- **重疊**：filler／靜音、降噪、章節、節目說明、轉寫、專案內可還原的刪除。
- **對方較強**：成熟的「刪字即剪輯」介面；Rooms 錄音；短影音／再利用代理人；協作。
- **本專案獨有／缺少**：本機不上傳、分鐘數無上限、`timeline.v1` 接受／拒絕、git 配方。缺少文字即時間軸、聲音克隆（刻意不做）、錄音、團隊協作。Descript 的語言表也沒有中文。

### 1.2 Adobe Podcast（Enhance Speech + Studio）

- **網址**：https://podcast.adobe.com/en ；https://podcast.adobe.com/enhance ；https://podcast.adobe.com/en/plans ；https://podcast.adobe.com/en/guides/whats-new-in-adobe-podcast-march-2026
- **定價（官方方案頁，2026-08-17）**：Free 與 Premium 功能表。Free Enhance：僅音訊、無批次、無強度滑桿、每檔 30 分鐘／500 MB、每日 1 小時。Premium Enhance：影片、批次上傳、強度／語音－音樂－環境控制、每日 4 小時、每檔至多 1 GB／2 小時。Studio Free：下載至多 30 分鐘、每日 2 個專案、不能下載原始分軌。Studio Premium：下載無上限、可下載講者分離的原始檔。**抓到的官方方案 HTML 沒有 Premium 美元標價。** 補充部落格常寫每月 $9.99；本次不當作一手價格。
- **本機或雲端**：瀏覽器／雲端。要上傳。抓到的官方頁沒有本機處理主張。
- **實際做什麼**：Enhance Speech（降噪／去殘響）。Studio：遠端錄音、依逐字稿剪輯、字幕、audiogram。2026-03：音樂滑桿、stem 下載（語音／噪音／音樂）、Studio 錄影、多軌匯入並合成一份逐字稿。
- **重疊**：降噪、轉寫、輕量剪輯、可選影片。
- **對方較強**：一鍵 enhance 是市場上免費／低價的音質基準；stem 分離對救援混音有用。
- **本專案**：不上傳、無每日上限、剪輯可審查、LUFS／true-peak 輸出、章節／節目說明僅草稿。缺少 Enhance 等級的神經降噪與 stem 分離。

### 1.3 Riverside（含 Magic Audio）

- **網址**：https://riverside.com/pricing ；Magic Audio 說明：https://support.riverside.com/hc/en-us/articles/15079835638301-Magic-Audio-tracks-Overview 與 https://support.riverside.com/hc/en-us/articles/13395368921885-Apply-Magic-Audio-to-individual-tracks-in-the-editor
- **定價（官方，2026-08-17）**：Free $0 — 一次性 2 小時多軌、720p、浮水印、44.1 kHz。比較表：Pro 月繳 $29／年繳每月 $24（年繳 $288）；Grow $39／$34（年繳 $408）；Webinar $99／$79（其中一張卡片寫 Webinar「年繳 $408」— 以比較表的 $99／$79 為明確的月／年配對）。Business 另議。FAQ：分軌下載額度 Pro 15 小時／Grow 20／Webinar 25；錄音本身無上限；額外剪輯席次為加購；AI Credits 用於翻譯／B-roll／Animated Clips（Pro／Grow 起始 20）；Magic Clips、Magic Audio、AI Co-Creator 不消耗那些 credits。
- **本機或雲端**：本機擷取，再雲端上傳／同步。剪輯與 Magic Audio 在瀏覽器。說明：Magic Audio 匯出需 Pro／Live／Webinar／Business（說明文章仍用舊的 Live 方案名）。
- **實際做什麼**：遠端多軌錄音；文字剪輯；Magic Audio 強化並可調強度混合；Magic Clips；節目說明；轉寫；付費方案含託管／上架。
- **重疊**：靜音／filler、強化、逐字稿、節目說明。
- **對方較強**：遠端錄音品質與每位來賓獨立音軌。
- **本專案**：只做後製、不上傳、可審查配方。不做錄音（刻意）。Magic Audio 總覽頁有一次抓取逾時；套用到單軌的文章有搜尋摘錄，視為官方。

### 1.4 Cleanvoice AI

- **網址**：https://cleanvoice.ai/pricing ；https://cleanvoice.ai/filler-words/
- **定價（官方，2026-08-17）**：免費試用（filler 頁：30 分鐘、免信用卡）。隨用隨付：$11／5 小時（每小時 $2.20）、$20／10 小時、$45／30 小時；點數有效 2 年。訂閱：$11／10 小時、$30／30 小時、$90／100 小時；未用點數可結轉至多 3 倍方案上限。另計加值稅。依音訊長度計費，最少 1 分鐘、無條件進位。檔案保存 7 天後永久刪除（定價 FAQ）。
- **本機或雲端**：必須上傳。
- **實際做什麼**：filler、靜音、口部聲／呼吸、噪音、強化、影片 podcast 剪輯、時間軸匯出、轉寫與摘要。官方 filler 語言：英語、法語、羅馬尼亞語、德語、阿拉伯語。口音提到愛爾蘭、澳洲、德國。**未列中文。** 多軌 filler 並保持同步。Smart Remover 在剪完後補上房間底噪。
- **重疊**：靜音／filler、降噪、逐字稿、部分文案。
- **對方較強**：專職 filler／口部聲模型；定價頁列出 Timeline Export。
- **本專案**：本機、逐項審查、git 配方、無小時計量。缺少口部聲／口吃模型，以及 Cleanvoice 的 filler 語言包（該包也沒有中文）。

### 1.5 Auphonic

- **網址**：https://auphonic.com/pricing ；https://auphonic.com/privacy ；https://auphonic.com/cli ；https://auphonic.com/blog/2026/03/26/auphonic-cli/ ；https://auphonic.com/blog/2026/04/15/automatic-video-cutting/ ；https://auphonic.com/help/resources/cli.html
- **定價（官方，2026-08-17）**：免費每月 2 小時（免費輸出帶 jingle；免費額度不累積）。定期方案以小時計：S 9、M 21、L 45、XL 100、XXL 250 小時／月；定期額度月末作廢。一次買斷點數從 5 小時起、永不過期。**抓到的 HTML 沒有美元／歐元金額**（有幣別切換，靜態摘錄沒有數字）。付費功能含多語轉寫與自動節目說明／章節。CLI 在免費與付費皆列出。Watch folder／批次在付費方案。
- **本機或雲端**：雲端處理，伺服器在德國 Hetzner 與 Cloudflare R2（隱私權政策）。CLI 是本機二進位，**會上傳**到 API（`auphonic process interview.wav --wait --download`）。隱私：為改進演算法，「Content 可能被 Auphonic 員工觀看或聆聽」；製作檔在公告天數後刪除（音訊 21 天、影片／API 7 天），但可能留下片段供演算法使用。
- **實際做什麼**：Leveler、降噪／去殘響、AutoEQ、響度（EBU 等）、filler 與靜音剪、咳嗽／音樂剪、ASR、自動節目說明／章節、影片、API、CLI、預設檔。剪輯模式：套用剪輯、剪輯處改靜音、或保留原檔並匯出 cut list。Editor：依類型上色、啟用／停用、拖曳邊界、重跑不另扣點數。
- **重疊**：幾乎整條後製管線，除了「只在本機」與「git 原生配方」。
- **對方較強**：響度／leveler 口碑；cut list 互換；CLI+API+預設檔；影片剪輯；同一製作重跑不另收費。
- **本專案**：不上傳、無點數、使用者擁有的 `timeline.v1` 檔、離線 dry-prompt 文案。缺少 Auphonic 的 leveler 品質、咳嗽／音樂剪、以及尚未出貨的 DAW cut list 匯出。

### 1.6 Hindenburg PRO

- **網址**：https://hindenburg.com/products/hindenburg-pro ；商店：https://hindenburg.com/products/radio-podcast/ ；永久授權：https://hindenburg.com/products/radio-podcast/perpetual/
- **定價（官方商店 HTML，2026-08-17）**：個人 Standard／Plus／Premium。轉寫時數：Standard 0、Plus 20、Premium 50 小時／月。Manuscript（像文書處理一樣剪音訊）、影片軌、Soundly 音效庫（Premium 為 Premium Soundly）。月繳／年繳／永久購買按鈕在抓到的 HTML 沒有可見金額。永久授權頁：一次買斷；持續轉寫要訂閱；首月 30 小時轉寫而後過期。**$12／年繳 $99 不在抓到的官方 HTML**；只出現在補充評論。
- **本機或雲端**：本機桌面 DAW。依永久授權頁，轉寫是計量的雲端加購。
- **實際做什麼**：口語 DAW — 錄音、轉寫、剪輯、蒙太奇、混音、上架。行銷頁主張自動電平與響度；演算法清單不在抓到的 HTML。
- **重疊**：本機口語剪輯、逐字稿剪輯、電平。
- **對方較強**：真正的多軌 DAW、還原歷史、採訪／新聞工作流程。
- **本專案**：免費、可腳本化、審查優先的自動化、無席次授權。缺少 DAW 混音（刻意不做）。

### 1.7 SquadCast

- **網址**：https://squadcast.fm/ ；收購：https://www.descript.com/blog/article/descript-season-5-squadcast-joins-descript-easy-reliable-remote-recording-editing-in-one-place（2023-08-15）
- **定價**：獨立站仍在行銷雲端錄音。2026-08-17 未抓到現行獨立方案金額。Descript 2023 文：付費 Descript 訂戶可用 SquadCast；第二階段要把錄音收進 Descript。
- **本機或雲端**：本機擷取 + 雲端備份（squadcast.fm 主張）。
- **實際做什麼**：遠端多軌錄音。不是後製配方工具。
- **重疊**：剪輯配方上沒有。只當匯入來源。
- **對方較強**：錄音可靠度。
- **本專案**：不錄音（刻意）。

### 1.8 Zencastr

- **網址**：https://zencastr.com/pricing
- **定價（官方，2026-08-17）**：抓到的頁面只顯示 **Vibecastr Free** 與 **Enterprise Custom**。Free 欄列出本機錄音、自動雲端備份、無限分軌、無限後製點數、文字剪輯、無限轉寫時數、100+ 轉寫語言、章節／標題／描述生成、長停頓與進階 filler 移除、正規化、降噪、4 席、託管。**中階付費價格不在抓到的頁面。** Free 功能表視為廠商行銷；不杜撰 Pro 方案價格。
- **本機或雲端**：本機錄音 + 雲端備份（官方表）。
- **實際做什麼**：錄音 + 雲端剪輯 + 託管 + AI 清理／文案。
- **重疊**：filler／靜音、文案、章節、轉寫。
- **對方較強**：錄音 + 託管綑綁；宣稱 100+ 轉寫語言（抓到的頁面沒展開清單；**台灣華語未核實**）。
- **本專案**：本機後製、不託管、可審查配方。

### 1.9 Castmagic

- **網址**：https://www.castmagic.io/pricing
- **定價（官方，2026-08-17）**：年繳：Hobby 每月 $19（年 $239）— 圖書館內 30 轉寫小時。Starter 每月 $48（年 $579）— 100 小時。Team 每月 $139（年 $1,669）— 400 小時、5 席。Business & Scale 從每月 $699 起（同一頁另有一行 $999）。時數是累積圖書館總量；可加買。FAQ 在 60+ 語言中列出「Mandarin (Simplified)」。
- **本機或雲端**：雲端上傳。
- **實際做什麼**：轉寫 + 節目說明、章節、短片、社群、電子報。**不是音訊剪輯器。**
- **重疊**：僅審查用的節目說明／章節。
- **對方較強**：提示詞庫與再利用產量。
- **本專案**：文案維持審查、可 dry-prompt／本機。缺少 Castmagic 的模板深度。Castmagic 不做剪輯／降噪。

### 1.10 Wondercraft

- **網址**：https://www.wondercraft.ai/pricing
- **定價（官方，2026-08-17）**：Free $0 — 150 credits、720p。Creator 月繳 $25／年繳 $21 — 1,000 credits。Pro 每月 $45 — 2,000–6,000 credits、最多 3 人。Enterprise 另議。頁面版權 2025。
- **本機或雲端**：雲端 AI 生成（聲音、影片、虛擬角色）。
- **實際做什麼**：用 AI 角色與聲音生成類 podcast／影片。定價頁行銷「Convo Mode (Editable NotebookLM Audio)」。
- **重疊**：本專案不想重疊的部分（聲音生成超出範圍）。
- **對方較強**：生成式節目製作。
- **本專案**：剪真實錄音；不合成主持人。

### 1.11 Krisp

- **網址**：https://krisp.ai/pricing/
- **定價（官方，2026-08-17）**：會議 AI — 7 天試用。Core 每使用者每月 $16／$8（月繳／年繳）。Advanced $30／$15。Enterprise 另議；Enterprise 列出「Private Transcription & Recordings (On-device)」。Call Center 年繳每座席每月 $10 起。會議方案皆含降噪。
- **本機或雲端**：通話路徑上的桌面降噪；筆記／轉寫走產品雲端，Enterprise 可選本機轉寫。
- **實際做什麼**：即時會議降噪、筆記、口音轉換。不是 podcast 時間軸剪輯器。
- **重疊**：只有降噪，而且在錄音當下，不是後製。
- **對方較強**：雙向即時降噪。
- **本專案**：後製、離線、可審查剪輯。

### 1.12 Adobe Premiere Pro 與 podcast 相鄰的功能

- **網址**：Adobe Community（Adobe 網域）：Separate Crosstalk https://community.adobe.com/announcements-732/now-in-beta-separate-crosstalk-in-premiere-1634070 ；AI Assistant https://community.adobe.com/announcements-727/meet-your-new-assistant-editor-ai-assistant-in-premiere-pro-is-now-in-public-beta-1629317 ；Enhance Speech 瑕疵討論見第 3 節。
- **定價**：Creative Cloud 訂閱。Separate Crosstalk：每秒音訊 1 Generative Credit，另加兩側各 2 秒 handle；片段 1 秒至 10 分鐘。2026-08-17 官方 Premiere 產品頁抓取逾時。
- **本機或雲端**：桌面程式；Firefly／合作模型與 credits 走雲端。
- **實際做什麼**：完整 NLE（非線性剪輯）。Essential Sound 內的 Enhance Speech（Community + 補充來源）。測試版：把兩人重疊說話與環境聲分開；Assistant 做分箱／逐字稿／粗剪。
- **重疊**：強化、依逐字稿剪輯、串音。
- **對方較強**：影片時間軸、串音實驗、產業互換格式。
- **本專案**：不是 NLE。應匯出到 Premiere，不取代它。

### 1.13 Podcastle

- **網址**：https://www.podcastle.ai/pricing
- **定價**：官方定價頁於 2026-08-17 **兩次逾時**。**本次沒有現行官方金額。** 不要把 2026-05 的 $14.99／$29.99 當作已核實的 2026-08 價格。
- **本機或雲端**：雲端工作室（先前官方定位；本次除網址存在外未再核實）。
- **實際做什麼**：錄音 + 剪輯 + AI 聲音 + 清理（產品類別）。細節未再抓取。
- **重疊／較強／獨特**：**本次一手來源不足。**

### 1.14 ElevenLabs Studio（與 podcast 相鄰）

- **網址**：https://elevenlabs.io/studio ；https://elevenlabs.io/pricing
- **定價（官方，2026-08-17）**：Free $0／1 萬 credits／3 個 Studio 專案。Starter $6／3 萬／20 專案。Creator $22（首月 $11）／12.1 萬。Pro $99／60 萬。Scale $299／180 萬／3 席。Business $990／600 萬／10 席。年繳 = 付 10 個月。共用點數：Voice Isolator 每分鐘 1,000 credits；Speech-to-Text 每分鐘 330（FAQ）。
- **本機或雲端**：雲端。Speech Correction 使用 AI 聲音克隆（官方 Studio 頁）。
- **實際做什麼**：生成 + 錄製音訊／影片的時間軸：TTS、音樂、音效、字幕、Voice Isolator、Speech Correction、Studio Agent。行銷「Podcasters：清理對白……不用重錄就能改錯」。
- **重疊**：降噪（isolator）、字幕、逐字稿。
- **對方較強**：生成式修補與配樂。
- **本專案**：明確不做聲音克隆。Isolator 品質只當降噪基準。

### 1.15 Alitu

- **網址**：https://alitu.com/pricing/
- **定價（官方，2026-08-17）**：比較區塊：「Get it all with Alitu 年繳每月 $32」以及促銷行「年繳每月 $20.58（sale price）」。代剪服務從每月 $295 起。7 天試用、30 天退款、可暫停至多 3 個月。託管每月 1,000 下載內免費，之後至 10,000 下載為 $10。**以頁面上非促銷的年繳每月 $32 為準；促銷價標為促銷。**
- **本機或雲端**：雲端。頁面宣稱錄音有本機備份。
- **實際做什麼**：意見導向的錄音 + 自動降噪／電平／EQ + Magic Filters（filler + 靜音）+ 文字或波形剪輯 + AI 節目說明 + 17 語轉寫 + 上架／託管。
- **重疊**：新手一鍵清理 + 文案。
- **對方較強**：最低摩擦的新手路徑 + 託管。
- **本專案**：不託管、無訂閱、操作可審查。缺少 Alitu 的代剪服務。

### 1.16 REAPER + SWS

- **網址**：https://www.reaper.fm/purchase.php（2026-08-17 抓取；頁首「DOWNLOAD REAPER Version 7.79: August 17, 2026」）；SWS：https://www.sws-extension.org/ ；https://github.com/reaper-oss/sws
- **定價／授權**：REAPER 優惠 $60、商業 $225、60 天完整試用、免費升級至 8.99。SWS/S&M：開源外掛，最新穩定版 v2.14.0 #7（2025-09-07）。GitHub **571 stars**（2026-08-17）。SWS 含 EBU R128 響度工具（sws-extension.org 連到專案 wiki）。
- **本機或雲端**：完全本機。
- **實際做什麼**：通用 DAW。ReaScript。SWS 加快照、響度、標記動作等。沒有內建 ASR／filler AI。
- **重疊**：本機、可腳本、專案檔可版本控制。
- **對方較強**：混音、外掛、無限還原、音訊優先 podcast 專業者的產業標準。
- **本專案**：意見導向的口語自動化 + 審查介面。應匯出到 REAPER（Auphonic 已能出 EDL），不取代它。

### 1.17 iZotope RX 12

- **網址**：https://www.izotope.com/en/products/rx.html
- **定價（官方，2026-08-17）**：RX 12 Advanced **$1,399.00**。Standard／Elements 價格不在抓到的 Advanced 頁。
- **本機或雲端**：本機程式 + DAW 外掛（AU/AAX/VST3）。列出的宿主含 Reaper 7、Adobe Audition 2026、Premiere Pro 2026。
- **實際做什麼**：頻譜修復、Dialogue Isolate、Repair Assistant、Scene Rebalance、Trim Silence、stems 檢視。手動 + 輔助。不是 podcast 配方執行器。
- **重疊**：降噪、靜音修剪、對白分離。
- **對方較強**：外科式修復品質；Repair Assistant 提出可調建議。
- **本專案**：免費的自動化審查管線。缺少 RX 等級修復。RX 沒有 git 配方，也不是中文優先 ASR。

### 1.18 Adobe Audition

- **網址**：https://www.adobe.com/products/audition.html
- **定價／功能**：官方產品頁於 2026-08-17 **逾時**。本次沒有一手功能／價格表。Audition 是 Creative Cloud 桌面 DAW；RX 12 列出 Audition 2026 為支援宿主。
- **本機或雲端**：本機剪輯器；部分 Adobe AI 功能走雲端／credits（見 Premiere Community）。
- **重疊／較強／獨特**：**本次一手來源不足。** 當作本專案應匯出的本機專業剪輯器，不當競爭對手。

### 1.19 Resound（補充 — 最接近的審查介面）

- **網址**：https://www.resound.fm/ ；https://www.resound.fm/pricing
- **定價（官方，2026-08-17）**：Free $0 — 每月 20 分鐘、MP3、1 軌、保存 1 天。Creator $15 — 4 小時、WAV/AAF/MP4、2 軌、保存 15 天、Enhance。Studio $60 — 30 小時、4 軌、保存 60 天、API。
- **本機或雲端**：雲端上傳。
- **實際做什麼**：偵測 filler 聲與超過 3 秒的靜音；使用者對每項 **Cut 或 Keep**；預覽；Enhance 混音／母帶；匯出合併檔或分軌。首頁路線圖：重複偵測、filler「詞」、影片、口吃（未宣稱已出貨）。
- **重疊**：逐項接受／拒絕 — 商業產品裡最接近本專案儀表板的介面。
- **對方較強**：成熟的 cut／keep 介面；AAF 可回 DAW。
- **本專案**：本機、無上限、`timeline.v1` + 還原對照表 + git。缺少 Resound 的 filler 聲模型與 AAF 匯出。

---

## 2. 開源／GitHub 專案

星數除另註外，取自 2026-08-17 的 GitHub 儲存庫頁。

### 2.1 WyattBlue/auto-editor

- **網址**：https://github.com/WyattBlue/auto-editor — **4,984 stars**
- **授權**：Unlicense／公有領域（https://github.com/WyattBlue/auto-editor/blob/master/LICENSE）。README 摘錄：app.auto-editor.com 線上版使用本庫資產（Unlicense）另加專有資產。
- **本機或雲端**：本機 CLI；可選專有網頁應用。
- **實際做什麼**：依靜音／畫面動態自動重剪影片／音訊。不是審查儀表板，也不是章節／文案工具。
- **重疊**：本機靜音剪輯。
- **對方較強**：成熟 CLI、使用族群大、影片優先。
- **本專案**：上線前審查、`timeline.v1`、逐字稿／章節／文案、LUFS 門檻、繁中路徑。缺少 auto-editor 多年累積的邊界情況。

### 2.2 與 Auphonic 相關的 OSS

- **auphonic/auphonic-mobile**：https://github.com/auphonic/auphonic-mobile — **48 stars**。舊行動網頁。不是 2026 的 CLI。
- **Auphonic CLI**：https://auphonic.com/cli — **不是開源**。封閉二進位，包著雲端 API（2026-03-26 部落格）。
- **auphonic-api-examples**：列於 https://github.com/auphonic（組織摘錄 21 stars）。API 範例，不是本機引擎。
- **含義**：沒有可直接內嵌的開源 Auphonic leveler。

### 2.3 Whisper 家族與說話人分離

| 專案 | 網址 | Stars（2026-08-17） | 授權（一手） | 角色 |
|---|---|---|---|---|
| openai/whisper | https://github.com/openai/whisper | 107,437 | MIT（`LICENSE` 原文） | 基準 ASR；訓練語言含中文（模型卡／論文；本次未重抓語言表） |
| ggml-org/whisper.cpp | https://github.com/ggml-org/whisper.cpp | 52,956 | MIT（`LICENSE` 原文） | 本機 C/C++ ASR |
| SYSTRAN/faster-whisper | https://github.com/SYSTRAN/faster-whisper | 24,956 | MIT（`LICENSE` 原文） | 較快的本機 ASR |
| m-bain/whisperX | https://github.com/m-bain/whisperX | 23,610 | 本次**未取回**授權檔 | 詞級時間戳 + 對齊 + pyannote 說話人分離 |
| pyannote/pyannote-audio | https://github.com/pyannote/pyannote-audio | 10,429 | 本次**未取回**授權檔 | 說話人分離元件；典型用法需 Hugging Face token／模型條款 |

- **本機或雲端**：權重在本機。pyannote 模型常需接受 Hugging Face 條款（未重抓）。
- **重疊**：本專案的 `transcribe` 邊界；命令列預設仍是 `stub`（`cli.py`）。
- **對方較強**：裝好權重之後的真實 ASR 品質。
- **本專案**：`transcript.v1` 加上經還原對照表重對時間。`dev` 已有真實轉接器：`faster-whisper-local`、`whisper-cpp-local`、`qwen3-asr-local`（`podcast_auto_editor/asr.py`）。它們是可選依賴；quickstart 預設仍是 `stub`。中文專用模型見 `docs/research/2026-05-17-chinese-asr-models.md`（該文引用 Qwen3-ASR 模型卡：台灣華語 CV-zh-tw，1.7B 的 WER 3.77）。

### 2.4 響度 CLI

| 專案 | 網址 | Stars | 授權 | 角色 |
|---|---|---|---|---|
| slhck/ffmpeg-normalize | https://github.com/slhck/ffmpeg-normalize | 1,527 | 本次 LICENSE 原文 **404** | ffmpeg 響度正規化包裝 |
| Moonbase59/loudgain | https://github.com/Moonbase59/loudgain | 228 | BSD-2（庫內 man page） | ReplayGain 2.0／R128 標籤；不改寫音訊 |
| desbma/r128gain | https://github.com/desbma/r128gain | 171 | LGPLv2.1（庫內 LICENSE）；**已封存** | 掃描／標籤 |

- **重疊**：本專案已用 LUFS／true-peak 門檻輸出（README）。
- **對方較強**：實戰過的量測／標籤工具。
- **本專案**：應拿數字跟 ffmpeg-normalize／Auphonic 比，不要重做標籤器。

### 2.5 bbc/audiowaveform

- **網址**：https://github.com/bbc/audiowaveform — **2,157 stars**
- **授權**：本次未取回（BBC 專案；常為 GPL-3 — **不當作已核實**）。
- **實際做什麼**：從音訊產生波形資料與 PNG。審查介面的積木，不是剪輯器。
- **重疊**：儀表板預覽。
- **本專案**：可重用波形峰值；不必自製繪製器。

### 2.6 Podlove 與 Opencast

- **podlove/podlove-publisher**：https://github.com/podlove/podlove-publisher — **309 stars**。WordPress 發行：章節、網頁播放器、feed。**不是剪輯器。**
- **opencast/opencast**：https://github.com/opencast/opencast — **497 stars**。校園課堂擷取與發行。**不是筆電上的 podcast 剪輯器。**

### 2.7 本機 podcast／靜音／filler 工具（2026 GitHub）

| 專案 | 網址 | Stars | 自稱能力 | 對本專案 |
|---|---|---|---|---|
| trsdn/autocut | https://github.com/trsdn/autocut | 2 | 本機 CLI：Parakeet／whisper.cpp、靜音+filler、可選 LLM、EBU −16 LUFS、`--dry-` | 最接近的 OSS *管線*表親；無審查介面；README 摘錄有英／德語旗標 |
| dennisrongo/cut-clean | https://github.com/dennisrongo/cut-clean | 3 | 本機桌面；Whisper；開關 filler／靜音；**英語 filler；僅 MP4；最長 15 分鐘／專案 1 小時** | 有開關審查；影片優先；有時長上限 |
| whyaang/Bowdler | https://github.com/whyaang/Bowdler | 23 | 本機 Apple Silicon；逐字稿剪輯；**一次 $49**（README 摘錄，價格「截至 2026-04」） | 付費本機應用；宣稱 32 語 |
| electronicbrains/poddie | https://github.com/electronicbrains/poddie | 0 | 本機 Mac；刪字即剪；本機 Whisper 或 OpenAI API | 文字剪輯介面；無 git 配方 |
| b2bvic/declip | https://github.com/b2bvic/declip | 7 | Apple Silicon CLI；filler；重拍；預設 dry-run；可選 Resemble Enhance | dry-run 文化與本專案一致；偏影片／對鏡頭說話 |

以上皆未主張「可放進 git 的 `timeline.v1` + 還原對照表 + LUFS 發行門檻 + 繁中優先政策」。

### 2.8 本機 Enhance 替代

| 專案 | 網址 | Stars | 授權 | 角色 |
|---|---|---|---|---|
| Rikorose/DeepFilterNet | https://github.com/Rikorose/DeepFilterNet | 4,604 | Apache-2.0 或 MIT（`LICENSE` 原文） | 本機神經降噪 |
| xiph/rnnoise | https://github.com/xiph/rnnoise | 5,783 | 本次未取回 COPYING（歷史上為 BSD 風格） | 經典本機 RNNoise |
| resemble-ai/resemble-enhance | https://github.com/resemble-ai/resemble-enhance | 2,396 | 授權**未取回** | 本機語音降噪／強化 |
| modelscope/ClearerVoice-Studio | https://github.com/modelscope/ClearerVoice-Studio | 4,414 | 授權**未取回** | 強化／分離／目標說話人擷取工具組 |

- **重疊**：規劃中／本機降噪 vs Adobe Enhance。
- **本專案**：尚未出貨 Enhance 等級模型。DeepFilterNet 是最小、說得出口的本機實驗。

### 2.9 章節／節目說明產生器

- **FanaHOVA/smol-podcaster**：https://github.com/FanaHOVA/smol-podcaster — **412 stars**。帶說話人標籤的逐字稿、章節、標題、推文；OpenAI + Claude；「Edit Show Notes」合併介面。雲端 LLM。README 寫 Latent Space 在用。
- **jamesmontemagno/podcast-metadata-generator**：https://github.com/jamesmontemagno/podcast-metadata-generator — 星數**未抓**。用 Copilot SDK 從逐字稿產生標題／描述／章節／SRT。
- **AlperNab/podcast-show-notes**：https://github.com/AlperNab/podcast-show-notes — 星數**未抓**。瀏覽器工作流程；本機引擎 + 可選 LLM。
- **AssemblyAI auto chapters + LeMUR**：雲端 API（https://www.assemblyai.com — 完整定價未抓）。不是本機。
- **podcast2**：**查無一手來源**能對上「產生章節／節目說明」的同名專案。
- **Listen Notes**：https://www.listennotes.com/api/ — podcast **目錄／搜尋 API**（頁面寫 3,799,596 個節目／192,228,674 集）。不是剪輯器。Listener.com 被列為會產生標題／描述／說明的客戶 — 那是第三方應用，不是 Listen Notes 本身。

---

## 3. 使用者痛點（只列可引用網址）

焦點：上傳隱私、訂閱、誤剪、中文／台灣華語、可審查性、可重現性。

### 3.1 上傳／隱私

- **Descript 把專案存在他們的伺服器**（檔案、逐字稿、中繼資料）。https://www.descript.com/security — 2026-08-17。可選擇分享逐字稿以改進演算法（預設關閉）。Custom Voice 音訊會用來改進服務。
- **Auphonic** 可能讓員工聆聽 Content 以改進演算法；製作刪除後仍可能留下片段。https://auphonic.com/privacy — 2026-08-17。歐盟伺服器（Hetzner）+ Cloudflare R2。
- **Cleanvoice** 保留原始與編輯檔 **7 天**，而後永久刪除。https://cleanvoice.ai/pricing FAQ — 2026-08-17。
- **Krisp** 宣稱會議資料不用來訓練模型；Enterprise 提供本機轉寫。https://krisp.ai/pricing/ — 2026-08-17。
- Reddit 上傳隱私討論：**本次查無一手來源。**

### 3.2 訂閱／計量

- Descript：兩套計量（媒體小時 + AI credits）；Creator／Business 可加購。https://www.descript.com/pricing
- Riverside：計量的是分軌**下載**小時，不是錄音小時；部分功能另有 AI credit。https://riverside.com/pricing FAQ
- Cleanvoice／Auphonic／Castmagic／Resound／ElevenLabs／Adobe Podcast：小時、點數或每日上限（見第 1 節）。
- REAPER 仍是一次 $60／$225。https://www.reaper.fm/purchase.php
- Reddit「點數用完」討論：**本次查無一手來源。**

### 3.3 誤剪／破壞性強化／可審查性

- **Adobe Community — Enhance 機器聲／破碎**：https://community.adobe.com/questions-544/enhance-causing-robotic-voice-163859 ；https://community.adobe.com/bug-reports-328/enhance-audio-is-producing-garbled-results-1558150
- **Adobe Community — Enhance 改掉用詞**：https://community.adobe.com/questions-729/enhance-speech-is-way-off-completely-changing-words-via-the-faulty-ai-library-1408577
- **Adobe Community — 靜音處幻聽出語音**：https://community.adobe.com/bug-reports-728/essential-sound-enhance-speech-dialogue-tool-hallucinations-1330744
- **Adobe Community — 回音／雙重音訊**：https://community.adobe.com/bug-reports-733/enhance-speech-causing-audio-artifact-906741
- **Auphonic** 後來提供逐段啟用／停用 — 產品回應可從功能本身讀到（https://auphonic.com/blog/2026/04/15/automatic-video-cutting/）。Auphonic 剪太狠的使用者抱怨網址：**本次查無一手來源。**
- **Resound** 定價頁有 FAQ 標題「Does Resound cut out content automatically or do I have control?」（答案本文未抽出）。首頁：「Stay in control by reviewing each edit, selecting cut or keep」。
- **G2** 評論頁本次未能抓成可引用正文（多為市集摘要）。G2 Learn 有一篇引 Descript 使用者希望 filler 只從字幕拿掉、不要從影音拿掉：https://learn.g2.com/free-audio-editing-software

### 3.4 中文／台灣華語

- Descript 官方轉寫語言表：**沒有中文**。https://www.descript.com/pricing
- Cleanvoice 官方 filler 語言：英、法、羅馬尼亞、德、阿拉伯。**沒有中文**。https://cleanvoice.ai/filler-words/
- Adobe Podcast 2026-03 更新提到的網站／Studio 語言：法、德、義、西、葡、英（另有其他網站語系）。**未列繁體中文／台灣華語。** https://podcast.adobe.com/en/guides/latest-updates（較舊的 2025-02 說明）與 2026-03 what’s-new（無 zh-TW）。
- Castmagic FAQ：60+ 語言含 **簡體**中文。https://www.castmagic.io/pricing — 不是台灣華語，也不是剪輯器。
- 繁中本機 ASR 證據：`docs/research/2026-05-17-chinese-asr-models.md` 引用 Qwen3-ASR 模型卡（台灣華語 CV-zh-tw，1.7B 的 WER 3.77）。承重的中文路徑在這裡，不在雲端剪輯器。

### 3.5 可重現性

- 本次抓到的商業官方頁，沒有廣告等同 `timeline.v1` 的、可放進 git 的剪輯配方。
- 最接近：Auphonic 預設檔 + API／CLI + cut list 匯出；Cleanvoice 時間軸／EDL 匯出；REAPER 專案檔；Descript 可匯出時間軸到多個 DAW（定價表：Samplitude、Reaper、FCP、Pro Tools、Logic、Audition、Premiere）。
- 雲端專案檔仍在廠商端（Descript 安全頁）。

---

## 4. 對照表（2026-08-17）

圖例：+ 原生／強；~ 部分；— 無；$ 計量加購。「本工具」= README 所寫的 Podcast Auto Editor（2026-08 工作樹）。

| 功能 | Descript | Adobe Pod | Riverside | Cleanvoice | Auphonic | Castmagic | Hindenburg | Resound | REAPER | auto-editor | ElevenLabs Studio | **本專案** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Filler 移除 | + | — | + | + | + | — | ~ | +（聲；詞在路線圖） | — | — | — | ~（靜音；改語音的剪輯一律審查） |
| 靜音修剪 | + | ~ | + | + | + | — | + | + | ~ | + | — | + |
| 口部聲 | ~ | — | ~ | + | ~ | — | — | ~ | — | — | — | — |
| 降噪 | + | + | +（Magic Audio） | + | + | — | + | + | $ 外掛 | — | +（Isolator） | —（未出貨） |
| 響度 leveler | ~ | — | ~ | + | + | — | + | + | ~／SWS | — | — | +（LUFS／TP 門檻） |
| 自動章節 | + | — | + | — | + $ | + | ~ | — | — | — | — | +（審查） |
| 節目說明 | + | — | + | + | + $ | + | — | — | — | — | — | +（審查／dry-prompt） |
| 轉寫 | +（表無中文） | + | + | + | + $ | +（列簡中） | $ | + | — | — | + | 預設 stub；真實轉接器可選 |
| 刪字即剪輯 | + | +（Studio） | + | — | — | — | + | — | — | — | +（生成語音） | — |
| 逐項審查 | ~ | — | ~ | ~（報告／EDL） | +（2026 Editor） | — | +（DAW） | + | + | — | ~ | **+** |
| 可放進 git 的配方 | — | — | — | — | ~（預設／API） | — | — | — | ~（專案） | ~（CLI 旗標） | — | **+（產物）** |
| 100% 本機 | — | — | — | — | — | — | ~（ASR 雲端） | — | + | + | — | **+** |
| 不必上傳 | — | — | — | — | — | — | 剪輯可 | — | + | + | — | **+** |
| CLI | — | — | — | API | +（會上傳） | API | ~ | — | + | + | API | **+** |
| 訂閱地板 | 年繳每月 $16 | Premium 金額不在 HTML | 年繳每月 $24 | 每月 $11 | 免費 2 小時再付費 | 年繳每月 $19 | 金額不在 HTML | 每月 $15 | 一次 $60 | 免費（CLI） | 每月 $6 | **免費** |

Podcastle、Audition、Premiere：因官方頁未完整抓到，不列入表。

---

## 5. 綜合 — 對本專案的調整含義

每項：缺口、證明缺口重要的競品、最小下一步實驗。

這些實驗是**階段 2 候選**，不能取代 `docs/plans/2026-08-17-adjustment-and-next.zh-TW.md` 的階段 1 真實集數。fix-log 指出 blocker 之後，最多只做其中一條。

1. **Cut list 互換已是預期能力。**  
   **缺口**：`timeline.v1` 對內完整、對外看不見。  
   **證明**：Auphonic 匯出 EDL／FCPXML／Reaper／Audacity／Audition cut list（https://auphonic.com/blog/2026/04/15/automatic-video-cutting/）。Cleanvoice 列出 Timeline Export。Descript 列出 DAW 時間軸匯出。  
   **最小實驗**：從一份已接受的 `timeline.v1` 產出 Reaper region EDL（或 Auphonic 形狀的 cut list），匯入 REAPER。成功條件 = 區段落在正確範圍。不要做 DAW。

2. **逐段審查不再是獨特的*品類*。**  
   **缺口**：Resound（cut／keep）與 Auphonic Editor（啟用／停用、拖邊界、重跑不另收費）已經在賣審查。  
   **證明**：https://www.resound.fm/ 與 Auphonic 2026-04-15 部落格。  
   **最小實驗**：請製作人審查 40 筆靜音+語音提案，比較本專案儀表板與同一批剪輯印成清單的耗時。若儀表板沒有明顯較快，下一步介面是「依類型批次保留 + 波形上下文」，不是再加文案。

3. **台灣華語／繁中在商業剪輯器仍是真空。**  
   **缺口**：Descript 官方 25 語沒有中文；Cleanvoice filler 沒有中文；Adobe Podcast 更新未列 zh-TW。  
   **證明**：https://www.descript.com/pricing ；https://cleanvoice.ai/filler-words/  
   **最小實驗**：一集 60 分鐘繁中，跑 Qwen3-ASR 1.7B 對照 Whisper large-v3（程序已在 `docs/research/2026-05-17-chinese-asr-models.md`）。指標：5 分鐘人工逐字稿的 WER／CER，以及章節草稿是否堪用。這是 ASR 的繼續／調整決策，不是平台重寫。

4. **Enhance 等級降噪是使用者十秒內會拿來比的功能。**  
   **缺口**：本專案尚未出貨神經強化。Adobe Enhance 與 Community 瑕疵串同時顯示需求與失敗模式（機器聲、改詞、幻聽語音）。  
   **證明**：Adobe 方案頁 + https://community.adobe.com/questions-729/enhance-speech-is-way-off-completely-changing-words-via-the-faulty-ai-library-1408577  
   **最小實驗**：同一段 10 分鐘吵雜繁中，比 DeepFilterNet、RNNoise、未處理。產出 = A/B 檔 + 一頁試聽紀錄。來賓同意不清楚時，第一次不要把音訊上傳到 Adobe。

5. **Filler／口部聲模型仍是 Cleanvoice 的護城河；只做英語的 OSS filler 過不了繁中。**  
   **缺口**：只自動剪靜音，服務不到「嗯／啊／那個」。Cleanvoice 未列中文。CutClean／declip 文件寫英語詞表。  
   **證明**：https://cleanvoice.ai/filler-words/ ；CutClean README（英語 filler）。  
   **最小實驗**：在一份繁中逐字稿上，用詞級時間戳 + 詞表偵測 嗯／啊／呃／那個，只以 `proposed` 寫入 `timeline.v1`，對 50 筆人工 keep／cut 清單量誤剪率。

6. **刪字即剪輯是使用者願意付 Descript 的東西；不要克隆 DAW，要克隆「詞的開關」。**  
   **缺口**：匯入的 `transcript.v1` 還不是剪輯面。  
   **證明**：Descript「像文件一樣剪」；Adobe Studio「像文件一樣剪音訊」；Hindenburg Manuscript；Poddie／Bowdler／CutClean。  
   **最小實驗**：既有審查介面裡，點逐字稿 cue 就切換重疊的操作。不加新的剪輯器外殼。

7. **計量仍是轉換故事；Auphonic 的 CLI 沒有拿掉上傳，也沒有拿掉小時上限。**  
   **缺口**：README 對照表仍引用 2026-05 價格；若干 2026-08 官方數字已變（Castmagic、Resound、Riverside 方案名）。  
   **證明**：第 1 節官方定價網址。  
   **最小實驗**：在研究資料夾做一頁試算（或之後再寫進 README 註腳）：「每月 4 集 × 90 分鐘」，只用 2026-08-17 官方數字：Descript Hobbyist 10 小時 + 400 credits；Riverside Pro 15 小時分軌下載；Cleanvoice $11／10 小時；Auphonic 免費 2 小時 + 下一檔定期時數；Resound Creator 4 小時；Adobe 免費每日 1 小時。不杜撰 Adobe Premium 美元價。

8. **不要追錄音、克隆、上架。**  
   **缺口**：沒有 — 這些仍正確地超出範圍。  
   **證明**：錄音由 Riverside／SquadCast／Zencastr 擁有；ElevenLabs Studio 的 Speech Correction 是克隆；Castmagic／Listen Notes 擁有發行周邊的文字。  
   **最小實驗**：無。整合故事維持「從 Riverside 匯入」。

---

## 6. 這次不該因此改的事

- 不要因為 ElevenLabs 與 Descript 在賣，就加聲音克隆。
- 不要因為 Alitu 與 Riverside 綑綁，就加 RSS／託管。
- 不要變成 DAW：REAPER、Hindenburg、RX 已在，Auphonic 已能把 cut list 交給它們。
- 不要把星數很少的 OSS（autocut、Poddie、CutClean）當成介面已驗證 — 它們證明的是對*本機*的需求，不是成品。

---

## 來源（除頁面自註日期外，查閱日為 2026-08-17）

與英文正本第 6 節同一組網址。英文正本：`docs/research/2026-08-17-competitor-landscape.md`。
