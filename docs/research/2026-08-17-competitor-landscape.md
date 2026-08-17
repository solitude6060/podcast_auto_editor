# Competitor Landscape — Podcast Auto-Editing Tools (2026-08 update)

Date accessed: 2026-08-17  
Supersedes: `docs/research/2026-05-17-competitor-landscape.md` (2026-05-17)  
Lens: local-first, review-before-ship (`timeline.v1` + per-operation preview), git-checkable recipes, audio-first WAV/MP3/M4A, optional MP4.  
Not in scope for this product: DAW replacement, cloud recording, voice cloning, publishing/RSS upload.

## Method

- Primary sources only for facts: official product/pricing/docs pages, official GitHub repositories, official privacy policies, official vendor blogs, Adobe Community posts written on Adobe-owned domains.
- GitHub star counts are from the repository page as fetched on 2026-08-17. If a page was not fetched, the count is omitted.
- Dollar prices are recorded only when the official page rendered a number. JavaScript-only prices are marked “not shown on fetched HTML”.
- Secondary reviews (blogs, aggregators) are labeled supplemental and are not used as the source of a price or star count.
- Reddit threads: no primary Reddit URLs were retrieved in this pass. Do not carry May-2026 Reddit claims forward as current evidence.
- Traditional Chinese sibling: `docs/research/2026-08-17-competitor-landscape.zh-TW.md`.

## What changed since 2026-05-17

| Change | Evidence | Consequence for this project |
|---|---|---|
| Auphonic shipped a first-party CLI (2026-03-26) that uploads, processes, and downloads | https://auphonic.com/blog/2026/03/26/auphonic-cli/ | “CLI + recipes” is no longer unique as a *surface*. Local + no-upload + git-checkable `timeline.v1` still is. |
| Auphonic Automatic Cutting now covers video; the Auphonic Editor can activate/deactivate individual cuts and export cut lists (EDL / FCPXML / Reaper / Audacity / Audition) | https://auphonic.com/blog/2026/04/15/automatic-video-cutting/ | Per-cut review is no longer unique vs this cloud processor. Interchange formats (EDL/Reaper) are now table stakes. |
| Adobe Podcast (March 2026) added source-separation sliders, stem download, Studio video recording, and multitrack import | https://podcast.adobe.com/en/guides/whats-new-in-adobe-podcast-march-2026 | Enhance remains the free/cheap denoise bar; still cloud upload, still daily caps. |
| Premiere Pro beta added Separate Crosstalk (1 Generative Credit / second) and an in-app AI Assistant | https://community.adobe.com/announcements-732/now-in-beta-separate-crosstalk-in-premiere-1634070 ; https://community.adobe.com/announcements-727/meet-your-new-assistant-editor-ai-assistant-in-premiere-pro-is-now-in-public-beta-1629317 | Crosstalk split is a studio pain this project does not solve. Credit-metered. |
| ElevenLabs Studio 3.0 markets podcast cleanup via Voice Isolator + Speech Correction (voice clone) | https://elevenlabs.io/studio | Generation/clone product. Out of scope. |
| Castmagic annual prices on the official page are Hobby $19 / Starter $48 / Team $139 per month billed annually | https://www.castmagic.io/pricing | Lower than the 2026-05 survey’s $39 / $99 / $299 figures. Still not an audio editor. |
| Resound official pricing is Free 20 min / Creator $15 (4 h) / Studio $60 (30 h) | https://www.resound.fm/pricing | Per-edit cut/keep still exists; free tier is 20 minutes, not the 1 h/month cited in May. |
| Riverside public pricing uses Pro / Grow / Webinar (Grow replaces the May “Live” label) | https://riverside.com/pricing | Still a recorder + cloud editor. Magic Audio export is paid. |
| Several local OSS “Descript alternatives” appeared (tiny star counts) | GitHub pages listed in §2 | Validates the local-review wedge; none ship git-checkable `timeline.v1` + 繁中 (Taiwan Mandarin) as a first-class path. |
| Commercial ASR language lists still omit Chinese / Taiwan Mandarin on Descript and Cleanvoice | https://www.descript.com/pricing ; https://cleanvoice.ai/filler-words/ | Strongest language-gap evidence this pass. |

---

## 1. Commercial products

Each card: name, URL, license/pricing (source + 2026-08-17), local vs cloud, what it actually does, overlap, what it does better, what Podcast Auto Editor uniquely has or lacks.

### 1.1 Descript

- **URL**: https://www.descript.com/pricing (pricing + feature table); https://www.descript.com/security (storage/privacy)
- **Pricing (official, 2026-08-17)**: Free $0 — 60 media minutes/month, 100 one-time AI credits. Hobbyist $16 / $24 per person/month (annual / monthly) — 10 media hours, 400 AI credits/month. Creator $24 / $35 — 30 hours, 800 credits. Business $50 / $65 — 40 hours, 1500 credits. Enterprise custom. Dual meters: media hours (imported/recorded) and AI credits (Underlord, Studio Sound, filler removal, etc.).
- **Local vs cloud**: Cloud. Official security page: project files, transcripts, and metadata are stored on Descript servers (AWS / Google Cloud). Transcription may use Rev or an in-infrastructure Whisper host. Custom Voice training uses Google Cloud.
- **What it does**: Text-based audio/video editor. Official table lists Studio Sound, Remove Filler Words, Shorten Word Gaps, Edit for Clarity, Remove Retakes, Add chapters, show-note / social drafts, AI Speech / custom voice clones, Rooms remote recording, captions, translation/dubbing. Transcription advertised in 25 languages: Catalan, Croatian, Czech, Danish, Dutch, English (US), Finnish, French (FR), German, Greek, Hindi, Hungarian, Italian, Latvian, Lithuanian, Malay, Norwegian, Polish, Portuguese (BR), Romanian, Slovak, Slovenian, Spanish (US), Swedish, Turkish. **Chinese is not in that list.**
- **Overlap**: filler/silence, denoise, chapters, show notes, transcription, review-ish undo inside a project.
- **Better than this project**: polished text-delete-to-cut UX; Rooms recording; clip/repurpose agents; collaboration.
- **This project uniquely has / lacks**: has local no-upload + unlimited minutes + `timeline.v1` accept/reject + git recipe. Lacks text-as-timeline UX, voice clone (intentional), recording, team collab. Lacks Descript’s language coverage *and* Descript also lacks Chinese on the official transcription list.

### 1.2 Adobe Podcast (Enhance Speech + Studio)

- **URL**: https://podcast.adobe.com/en ; https://podcast.adobe.com/enhance ; https://podcast.adobe.com/en/plans ; https://podcast.adobe.com/en/guides/whats-new-in-adobe-podcast-march-2026
- **Pricing (official plans page, 2026-08-17)**: Free vs Premium feature table. Free Enhance: audio only, no bulk, no strength slider, 30 min / 500 MB per file, 1 hour/day. Premium Enhance: video, bulk upload, strength / speech-music-ambience controls, 4 hours/day, files up to 1 GB / 2 hours. Studio Free: download up to 30 min, 2 projects/day, no original-recording download. Studio Premium: unlimited downloads, speaker-separated originals. **Dollar price for Premium was not rendered on the fetched official plans HTML.** Supplemental blogs quote $9.99/month; that figure is not treated as primary here.
- **Local vs cloud**: Browser / cloud. Files are uploaded. No local-processing claim on the official pages fetched.
- **What it does**: Enhance Speech (denoise / echo). Studio: remote record, transcript-based edit, captions, audiograms. March 2026: music slider, stem download (speech / noise / music), Studio video recording, multitrack import with a unified transcript.
- **Overlap**: denoise, transcription, light cuts, optional video.
- **Better**: one-click enhance quality is the market’s free/cheap bar; stem split is useful for rescue mixes.
- **This project**: no upload, no daily cap, reviewable cuts, LUFS/true-peak render, chapters/show notes as review-only drafts. Lacks Enhance-class neural denoise and stem separation.

### 1.3 Riverside (including Magic Audio)

- **URL**: https://riverside.com/pricing ; Magic Audio help: https://support.riverside.com/hc/en-us/articles/15079835638301-Magic-Audio-tracks-Overview and https://support.riverside.com/hc/en-us/articles/13395368921885-Apply-Magic-Audio-to-individual-tracks-in-the-editor
- **Pricing (official, 2026-08-17)**: Free $0 — 2 hours one-off multi-track, 720p, watermark, 44.1 kHz. Compare-plans block: Pro $29 monthly / $24/mo annual ($288/year); Grow $39 / $34 ($408/year); Webinar $99 / $79 (page also shows Webinar “Billed $408 annually” in one card — treat the compare-plans $99/$79 pair as the explicit monthly/annual pair). Business custom. FAQ: separate-track downloads 15 h Pro / 20 h Grow / 25 h Webinar; recording itself unlimited; extra editor seats are add-ons; AI Credits for Translation / B-roll / Animated Clips (Pro/Grow start with 20); Magic Clips, Magic Audio, AI Co-Creator do not use those credits.
- **Local vs cloud**: Local capture with cloud upload/sync. Editing and Magic Audio run in the browser. Help: Magic Audio export requires Pro / Live / Webinar / Business (help article still uses the older “Live” plan name).
- **What it does**: Remote multi-track record; text-based edit; Magic Audio enhance with intensity blend; Magic Clips; show notes; transcription; hosting/publish on paid plans.
- **Overlap**: silence/filler, enhance, transcripts, show notes.
- **Better**: remote recording quality and per-guest tracks.
- **This project**: post-only, no upload, review recipe. Lacks recording (intentional). Magic Audio help page fetch for the overview timed out on one attempt; the apply-to-tracks article was retrieved via search snippet and is treated as official.

### 1.4 Cleanvoice AI

- **URL**: https://cleanvoice.ai/pricing ; https://cleanvoice.ai/filler-words/
- **Pricing (official, 2026-08-17)**: Free trial (filler page: 30 minutes, no card). PAYG: $11 / 5 h ($2.20/h), $20 / 10 h, $45 / 30 h; credits valid 2 years. Subscription: $11 / 10 h, $30 / 30 h, $90 / 100 h; unused credits roll over up to 3× plan limit. VAT extra. Billing by audio duration, 1-minute minimum, rounded up. Files stored 7 days then permanently deleted (pricing FAQ).
- **Local vs cloud**: Cloud upload required.
- **What it does**: Filler, silence, mouth sounds / breaths, noise, enhancer, video podcast editing, timeline export, transcription & summary. Filler languages officially listed: English, French, Romanian, German, Arabic. Accents mentioned: Irish, Australian, German. **Chinese is not listed.** Multi-track filler while keeping sync. Smart Remover inserts room noise after cuts.
- **Overlap**: silence/filler, denoise, transcripts, some notes.
- **Better**: dedicated filler / mouth-sound model; EDL/timeline export into Reaper, Audition, Premiere, Resolve, Audacity (described on Cleanvoice’s own site and on Castmagic’s Cleanvoice review; treat the official filler/pricing pages as primary for languages and pricing, and timeline-export as claimed on https://cleanvoice.ai/pricing “Timeline Export”).
- **This project**: local, per-op review, git recipe, no hour meter. Lacks mouth-sound / stutter models and Cleanvoice’s filler language pack (which also lacks Chinese).

### 1.5 Auphonic

- **URL**: https://auphonic.com/pricing ; https://auphonic.com/privacy ; https://auphonic.com/cli ; https://auphonic.com/blog/2026/03/26/auphonic-cli/ ; https://auphonic.com/blog/2026/04/15/automatic-video-cutting/ ; https://auphonic.com/help/resources/cli.html
- **Pricing (official, 2026-08-17)**: Free 2 h/month (jingle on free outputs; free credits do not stack). Recurring plans by hours: S 9 h, M 21 h, L 45 h, XL 100 h, XXL 250 h / month; unused recurring credits do not roll over. One-time credits from 5 h upward, never expire. **USD/EUR dollar amounts were not present in the fetched HTML** (toggle exists; numbers were not in the static extract). Paid features include multilingual speech recognition and automatic shownotes/chapters. CLI listed as available on Free and paid. Watch folders / batch on paid.
- **Local vs cloud**: Cloud processing on Hetzner DE and Cloudflare R2 (privacy policy). CLI is a local binary that **uploads** to the API (`auphonic process interview.wav --wait --download`). Privacy: Content “may be viewed and/or listened to by an Auphonic employee” to improve algorithms; productions deleted after announced retention (21 days audio, 7 days video/API) though excerpts may be kept for algorithm work.
- **What it does**: Leveler, noise/reverb, AutoEQ, loudness (EBU etc.), filler & silence cutting, cough/music cutters, ASR, auto shownotes/chapters, video, API, CLI, presets. Cut modes: apply cuts, set cuts to silence, or export uncut audio + cut lists. Editor: color-coded cuts, activate/deactivate, drag boundaries, reprocess at no extra credit.
- **Overlap**: almost the entire post-production pipeline except local-only processing and git-native recipes.
- **Better**: loudness/leveler reputation; cut-list interchange; CLI+API+presets; video cutting; no extra charge to re-run the same production.
- **This project**: no upload, no credit meter, `timeline.v1` as a file the user owns, offline dry-prompt notes. Lacks Auphonic’s leveler quality, cough/music cutters, and DAW cut-list export (not shipped).

### 1.6 Hindenburg PRO

- **URL**: https://hindenburg.com/products/hindenburg-pro ; shop: https://hindenburg.com/products/radio-podcast/ ; perpetual: https://hindenburg.com/products/radio-podcast/perpetual/
- **Pricing (official shop HTML, 2026-08-17)**: Personal Standard / Plus / Premium. Transcription hours: Standard 0, Plus 20, Premium 50 per month. Manuscript (edit audio like a word processor), video track, Soundly library (Premium = Premium Soundly). Monthly / yearly / perpetual purchase buttons rendered without visible dollar amounts in the fetched HTML. Perpetual page: one-time purchase; ongoing transcription requires subscription; 30 transcription hours for the first month then expire. **Dollar figures $12 / $99/year are not on the fetched official HTML**; they appear only in supplemental reviews.
- **Local vs cloud**: Local desktop DAW. Transcription is a metered cloud add-on per the perpetual page.
- **What it does**: Spoken-word DAW — record, transcribe, edit, montage, mix, publish. Auto-leveling and loudness are product claims on the marketing pages; exact algorithm list was not on the fetched HTML.
- **Overlap**: local spoken-word edit, transcript edit, leveling.
- **Better**: real multitrack DAW, undo history, field/journalism workflow.
- **This project**: free, scriptable, review-first automation, no seat license. Lacks DAW mixing (intentional).

### 1.7 SquadCast

- **URL**: https://squadcast.fm/ ; acquisition: https://www.descript.com/blog/article/descript-season-5-squadcast-joins-descript-easy-reliable-remote-recording-editing-in-one-place (2023-08-15)
- **Pricing**: Standalone SquadCast site still markets cloud recording. Current standalone dollar plans were not captured on 2026-08-17. Descript’s 2023 post: paying Descript subscribers get SquadCast; phase two would fold recording into Descript.
- **Local vs cloud**: Local capture + cloud backup (vendor claim on squadcast.fm).
- **What it does**: Remote multi-track recording. Not a post-production recipe tool.
- **Overlap**: none on edit recipes. Import target only.
- **Better**: recording reliability.
- **This project**: does not record (intentional).

### 1.8 Zencastr

- **URL**: https://zencastr.com/pricing
- **Pricing (official, 2026-08-17)**: Fetched page showed **Vibecastr Free** and **Enterprise Custom** only. Free column lists local recording, automatic cloud backups, unlimited separate tracks, unlimited postproduction credits, text-based editing, unlimited transcription hours, 100+ transcription languages, chapter / title / description generation, long-pause and advanced filler removal, normalize, noise removal, 4 seats, hosting. **Mid-tier paid prices were not on the fetched page.** Treat the Free feature list as vendor marketing; do not invent a $X Pro plan.
- **Local vs cloud**: Local recording + cloud backup (official table).
- **What it does**: Record + cloud edit + host + AI cleanup/notes.
- **Overlap**: filler/silence, notes, chapters, transcription.
- **Better**: recording + hosting bundle; claims 100+ transcription languages (list not expanded on the fetched page; **Taiwan Mandarin not verified**).
- **This project**: local post, no host, review recipe.

### 1.9 Castmagic

- **URL**: https://www.castmagic.io/pricing
- **Pricing (official, 2026-08-17)**: Annual: Hobby $19/mo ($239/yr) — 30 transcribed hours in library. Starter $48/mo ($579/yr) — 100 h. Team $139/mo ($1,669/yr) — 400 h, 5 seats. Business & Scale from $699/mo (page also shows $999/mo in one line). Hours are a growing library total; more hours can be bought. Languages FAQ lists “Mandarin (Simplified)” among 60+.
- **Local vs cloud**: Cloud upload.
- **What it does**: Transcription + show notes, chapters, clips, social, newsletter. **Not an audio editor.**
- **Overlap**: review-only show notes / chapters.
- **Better**: prompt library and repurposing volume.
- **This project**: notes stay review-only and can be dry-prompt / local. Lacks Castmagic’s template depth. Castmagic lacks cuts/denoise.

### 1.10 Wondercraft

- **URL**: https://www.wondercraft.ai/pricing
- **Pricing (official, 2026-08-17)**: Free $0 — 150 credits, 720p. Creator $25 monthly / $21 annual — 1,000 credits. Pro $45/mo — 2,000–6,000 credits, up to 3 users. Enterprise custom. Page copyright 2025.
- **Local vs cloud**: Cloud AI generation (voices, video, avatars).
- **What it does**: Generate podcast-like / video content with AI characters and voices. “Convo Mode (Editable NotebookLM Audio)” marketed on the pricing page.
- **Overlap**: none that this project wants (voice generation is out of scope).
- **Better**: generative show production.
- **This project**: edits real recordings; does not synthesize hosts.

### 1.11 Krisp

- **URL**: https://krisp.ai/pricing/
- **Pricing (official, 2026-08-17)**: Meeting AI — 7-day free trial. Core $16 / $8 per user/month (monthly / annual). Advanced $30 / $15. Enterprise custom; Enterprise lists “Private Transcription & Recordings (On-device)”. Call Center from $10 per agent/month annual. Noise cancellation is included in every Meeting plan.
- **Local vs cloud**: Desktop noise cancellation on the call path; notes/transcription are product-cloud except Enterprise on-device option.
- **What it does**: Real-time meeting noise cancellation, notes, accent conversion. Not a podcast timeline editor.
- **Overlap**: denoise only, and at record time rather than post.
- **Better**: live two-way NC.
- **This project**: post-production, offline, reviewable cuts.

### 1.12 Adobe Premiere Pro podcast-adjacent tools

- **URL**: Adobe Community announcements (official Adobe domain): Separate Crosstalk https://community.adobe.com/announcements-732/now-in-beta-separate-crosstalk-in-premiere-1634070 ; AI Assistant https://community.adobe.com/announcements-727/meet-your-new-assistant-editor-ai-assistant-in-premiere-pro-is-now-in-public-beta-1629317 ; Enhance Speech artifact threads listed in §3.
- **Pricing**: Creative Cloud subscription. Separate Crosstalk: 1 Generative Credit per second of audio, plus 2-second handles; clips 1 s–10 min. Official Premiere product-page fetch timed out on 2026-08-17.
- **Local vs cloud**: Desktop app; Firefly/partner models and credits are cloud.
- **What it does**: Full NLE. Enhance Speech in Essential Sound (community + Podcast Consultant supplemental). Beta: split two overlapping speakers + ambience; Assistant for bins/transcripts/rough cuts.
- **Overlap**: enhance, transcript-assisted edit, crosstalk.
- **Better**: video timeline, crosstalk experiment, industry interchange.
- **This project**: not an NLE. Should export into Premiere, not replace it.

### 1.13 Podcastle

- **URL**: https://www.podcastle.ai/pricing
- **Pricing**: Official pricing page **timed out twice** on 2026-08-17. **No current official dollar figures recorded this pass.** Do not reuse May-2026 $14.99 / $29.99 numbers as verified 2026-08 prices.
- **Local vs cloud**: Cloud studio (prior official positioning; not re-verified this pass beyond the URL existing).
- **What it does**: Record + edit + AI voices + cleanup (vendor category). Details not re-fetched.
- **Overlap / better / unique**: **Insufficient primary source this pass.**

### 1.14 ElevenLabs Studio (podcast-adjacent)

- **URL**: https://elevenlabs.io/studio ; https://elevenlabs.io/pricing
- **Pricing (official, 2026-08-17)**: Free $0 / 10k credits / 3 Studio projects. Starter $6 / 30k / 20 projects. Creator $22 ($11 first month) / 121k. Pro $99 / 600k. Scale $299 / 1.8M / 3 seats. Business $990 / 6M / 10 seats. Annual = 10 months. Shared credits: Voice Isolator 1,000 credits/minute; Speech-to-Text 330/min (FAQ).
- **Local vs cloud**: Cloud. Speech Correction uses AI voice cloning (official Studio page).
- **What it does**: Timeline editor for generated + recorded audio/video: TTS, music, SFX, captions, Voice Isolator, Speech Correction, Studio Agent. Markets “Podcasters: clean up dialogue… fix mistakes without re-recording”.
- **Overlap**: denoise (isolator), captions, transcripts.
- **Better**: generative repair and music.
- **This project**: explicitly not a voice cloner. Isolator quality is a denoise benchmark only.

### 1.15 Alitu

- **URL**: https://alitu.com/pricing/
- **Pricing (official, 2026-08-17)**: Comparison block: “Get it all with Alitu $32/m billed annually” and a sale line “$20.58/m billed annually (sale price)”. Hands-off editing service from $295/month. 7-day trial, 30-day refund, pause up to 3 months. Hosting free to 1,000 downloads/month, then $10 to 10,000. **Treat $32/m annual as the non-sale figure on the page; sale price is promotional.**
- **Local vs cloud**: Cloud. Page claims local backups for recording.
- **What it does**: Opinionated record + auto noise/level/EQ + Magic Filters (filler + silence) + text or waveform edit + AI shownotes + transcripts in 17 languages + publish/host.
- **Overlap**: beginner one-click cleanup + notes.
- **Better**: lowest-friction beginner path + hosting.
- **This project**: no host, no subscription, reviewable ops. Lacks Alitu’s “do it for me” service.

### 1.16 REAPER + SWS

- **URL**: https://www.reaper.fm/purchase.php (fetched 2026-08-17; page header “DOWNLOAD REAPER Version 7.79: August 17, 2026”); SWS: https://www.sws-extension.org/ ; https://github.com/reaper-oss/sws
- **Pricing / license**: REAPER discounted $60, commercial $225, 60-day full eval, free upgrades through 8.99. SWS/S&M: open-source plugin, latest stable v2.14.0 #7 (2025-09-07). GitHub **571 stars** (2026-08-17). SWS includes EBU R128 loudness tools (project wiki linked from sws-extension.org).
- **Local vs cloud**: 100% local.
- **What it does**: General DAW. ReaScript. SWS adds snapshots, loudness, marker actions, etc. No native ASR/filler AI.
- **Overlap**: local, scriptable, versionable project files.
- **Better**: mixing, plugins, infinite undo, industry standard for audio-first podcast pros.
- **This project**: opinionated spoken-word automation + review UI. Should export to REAPER (Auphonic already does EDL), not replace it.

### 1.17 iZotope RX 12

- **URL**: https://www.izotope.com/en/products/rx.html
- **Pricing (official, 2026-08-17)**: RX 12 Advanced **$1,399.00**. Standard / Elements prices not on the fetched Advanced page.
- **Local vs cloud**: Local app + DAW plugins (AU/AAX/VST3). Hosts listed include Reaper 7, Adobe Audition 2026, Premiere Pro 2026.
- **What it does**: Spectral repair, Dialogue Isolate, Repair Assistant, Scene Rebalance, Trim Silence, stems view. Manual + assist. Not a podcast recipe runner.
- **Overlap**: denoise, silence trim, dialogue isolate.
- **Better**: surgical repair quality; Repair Assistant proposes tweaks.
- **This project**: free automated review pipeline. Lacks RX-class repair. RX lacks git recipes and Chinese-first ASR.

### 1.18 Adobe Audition

- **URL**: https://www.adobe.com/products/audition.html
- **Pricing / features**: Official product page **timed out** on 2026-08-17. No primary feature/price table captured this pass. Audition is a Creative Cloud desktop DAW; RX 12 lists Audition 2026 as a supported host.
- **Local vs cloud**: Local editor; some Adobe AI features use cloud/credits (see Premiere community).
- **Overlap / better / unique**: **Insufficient primary source this pass.** Treat as the local pro editor this project should export toward, not compete with.

### 1.19 Resound (honorable — closest review UX)

- **URL**: https://www.resound.fm/ ; https://www.resound.fm/pricing
- **Pricing (official, 2026-08-17)**: Free $0 — 20 min/month, MP3, 1 track, 1-day storage. Creator $15 — 4 h, WAV/AAF/MP4, 2 tracks, 15-day storage, Enhance. Studio $60 — 30 h, 4 tracks, 60-day storage, API.
- **Local vs cloud**: Cloud upload.
- **What it does**: Detect filler sounds and silences >3 s; user **Cut or Keep** each item; preview; Enhance mix/master; export merged or per-track. Roadmap on homepage: repeat detection, filler *words*, video, stutters (not claimed as shipped).
- **Overlap**: per-edit accept/reject — the closest commercial UX to this project’s dashboard.
- **Better**: polished cut/keep UI; AAF for DAW round-trip.
- **This project**: local, unlimited, `timeline.v1` + recovery map + git. Lacks Resound’s filler-sound model and AAF export.

---

## 2. Open-source / GitHub projects

Star counts from the GitHub repository page on 2026-08-17 unless noted.

### 2.1 WyattBlue/auto-editor

- **URL**: https://github.com/WyattBlue/auto-editor — **4,984 stars**
- **License**: Unlicense / public domain (https://github.com/WyattBlue/auto-editor/blob/master/LICENSE). Repo README (via search extract): online app at app.auto-editor.com uses repo assets (Unlicense) plus separate proprietary assets.
- **Local vs cloud**: Local CLI; optional proprietary web app.
- **What it does**: Automatic silence/motion-based recut of video/audio. Not a review dashboard; not a podcast chapter/notes tool.
- **Overlap**: local silence cutting.
- **Better**: mature CLI, huge user base, video-first.
- **This project**: review-before-ship, `timeline.v1`, transcripts/chapters/notes, LUFS gates, 繁中 path. Lacks auto-editor’s years of edge-case cutting.

### 2.2 Auphonic-related OSS

- **auphonic/auphonic-mobile**: https://github.com/auphonic/auphonic-mobile — **48 stars**. Old mobile web app. Not the 2026 CLI.
- **Auphonic CLI**: https://auphonic.com/cli — **not OSS**. Closed binary wrapping the cloud API (blog 2026-03-26).
- **auphonic-api-examples**: listed on https://github.com/auphonic (21 stars in org extract). API samples, not a local engine.
- **Implication**: there is no open Auphonic leveler to vendor.

### 2.3 Whisper family and diarization

| Project | URL | Stars (2026-08-17) | License (primary) | Role |
|---|---|---|---|---|
| openai/whisper | https://github.com/openai/whisper | 107,437 | MIT (`LICENSE` raw) | Reference ASR; includes Chinese among trained languages (model card / paper; this pass did not re-fetch the language table) |
| ggml-org/whisper.cpp | https://github.com/ggml-org/whisper.cpp | 52,956 | MIT (`LICENSE` raw) | Local C/C++ ASR |
| SYSTRAN/faster-whisper | https://github.com/SYSTRAN/faster-whisper | 24,956 | MIT (`LICENSE` raw) | Fast local ASR |
| m-bain/whisperX | https://github.com/m-bain/whisperX | 23,610 | License file **not retrieved** this pass | Word timestamps + alignment + pyannote diarization |
| pyannote/pyannote-audio | https://github.com/pyannote/pyannote-audio | 10,429 | License file **not retrieved** this pass | Diarization building blocks; typical use needs HF token / model terms |

- **Local vs cloud**: Local weights. pyannote models often require accepting Hugging Face terms (not re-fetched).
- **Overlap**: this project’s `transcribe` boundary; CLI default remains `stub` (`cli.py`).
- **Better**: actual ASR quality when the operator installs weights.
- **This project**: `transcript.v1` plus remapping through the recovery map. Real adapters already exist on `dev`: `faster-whisper-local`, `whisper-cpp-local`, `qwen3-asr-local` (`podcast_auto_editor/asr.py`). They are optional extras; quickstart still uses `stub`. Chinese-specific models are documented in `docs/research/2026-05-17-chinese-asr-models.md` (Qwen3-ASR Taiwan Mandarin CV-zh-tw WER 3.77 on the Qwen model card cited there).

### 2.4 Loudness CLIs

| Project | URL | Stars | License | Role |
|---|---|---|---|---|
| slhck/ffmpeg-normalize | https://github.com/slhck/ffmpeg-normalize | 1,527 | LICENSE raw **404** this pass | ffmpeg loudness normalize wrapper |
| Moonbase59/loudgain | https://github.com/Moonbase59/loudgain | 228 | BSD-2 (man page in repo) | ReplayGain 2.0 / R128 tagger; does not rewrite audio |
| desbma/r128gain | https://github.com/desbma/r128gain | 171 | LGPLv2.1 (repo LICENSE); **archived** | Scanner/tagger |

- **Overlap**: this project already renders with LUFS / true-peak gates (README).
- **Better**: battle-tested measure/tag tools.
- **This project**: should compare numbers against ffmpeg-normalize / Auphonic, not reimplement tagging.

### 2.5 bbc/audiowaveform

- **URL**: https://github.com/bbc/audiowaveform — **2,157 stars**
- **License**: not fetched this pass (BBC project; typically GPL-3 — **do not treat as verified**).
- **What it does**: Waveform data + PNG from audio. Review-UI building block, not an editor.
- **Overlap**: dashboard preview.
- **This project**: can reuse waveform peaks; does not need to own a renderer.

### 2.6 Podlove and Opencast

- **podlove/podlove-publisher**: https://github.com/podlove/podlove-publisher — **309 stars**. WordPress publisher: chapters, web player, feeds. **Not an editor.**
- **opencast/opencast**: https://github.com/opencast/opencast — **497 stars**. Campus lecture capture/distribution. **Not a laptop podcast editor.**

### 2.7 Local podcast / silence / filler tools (2026 GitHub)

| Project | URL | Stars | What it claims | vs this project |
|---|---|---|---|---|
| trsdn/autocut | https://github.com/trsdn/autocut | 2 | Local CLI: Parakeet/whisper.cpp, silence+filler, optional LLM, EBU −16 LUFS, `--dry-` | Closest OSS *pipeline* cousin; no review UI; English/German flags in README extract |
| dennisrongo/cut-clean | https://github.com/dennisrongo/cut-clean | 3 | Local desktop; Whisper; toggle fillers/silences; **English fillers; MP4 only; max 15 min / 1 h project** | Review toggles; video-first; duration cap |
| whyaang/Bowdler | https://github.com/whyaang/Bowdler | 23 | Local Apple Silicon; transcript edit; **$49 once** (README extract, prices “as of April 2026”) | Paid local app; 32 languages claimed |
| electronicbrains/poddie | https://github.com/electronicbrains/poddie | 0 | Local Mac; delete words to cut; local Whisper or OpenAI API | Text-edit UX; no git recipe |
| b2bvic/declip | https://github.com/b2bvic/declip | 7 | Apple Silicon CLI; fillers; retakes; dry-run default; optional Resemble Enhance | Dry-run culture matches this project; video/talking-head |

None of these advertise a git-checkable `timeline.v1` + recovery map + LUFS publish gates + 繁中-first policy.

### 2.8 Local Enhance alternatives

| Project | URL | Stars | License | Role |
|---|---|---|---|---|
| Rikorose/DeepFilterNet | https://github.com/Rikorose/DeepFilterNet | 4,604 | Apache-2.0 OR MIT (`LICENSE` raw) | Local neural noise suppression |
| xiph/rnnoise | https://github.com/xiph/rnnoise | 5,783 | COPYING **not retrieved** this pass (historically BSD-style) | Classic local RNNoise |
| resemble-ai/resemble-enhance | https://github.com/resemble-ai/resemble-enhance | 2,396 | License **not retrieved** | Local speech denoise/enhance |
| modelscope/ClearerVoice-Studio | https://github.com/modelscope/ClearerVoice-Studio | 4,414 | License **not retrieved** | Enhancement / separation / TSE toolkit |

- **Overlap**: planned/local denoise vs Adobe Enhance.
- **This project**: no shipped Enhance-class model. DeepFilterNet is the smallest honest local experiment.

### 2.9 Chapter / show-notes generators

- **FanaHOVA/smol-podcaster**: https://github.com/FanaHOVA/smol-podcaster — **412 stars**. Diarized transcript, chapters, titles, tweets; OpenAI + Claude; “Edit Show Notes” merge UI. Cloud LLM. Used by Latent Space (README).
- **jamesmontemagno/podcast-metadata-generator**: https://github.com/jamesmontemagno/podcast-metadata-generator — stars **not fetched**. Copilot-SDK titles/descriptions/chapters/SRT from transcripts.
- **AlperNab/podcast-show-notes**: https://github.com/AlperNab/podcast-show-notes — stars **not fetched**. Browser workflow; local engine + optional LLM.
- **AssemblyAI auto chapters + LeMUR**: cloud API (https://www.assemblyai.com — full pricing not fetched). Not local.
- **podcast2**: **no primary source found** for a project of that name that generates chapters/show notes.
- **Listen Notes**: https://www.listennotes.com/api/ — podcast **directory/search API** (3,799,596 shows / 192,228,674 episodes on the page). Not an editor. Listener.com is listed as a customer that generates titles/descriptions/notes — that is a third-party app, not Listen Notes itself.

---

## 3. User pain (cited URLs only)

Focus: upload privacy, subscription, false cuts, Chinese/Taiwan Mandarin, reviewability, reproducibility.

### 3.1 Upload / privacy

- **Descript stores the project on their servers** (files, transcripts, metadata). https://www.descript.com/security — accessed 2026-08-17. Opt-in to share transcripts to improve algorithms (off by default). Custom Voice audio is used to improve the service.
- **Auphonic** may have employees listen to Content to improve algorithms; may keep excerpts after production deletion. https://auphonic.com/privacy — accessed 2026-08-17. EU servers (Hetzner) + Cloudflare R2.
- **Cleanvoice** keeps original + edited files **7 days**, then permanent delete. https://cleanvoice.ai/pricing FAQ — accessed 2026-08-17.
- **Krisp** claims meeting data is not used to train models; Enterprise offers on-device transcription. https://krisp.ai/pricing/ — accessed 2026-08-17.
- Reddit upload-privacy threads: **no primary source found this pass.**

### 3.2 Subscription / metering

- Descript: two meters (media hours + AI credits); top-ups on Creator/Business. https://www.descript.com/pricing
- Riverside: separate-track **download** hours, not record hours; AI credit pack for some features. https://riverside.com/pricing FAQ
- Cleanvoice / Auphonic / Castmagic / Resound / ElevenLabs / Adobe Podcast: hour or credit or daily caps (see §1).
- REAPER remains one-time $60 / $225. https://www.reaper.fm/purchase.php
- Reddit “credits ran out” threads: **no primary source found this pass.**

### 3.3 False cuts / destructive enhance / reviewability

- **Adobe Community — robotic / garbled Enhance**: https://community.adobe.com/questions-544/enhance-causing-robotic-voice-163859 ; https://community.adobe.com/bug-reports-328/enhance-audio-is-producing-garbled-results-1558150
- **Adobe Community — Enhance changes words**: https://community.adobe.com/questions-729/enhance-speech-is-way-off-completely-changing-words-via-the-faulty-ai-library-1408577
- **Adobe Community — hallucinations in silence**: https://community.adobe.com/bug-reports-728/essential-sound-enhance-speech-dialogue-tool-hallucinations-1330744
- **Adobe Community — echo / doubled audio**: https://community.adobe.com/bug-reports-733/enhance-speech-causing-audio-artifact-906741
- **Auphonic** added activate/deactivate per cut after complaints that headless processors are one-shot — inferred product response; the *feature* is primary (https://auphonic.com/blog/2026/04/15/automatic-video-cutting/). User complaint URLs for Auphonic over-cut: **no primary source found this pass.**
- **Resound** FAQ heading “Does Resound cut out content automatically or do I have control?” exists on https://www.resound.fm/pricing (answer body not extracted). Homepage: “Stay in control by reviewing each edit, selecting cut or keep”.
- **G2** review pages were not successfully fetched as quoteable primary text this pass (marketplace stubs only). One G2 Learn article quotes a Descript user wanting filler removed from captions but not from A/V: https://learn.g2.com/free-audio-editing-software

### 3.4 Chinese / Taiwan Mandarin

- Descript official transcription language list: **no Chinese**. https://www.descript.com/pricing
- Cleanvoice official filler languages: EN, FR, RO, DE, AR. **no Chinese**. https://cleanvoice.ai/filler-words/
- Adobe Podcast March 2026 notes site/Studio languages: French, German, Italian, Spanish, Portuguese, English (plus other site locales). **Traditional Chinese / Taiwan Mandarin not listed.** https://podcast.adobe.com/en/guides/latest-updates (older Feb 2025 notes) and March 2026 what’s-new (no zh-TW).
- Castmagic FAQ: Mandarin **Simplified** in 60+ languages. https://www.castmagic.io/pricing — not Taiwan Mandarin, and not an editor.
- Local ASR evidence for 繁中: `docs/research/2026-05-17-chinese-asr-models.md` citing Qwen3-ASR model card (Taiwan Mandarin CV-zh-tw WER 3.77 for 1.7B). That is the load-bearing Chinese path, not a cloud editor.

### 3.5 Reproducibility

- No commercial official page fetched this pass advertises a git-checkable edit recipe equivalent to `timeline.v1`.
- Closest: Auphonic presets + API/CLI + cut-list export; Cleanvoice timeline/EDL export; REAPER project files; Descript timeline export to several DAWs (pricing table: Samplitude, Reaper, FCP, Pro Tools, Logic, Audition, Premiere).
- Cloud project files remain on the vendor (Descript security page).

---

## 4. Comparison matrix (2026-08-17)

Legend: + native / strong; ~ partial; — absent; $ metered add-on. “Our tool” = Podcast Auto Editor as specified in README (2026-08 working tree).

| Feature | Descript | Adobe Pod | Riverside | Cleanvoice | Auphonic | Castmagic | Hindenburg | Resound | REAPER | auto-editor | ElevenLabs Studio | **This project** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Filler removal | + | — | + | + | + | — | ~ | + (sounds; words roadmap) | — | — | — | ~ (silence; speech cuts review-only) |
| Silence trim | + | ~ | + | + | + | — | + | + | ~ | + | — | + |
| Mouth sounds | ~ | — | ~ | + | ~ | — | — | ~ | — | — | — | — |
| Denoise | + | + | + (Magic Audio) | + | + | — | + | + | $ plugins | — | + (Isolator) | — (not shipped) |
| Loudness leveler | ~ | — | ~ | + | + | — | + | + | ~ / SWS | — | — | + (LUFS/TP gates) |
| Auto chapters | + | — | + | — | + $ | + | ~ | — | — | — | — | + (review) |
| Show notes | + | — | + | + | + $ | + | — | — | — | — | — | + (review / dry-prompt) |
| Transcription | + (no zh listed) | + | + | + | + $ | + (zh-CN listed) | $ | + | — | — | + | stub default; real adapters optional |
| Text-delete edit | + | + (Studio) | + | — | — | — | + | — | — | — | + (generated speech) | — |
| Per-edit review | ~ | — | ~ | ~ (report / EDL) | + (Editor 2026) | — | + (DAW) | + | + | — | ~ | **+** |
| Git-checkable recipe | — | — | — | — | ~ (presets/API) | — | — | — | ~ (project) | ~ (CLI flags) | — | **+ (artefact)** |
| 100% local | — | — | — | — | — | — | ~ (ASR cloud) | — | + | + | — | **+** |
| No upload | — | — | — | — | — | — | + for edit | — | + | + | — | **+** |
| CLI | — | — | — | API | + (uploads) | API | ~ | — | + | + | API | **+** |
| Subscription floor | $16/mo ann. | Premium $ not on HTML | $24/mo ann. | $11/mo | 2 h free then paid | $19/mo ann. | $ not on HTML | $15/mo | $60 once | free (CLI) | $6/mo | **free** |

Podcastle, Audition, Premiere: omitted from the grid because official pages were not fully fetched.

---

## 5. Synthesis — implications for this project

Each item: gap, competitor that proves it matters, smallest next experiment.

These experiments are **Phase 2 candidates**. They do not replace the Phase 1 real-episode run in `docs/plans/2026-08-17-adjustment-and-next.md`. Run at most one after that fix-log names the blocker.

1. **Cut-list interchange is now expected.**  
   **Gap**: `timeline.v1` is internally excellent and externally invisible.  
   **Proves it**: Auphonic exports EDL / FCPXML / Reaper / Audacity / Audition cut lists (https://auphonic.com/blog/2026/04/15/automatic-video-cutting/). Cleanvoice lists Timeline Export. Descript lists DAW timeline export.  
   **Smallest experiment**: emit a Reaper-region EDL (or Auphonic-shaped cut list) from one accepted `timeline.v1` and import it into REAPER. Success = regions land on the right ranges. Do not build a DAW.

2. **Per-cut review is no longer a unique *category*.**  
   **Gap**: Resound (cut/keep) and Auphonic Editor (activate/deactivate, drag bounds, free reprocess) already sell review.  
   **Proves it**: https://www.resound.fm/ and Auphonic 2026-04-15 blog.  
   **Smallest experiment**: time a producer reviewing 40 proposed silence+speech ops in this project’s dashboard vs the same ops as a printed cut list. If dashboard time is not clearly lower, the next UI change is batch-keep-by-type + waveform context, not more copy.

3. **Taiwan Mandarin / 繁中 is still a vacuum in commercial editors.**  
   **Gap**: Descript’s official 25-language list has no Chinese; Cleanvoice fillers omit Chinese; Adobe Podcast what’s-new does not list zh-TW.  
   **Proves it**: https://www.descript.com/pricing ; https://cleanvoice.ai/filler-words/  
   **Smallest experiment**: one 60-minute 繁中 episode through Qwen3-ASR 1.7B vs Whisper large-v3 (protocol already in `docs/research/2026-05-17-chinese-asr-models.md`). Metric: WER/CER on a 5-minute hand transcript + whether chapter drafts are usable. This is the continue/adjust decision for ASR, not a platform rewrite.

4. **Enhance-class denoise is the feature users will compare in 10 seconds.**  
   **Gap**: this project has no shipped neural enhance. Adobe Enhance + community artifact threads show both demand and failure modes (robot, word change, hallucinated speech).  
   **Proves it**: Adobe plans + https://community.adobe.com/questions-729/enhance-speech-is-way-off-completely-changing-words-via-the-faulty-ai-library-1408577  
   **Smallest experiment**: DeepFilterNet vs RNNoise vs unprocessed on a 10-minute noisy 繁中 clip. Output = A/B files + a one-page listen note. Do not upload guest audio to Adobe for the first run if consent is unclear.

5. **Filler/mouth-sound models are still Cleanvoice’s moat; English-only OSS fillers will fail 繁中.**  
   **Gap**: silence-only automation under-serves “嗯 / 啊 / 那個”. Cleanvoice does not list Chinese. CutClean/declip document English lexicons.  
   **Proves it**: https://cleanvoice.ai/filler-words/ ; CutClean README (English fillers).  
   **Smallest experiment**: word-timestamp lexicon detector for 嗯/啊/呃/那個 on one 繁中 transcript, propose `timeline.v1` ops at `proposed` only, measure false-cut rate against a human keep/cut list of 50 items.

6. **Text-delete-to-cut is what people pay Descript for; do not clone the DAW, clone the *word toggle*.**  
   **Gap**: imported `transcript.v1` is not yet a cutting surface.  
   **Proves it**: Descript “edit like a doc”; Adobe Studio “edit audio like a doc”; Hindenburg Manuscript; Poddie/Bowdler/CutClean.  
   **Smallest experiment**: in the existing review UI, clicking a transcript cue toggles the overlapping operation. No new editor chrome.

7. **Metering is still the conversion story; Auphonic’s CLI does not remove the upload or the hour cap.**  
   **Gap**: README comparison table still cites May-2026 prices; several 2026-08 official numbers moved (Castmagic, Resound, Riverside plan names).  
   **Proves it**: official pricing URLs in §1.  
   **Smallest experiment**: one calculator page in the research folder (or README footnote later) for “4 × 90-minute episodes / month” using only 2026-08-17 official numbers: Descript Hobbyist 10 h + 400 credits; Riverside Pro 15 h separate-track downloads; Cleanvoice $11 / 10 h; Auphonic 2 h free + next recurring tier hours; Resound Creator 4 h; Adobe free 1 h/day. No invented Adobe Premium dollar.

8. **Do not chase recording, cloning, or publishing.**  
   **Gap**: none — these remain correctly out of scope.  
   **Proves it**: Riverside/SquadCast/Zencastr own recording; ElevenLabs Studio Speech Correction is cloning; Castmagic/Listen Notes own distribution-adjacent text.  
   **Smallest experiment**: none. Keep import-from-Riverside as the integration story.

---

## 6. What this project should not change based on this pass

- Do not add voice cloning because ElevenLabs and Descript sell it.
- Do not add RSS/hosting because Alitu and Riverside bundle it.
- Do not become a DAW because REAPER + Hindenburg + RX exist and Auphonic already hands them cut lists.
- Do not treat tiny-star OSS (autocut, Poddie, CutClean) as market proof of UX — they prove demand for *local*, not a finished product.

---

## Sources (accessed 2026-08-17 unless dated on the page)

### Official commercial

- https://www.descript.com/pricing
- https://www.descript.com/security
- https://riverside.com/pricing
- https://support.riverside.com/hc/en-us/articles/15079835638301-Magic-Audio-tracks-Overview
- https://support.riverside.com/hc/en-us/articles/13395368921885-Apply-Magic-Audio-to-individual-tracks-in-the-editor
- https://cleanvoice.ai/pricing
- https://cleanvoice.ai/filler-words/
- https://auphonic.com/pricing
- https://auphonic.com/privacy
- https://auphonic.com/cli
- https://auphonic.com/blog/2026/03/26/auphonic-cli/
- https://auphonic.com/blog/2026/04/15/automatic-video-cutting/
- https://auphonic.com/help/resources/cli.html
- https://podcast.adobe.com/en
- https://podcast.adobe.com/enhance
- https://podcast.adobe.com/en/plans
- https://podcast.adobe.com/en/guides/whats-new-in-adobe-podcast-march-2026
- https://www.castmagic.io/pricing
- https://hindenburg.com/products/hindenburg-pro
- https://hindenburg.com/products/radio-podcast/
- https://hindenburg.com/products/radio-podcast/perpetual/
- https://www.wondercraft.ai/pricing
- https://krisp.ai/pricing/
- https://alitu.com/pricing/
- https://zencastr.com/pricing
- https://www.resound.fm/
- https://www.resound.fm/pricing
- https://www.reaper.fm/purchase.php
- https://www.sws-extension.org/
- https://www.izotope.com/en/products/rx.html
- https://elevenlabs.io/studio
- https://elevenlabs.io/pricing
- https://squadcast.fm/
- https://www.descript.com/blog/article/descript-season-5-squadcast-joins-descript-easy-reliable-remote-recording-editing-in-one-place
- https://www.listennotes.com/api/
- https://www.podcastle.ai/pricing (fetch timed out)
- https://www.adobe.com/products/audition.html (fetch timed out)
- https://helpx.adobe.com/premiere-pro/using/enhance-speech.html (fetch timed out / 404)

### Official community (Adobe)

- https://community.adobe.com/announcements-732/now-in-beta-separate-crosstalk-in-premiere-1634070
- https://community.adobe.com/announcements-727/meet-your-new-assistant-editor-ai-assistant-in-premiere-pro-is-now-in-public-beta-1629317
- https://community.adobe.com/questions-544/enhance-causing-robotic-voice-163859
- https://community.adobe.com/bug-reports-328/enhance-audio-is-producing-garbled-results-1558150
- https://community.adobe.com/questions-729/enhance-speech-is-way-off-completely-changing-words-via-the-faulty-ai-library-1408577
- https://community.adobe.com/bug-reports-728/essential-sound-enhance-speech-dialogue-tool-hallucinations-1330744
- https://community.adobe.com/bug-reports-733/enhance-speech-causing-audio-artifact-906741

### GitHub (stars from repo page 2026-08-17)

- https://github.com/WyattBlue/auto-editor
- https://github.com/openai/whisper
- https://github.com/ggml-org/whisper.cpp
- https://github.com/SYSTRAN/faster-whisper
- https://github.com/m-bain/whisperX
- https://github.com/pyannote/pyannote-audio
- https://github.com/slhck/ffmpeg-normalize
- https://github.com/Moonbase59/loudgain
- https://github.com/desbma/r128gain
- https://github.com/bbc/audiowaveform
- https://github.com/Rikorose/DeepFilterNet
- https://github.com/xiph/rnnoise
- https://github.com/resemble-ai/resemble-enhance
- https://github.com/modelscope/ClearerVoice-Studio
- https://github.com/opencast/opencast
- https://github.com/podlove/podlove-publisher
- https://github.com/auphonic/auphonic-mobile
- https://github.com/reaper-oss/sws
- https://github.com/FanaHOVA/smol-podcaster
- https://github.com/trsdn/autocut
- https://github.com/dennisrongo/cut-clean
- https://github.com/whyaang/Bowdler
- https://github.com/electronicbrains/poddie
- https://github.com/b2bvic/declip

### Supplemental (not used for prices/stars)

- https://www.castmagic.io/software-review/cleanvoice-ai
- https://learn.g2.com/free-audio-editing-software
- https://thepodcastconsultant.com/blog/adobe-podcast-enhance
- https://www.creatorstackclub.com/software/hindenburg
- Prior survey: `docs/research/2026-05-17-competitor-landscape.md`
- Chinese ASR: `docs/research/2026-05-17-chinese-asr-models.md`
