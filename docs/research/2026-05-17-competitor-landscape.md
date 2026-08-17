# Competitor Landscape — Podcast Auto-Editing Tools (2025–2026)

Date: 2026-05-17
Scope: 13 commercial / open-source podcast editing & automation tools.
Lens: What end-users actually complain about, and where a **local-first, review-first, CLI + local web dashboard** tool can credibly differentiate.
Sources: 2025–2026 vendor docs, Reddit r/podcasting, G2, Capterra, Trustpilot, vendor changelogs, third-party reviews. Source list at the end of this document.

This research informs `docs/plans/2026-05-17-persona-ab-stage1.md`.

**Errata (2026-08-17):** The feature matrix in this file marked this project as shipping denoise via RNNoise/Demucs. That row is wrong; there is no denoise module in `podcast_auto_editor/`. Use `docs/research/2026-08-17-competitor-landscape.md` for current pricing and the corrected matrix.

---

## 1. Competitor Cards

### 1.1 Descript
- **Core positioning**: Text-based audio/video editor — "edit by deleting words in a transcript".
- **AI features**: Filler removal (Edit for Clarity), Studio Sound (denoise+dereverb), Overdub (voice clone), Underlord (multi-step AI co-editor, Aug 2025), AI Speakers, auto chapters, captions, "polish for YouTube" agent.
- **Editing model**: Text-based + multitrack timeline. Non-destructive in principle (delete/ignore are reversible, "restore removed media"), but **users widely report undo gaps** ("no way to undo if you press the wrong button").
- **Privacy**: Cloud-only, project files synced to Descript servers; voice cloning runs server-side; transcripts stored in cloud.
- **Pricing (Sept 2025 overhaul)**: Free / Hobbyist $16 / Creator $24 / Business $50 (annual, per user). Switched from "transcription hours" to **metered media-minutes + AI credits** for Studio Sound / Overdub.
- **Top complaints**: Sept-2025 repricing — long-time $30/mo customers seeing "hundreds" once team busts the new media-minute pool; AI credits depleted fast; app slow/laggy on long files; Rooms buggy; filler removal sometimes deletes wanted content; Overdub vocab-locked at 1,000 words on lower tiers.
- **Differentiator**: The most polished text-based editing UX + Underlord agent that chains edits.

### 1.2 Adobe Podcast (incl. Enhance)
- **Core positioning**: Free-tier AI speech enhancer + simple browser editor.
- **AI features**: Enhance Speech (denoise + dereverb), Enhance Speech v2, Mic Check, basic transcription, auto cuts. No filler removal at the polished tier of Cleanvoice/Descript.
- **Editing model**: Lightweight web editor; processing is **destructive on export** (one-way enhancement, no diff/undo of the AI's choices). Strength is locked at 100% on web.
- **Privacy**: Cloud-only (browser). Files uploaded to Adobe.
- **Pricing**: Free tier, 30 min/file, ~1 hr/day cap. Paid bundling via CC.
- **Top complaints**: Sibilant (S/T) artifacts → lisp; over-processed voice when noise > voice → "robot" effect; can't separate bleed on a single shared mic; no strength slider on web; thin editing toolset.
- **Differentiator**: Best free denoise quality on the market; zero learning curve.

### 1.3 Riverside.fm
- **Core positioning**: Remote multi-host recording (local capture + cloud sync) → Magic Editor for post.
- **AI features**: Magic Editor (text-based edits), Magic Clips (auto short-form), AI show notes, transcription, automatic cleanup.
- **Editing model**: Cloud timeline + text editing. Non-destructive within project, but **edits and transcripts live on Riverside servers**.
- **Privacy**: Local capture, **but auto-uploads in real time during recording**; project storage cloud-only.
- **Pricing**: Pro $24 / Live $34 / Webinar $79 per month; annual ~35% discount.
- **Top complaints**: Magic Editor sluggish, lacks flexibility for nuanced edits; Magic Clips audio/video misalignment (wrong speaker on screen); features like virtual background / faster render gated to higher plans; sync glitches, missing files, app crashes during sessions.
- **Differentiator**: Best-in-class remote multi-track recording; SquadCast tech now inside Descript dilutes this edge.

### 1.4 Podcastle
- **Core positioning**: All-in-one cloud studio (record + edit + AI voices + publish) for solo/SMB creators.
- **AI features**: Magic Dust (audio cleanup), filler/silence removal, AI text-to-speech voices, transcription, voice cloning, video enhance / cinematic blur / eye contact (Business).
- **Editing model**: Cloud multitrack + text-based. Reversible inside project; AI cleanup applied as transform, no fine-grained per-edit diff.
- **Privacy**: Cloud-only, browser-based, internet-dependent.
- **Pricing**: Free (3hr video + 1hr transcription, watermark) / Storyteller $14.99 / Pro $29.99 / Business $39.99 — heavy metering on transcription hours and TTS chars.
- **Top complaints**: Bugs during record/edit (unsynced audio, frozen files, lost sessions, bad waveforms); noise reduction sometimes makes audio worse; voice clone inconsistent; storage caps (5GB Storyteller); imported clean audio sometimes degraded.
- **Differentiator**: Cheapest "everything-in-one" with TTS voices.

### 1.5 Cleanvoice AI
- **Core positioning**: Headless audio cleanup API/web — fillers, mouth sounds, stutters, long pauses removed automatically.
- **AI features**: Filler removal (20+ types, 20+ languages), mouth-sound removal, stutter/repetition removal, silence trim, basic loudness. **Not** an editor — output is a cleaned file.
- **Editing model**: **Destructive on output**: returns a new audio file. Has a report listing detected items, but no per-edit interactive accept/reject inside a multitrack editor.
- **Privacy**: Cloud upload required (EU-hosted, GDPR-friendly per their marketing).
- **Pricing**: Free trial 30 min; PAYG $11 / 5 hr (2-yr validity); subs $11/mo (10hr) → $90/mo (100hr) with rollover.
- **Top complaints**: Over-aggressive cuts → choppiness on long episodes; rule-based, no taste/style adaptation; no real editor; no podcast hosting; limited file format support; no judgment on tone/pacing.
- **Differentiator**: Highest-quality dedicated filler/mouth-sound model in the market; PAYG credits don't expire fast.

### 1.6 Auphonic
- **Core positioning**: Best-in-class loudness leveler + mastering engine for podcasters.
- **AI features**: Adaptive Leveler (multi-speaker balance), noise/hum reduction, loudness normalization (EBU/ATSC/Spotify), filler/silence cuts (newer), speech-to-text (multiple engines incl. Whisper), auto chapters via cue points.
- **Editing model**: Process pipeline, not an editor. Destructive output file. Repeatable presets/watch folders.
- **Privacy**: Cloud-based (web), EU servers (Hetzner DE / Cloudflare R2 EU). Older "Auphonic Leveler" desktop app exists for Mac/Win but has narrower feature set.
- **Pricing**: 2 hr/mo free; subs $13/9hr → $119/100hr; one-time credits from $12/5hr (no expiry).
- **Top complaints**: Leveler occasionally gives "bad output" requiring redo; no interactive editor / no per-edit diff; UI dated; cloud round-trip overhead; web-only for full feature set.
- **Differentiator**: Loudness/leveling quality + non-expiring credits; the workflow tool serious solo podcasters quietly stick with.

### 1.7 Castmagic
- **Core positioning**: Post-recording "content multiplier" — feed audio in, get show notes / chapters / clips / social posts / newsletter out.
- **AI features**: Transcription, summarization, show-notes, timestamped chapters, social asset generation, repurposing templates.
- **Editing model**: **Not an audio editor.** Generates text/asset artefacts only.
- **Privacy**: Cloud-only, audio uploaded.
- **Pricing**: Hobby $39/mo (200 min) / Starter $99/mo (500 min) / Rising Star $299/mo (1500 min); annual ~40% off.
- **Top complaints**: Output still needs human pass; minute caps restrictive; high price for casual users; weak accent/technical-term accuracy; export is copy-paste / CSV — no real integrations to hosts; can't push back to Spotify/Apple programmatically.
- **Differentiator**: Strongest content-repurposing prompts; saves hours on show notes.

### 1.8 Hindenburg Pro
- **Core positioning**: DAW built for spoken-word/journalism — auto-leveling baked in.
- **AI features**: Auto leveler, loudness normalization, voice profiler, noise reduction, EQ presets, transcription (paid extra), text-based editing of transcript.
- **Editing model**: Non-destructive multitrack DAW (clips + regions + history). True undo, true timeline.
- **Privacy**: Local desktop app (Mac/Win). Transcription is cloud-paid (extra hours required).
- **Pricing**: $12/mo monthly or $99/yr ($8.25/mo). One license per user, max 2 machines.
- **Top complaints**: Transcription not free even with perpetual license; no license sharing; learning curve vs Descript-style text editing; UI feels traditional-DAW; field-recorder workflow excellent but niche.
- **Differentiator**: One of the few **actually local** spoken-word DAWs with real auto-leveler; predictable file ownership.

### 1.9 Resound.fm
- **Core positioning**: Lightweight AI cleanup with **per-edit accept/reject**.
- **AI features**: Filler detection, silence trim, AI Enhance (mix/master).
- **Editing model**: Each suggested cut is reviewable — **"cut" or "keep" per item**. This is the closest competitor to a "diff/review" model.
- **Privacy**: Cloud upload.
- **Pricing**: Free 1hr/mo; paid from $12/mo.
- **Top complaints**: Smaller surface area vs Descript; cloud-only; doesn't replace a full editor.
- **Differentiator**: The **"review each edit" UX is the rare one** in this market — most others apply changes globally.

### 1.10 Reaper (DAW + podcast workflow)
- **Core positioning**: General-purpose DAW used heavily by podcast pros (Marco Arment's setup, etc.).
- **AI features**: None native; relies on plugins (RX, FabFilter) or external Whisper for transcription.
- **Editing model**: Fully non-destructive, project-file-based (~360KB vs Audacity's ~3GB), real undo history, version control friendly.
- **Privacy**: 100% local. Files never leave disk unless you do it.
- **Pricing**: $60 personal license (one-time, very generous trial).
- **Top complaints**: Steep learning curve; no built-in AI; no text-based editing; podcast-specific niceties (auto-leveler, chapter export) require custom scripts/plugins.
- **Differentiator**: Best price/perf, totally local, infinitely scriptable (ReaScript) — a serious template for what local-first can be at the editor layer.

### 1.11 Audacity
- **Core positioning**: Free OSS audio editor, default beginner choice.
- **AI features**: OpenVINO-based plugins added (transcription, music separation, noise suppression — **runs locally**) in 2024-2025.
- **Editing model**: Mostly destructive (waveform edits write into project), limited undo depth on long sessions, project files huge.
- **Privacy**: Local. (Telemetry scare from 2021 was rolled back; current is opt-in.)
- **Pricing**: Free.
- **Top complaints**: Destructive workflow; bloated project files; UI dated; no text-based editing; poor multi-track for podcast; AI plugin install friction.
- **Differentiator**: Truly free + truly local + now genuinely has local AI via OpenVINO.

### 1.12 Open-source / local-first stack (DarkRoom, Whispering, aTrain, WhisperX-based pipelines)
- **Core positioning**: Glue your own pipeline: faster-whisper / whisper.cpp + FFmpeg + (optional) local LLM (Ollama).
- **AI features**: Transcription (Whisper variants — Large-v3 ~2.7% WER clean, 8-12% WER podcasts; faster-whisper ~4× speed; whisper.cpp portable C++), diarization (WhisperX/pyannote), summarization via local LLM, filler detection via LLM-on-transcript.
- **Editing model**: Whatever you build. Most existing OSS projects are pipelines, **not interactive editors with review UI** — that is the gap our project sits in.
- **Privacy**: 100% on-device.
- **Pricing**: Free; capex = your hardware.
- **Top complaints**: No polished UX; setup pain (CUDA/CTranslate2/PyAnnote auth); no "approve/reject per edit"; no integration with podcast hosts; community-maintained, breakage on dep updates.
- **Differentiator**: The only branch where the user genuinely owns the data and the model.

### 1.13 Honorable mentions
- **Alitu** — opinionated "podcast maker" (cloud, beginner-friendly, denoise + leveler in one click). Cloud-only.
- **Squadcast** — now inside Descript (acquired); recording layer.
- **Zencastr** — Riverside competitor; cloud + local backup.
- **Spectro** — niche local audio analyzer; not a full editor.

---

## 2. Comparison Matrix (Feature × Tool)

Legend: + native / strong; ~ partial / weak; — absent; $ paywalled add-on.

| Feature | Descript | Adobe Pod | Riverside | Podcastle | Cleanvoice | Auphonic | Castmagic | Hindenburg | Resound | Reaper | Audacity | OSS DIY | **Our tool** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Filler removal | + | — | + | + | + | + | — | ~ | + | — | — | ~ | + (planned) |
| Silence/long-pause trim | + | ~ | + | + | + | + | — | + | + | ~ | ~ | ~ | + |
| Mouth-sound removal | ~ | — | ~ | ~ | + | ~ | — | — | ~ | — | — | — | + (target) |
| Denoise / dereverb | + | + | + | + | + | + | — | + | + | $ | $ | ~ | + (RNNoise/Demucs) |
| Loudness leveler | ~ | — | ~ | ~ | + | + | — | + | + | ~ | ~ | ~ | + (FFmpeg) |
| Auto chapters | + | — | + | ~ | — | + | + | ~ | — | — | — | ~ | + |
| Auto show notes | + | — | + | ~ | — | — | + | — | — | — | — | + (LLM) | + |
| Transcription | + | + | + | + | + | + | + | $ | + | — | + (OpenVINO) | + | + (Whisper) |
| Text-based editing | + | ~ | + | + | — | — | — | + | — | — | — | — | + (planned) |
| Voice clone | + | — | — | + | — | — | — | — | — | — | — | (XTTS local) | not target |
| Multitrack DAW | + | — | + | + | — | — | — | + | — | + | + | DIY | — (out of scope) |
| Per-edit review/diff | ~ | — | ~ | ~ | — | — | — | + (DAW) | + | + | + | — | **+ key differentiator** |
| True undo / non-destructive | ~ | — | ~ | ~ | — | — | — | + | + | + | ~ | DIY | + (snapshot model) |
| 100% local processing | — | — | — | — | — | — | — | + (transcription cloud) | — | + | + | + | **+** |
| No upload required | — | — | — | — | — | — | — | + | — | + | + | + | **+** |
| CLI / scriptable | — | — | — | — | API | API | API | ~ | — | + (ReaScript) | ~ (CLI) | + | **+** |
| Local web dashboard | — | — | — | — | — | — | — | — | — | — | — | rare | **+** |
| Free tier real cap | metered | 1hr/day | trial | 1hr/mo trans | 30min trial | 2hr/mo | trial | trial | 1hr/mo | 60-day full | unlimited | unlimited | unlimited |
| Subscription floor | $16/mo | bundled | $24/mo | $14.99/mo | $11/mo | $13/mo | $39/mo | $8.25/mo | $12/mo | $60 once | free | free | free |

---

## 3. Unmet Needs — Hobbyist / Solo Podcaster Lens

Three to five real gaps the field hasn't solved, ranked by how much **local-first** can win.

1. **"I don't want my guest's voice on someone's training set."** Voice-cloning lawsuits (NPR host vs Google NotebookLM, ElevenLabs scraping) and ToS clauses granting "perpetual, irrevocable, royalty-free, worldwide licence" have made consent + cloud uploads a real anxiety. Local-first removes the question entirely — and it can be marketed as a contractual artefact ("audio never leaves the machine, signed by the binary"). **Local wins outright.**

2. **"AI ate the wrong words and I can't tell what changed."** Cleanvoice, Adobe Enhance, Auphonic deliver a single processed file — there's no diff. Descript has reversible delete but users still report undo gaps. Resound is the only one with per-item review. A **proper diff/review UI before applying edits** (filler list + waveform context + accept/reject + dry-run export) is a clear unmet need. Local-first helps because the full original audio is cheap to keep on disk for diffing.

3. **"My credits ran out mid-episode."** Sept-2025 Descript repricing, Cleanvoice metered hours, Castmagic minute caps, Auphonic credit packs — every cloud tool meters AI work. For a hobbyist with one ~60-90 min episode/week, monthly pricing punishes both peaks (live event week) and lulls (paying $24 for nothing). A local tool has zero marginal cost per minute. **Pricing pain is the strongest "switch" signal Reddit produces.**

4. **"I can't reproduce last month's edit."** Cloud editors don't expose the edit graph. If a guest asks for a fix two months later, it has to be re-done by hand. A **declarative edit recipe (YAML/JSON) checked into git** plus deterministic re-renders is something only a CLI/local tool can credibly offer. This is the "infra-as-code" angle for podcasters.

5. **"Offline = no work."** Podcastle/Riverside/Adobe stop functioning without internet; Descript degrades. Travel/coffee-shop/hotel editing is real. Local-first is trivially better here — worth saying out loud.

---

## 4. Unmet Needs — Mid-Size Studio Lens (weekly cadence, multi-host, quality matters, budget-aware)

Studios live with different pain than hobbyists.

1. **Per-seat repricing risk.** Descript's Sept-2025 pivot to media-minute pools surprised teams that scaled past the cap. Hindenburg requires one license per user with no sharing. A **self-hosted tool with no per-seat cost** is a CFO-friendly story. Even if the studio still uses Descript for the text-edit UX, our tool can own the deterministic post-processing leg (leveler, loudness, chapter export, RSS push) without per-minute fees.

2. **Multi-track multi-host hygiene.** Riverside Magic Clips misaligns audio/video (wrong speaker on screen); Adobe Enhance can't separate bleed on one mic; Descript Rooms is "buggy" per Reddit. Studios producing 3-4 host shows still spend hours on cleanup per episode. A **multi-track-aware filler/cross-talk pipeline** — that knows track A is host, tracks B/C are guests, only cuts host stutters from host track and never crosses tracks — is genuinely missing. Local tools can do this without bandwidth penalties (multi-track uploads to cloud are slow + costly).

3. **Reproducible pipeline + audit trail.** Studios need to answer "what did we change?" and "can we re-render at higher quality?" — exactly what cloud editors hide. A CLI that emits a machine-readable change log per episode (filler cuts with timestamps, leveler params, denoise model version) is **release-engineering for podcasting**. Nobody ships this today.

4. **Brand-specific filler/style policies.** Castmagic/Cleanvoice are rule-based, can't adapt to "we keep 'um' before emotional beats" or "host A's laugh is part of the brand, never cut". A local tool with **per-show config + per-host overrides + opt-in local LLM that learns from past approvals** is differentiated and can be private (model fine-tuning on the studio's own laptop, not shipped to a vendor).

5. **Vendor-lock-in escape hatch.** Cloud tools own the project file. If Descript repricing/outage/acquisition happens (it just did), the studio is stranded. A **canonical edit-recipe + raw audio on disk** means switching costs are bounded. Contracts and procurement teams care; this is sellable upmarket.

6. **Hardware investment already paid.** Many studios already have a Mac Studio / RTX workstation for video. Cloud tools ignore that capex and re-charge for compute monthly. Local-first lets the studio amortize hardware they already bought.

---

## 5. Where Local-First Specifically Wins (Synthesis)

The field clusters into three groups, all of which leak in the same places:

| Cluster | Examples | Where they leak |
|---|---|---|
| Cloud-native AI editors | Descript, Riverside, Podcastle | Pricing volatility, undo/diff weakness, privacy of voice clone, offline = dead |
| Headless cloud processors | Adobe Enhance, Cleanvoice, Auphonic, Castmagic | One-shot destructive output, no review UI, metered credits, upload friction |
| Local DAWs | Hindenburg, Reaper, Audacity | No AI / weak AI, no text-based editing, no LLM-driven show-notes, dated UX |

**Our wedge** sits at the empty intersection: *local-first AI* with *review/diff UX* and *CLI + local web dashboard reproducibility*. Specifically defensible:

- **No upload, no metering, no credit dread** — pricing-pain converts directly.
- **Diff / dry-run / accept-reject per edit** — the missing UX in headless cloud processors and most editors except Resound and DAWs.
- **Reproducible edit recipes (git-friendly)** — nobody ships this; it's natural for a CLI tool.
- **Per-show / per-host config that learns locally** — training on user data without sending it anywhere.
- **Hardware-aware** — uses the Mac/RTX already on the desk; faster-whisper + whisper.cpp benchmarks support Whisper Large-v3 quality at 4× original speed locally.

What it explicitly **does not need to chase** to be differentiated:
- Voice cloning (lawsuit-magnet, low ROI for the target user).
- Cloud multi-host recording (Riverside/Squadcast/Zencastr own this; integrate via file import instead).
- Full DAW timeline (Reaper/Hindenburg/Audacity exist; stay opinionated and post-only).

---

## Sources

- [Descript Review 2025 — workfromyourlaptop](https://workfromyourlaptop.com/descript-review/)
- [Descript Pricing September 2025 — Trebble](https://www.trebble.fm/post/descript-pricing-september-2025)
- [Descript Pricing 2026 — Sonix](https://sonix.ai/resources/descript-pricing/)
- [Descript Reviews — Capterra](https://www.capterra.com/p/230702/Descript/reviews/)
- [Edit like a doc — Descript Help](https://help.descript.com/hc/en-us/articles/15726742913933-Edit-like-a-doc)
- [Descript Overdub Review 2026 — qcall.ai](https://qcall.ai/descript-overdub-review)
- [Adobe Podcast Enhance Review 2026 — Podtools](https://podtools.cc/fix-bad-audio-free-adobe-enhance-review/)
- [Adobe Podcast Pros and Cons — G2](https://www.g2.com/products/adobe-podcast/reviews?qs=pros-and-cons)
- [Adobe Podcast Review — Cleanvoice blog](https://cleanvoice.ai/blog/adobe-podcast-review/)
- [Riverside Pricing](https://riverside.com/pricing)
- [Riverside Review 2026 — Cleanvoice blog](https://cleanvoice.ai/blog/riverside-review/)
- [Riverside Reviews — Trustpilot](https://www.trustpilot.com/review/riverside.fm)
- [Podcastle Pricing](https://podcastle.ai/pricing)
- [Podcastle Review 2025 — Cleanvoice blog](https://cleanvoice.ai/blog/podcastle-review/)
- [Cleanvoice Filler Words](https://cleanvoice.ai/filler-words/)
- [Cleanvoice Review — Castmagic](https://www.castmagic.io/software-review/cleanvoice-ai)
- [Auphonic Pricing](https://auphonic.com/pricing)
- [Auphonic Privacy Policy](https://auphonic.com/privacy)
- [Auphonic Review — AI Audio Gear](https://aiaudiogear.com/auphonic-review/)
- [Castmagic Pricing](https://www.castmagic.io/pricing)
- [Castmagic Review 2026 — Today Testing](https://todaytesting.com/castmagic-review/)
- [Hindenburg Pro — The Podcast Consultant](https://thepodcastconsultant.com/blog/hindenburg-pro)
- [Hindenburg Pricing — SoftwareSuggest](https://www.softwaresuggest.com/hindenburg)
- [Resound](https://www.resound.fm/)
- [Resound Enhance](https://www.resound.fm/enhance)
- [Reaper for Podcasts — mkaz.blog](https://mkaz.blog/misc/using-reaper-instead-of-audacity-for-podcasts/)
- [REAPER Review — The Podcast Consultant](https://thepodcastconsultant.com/blog/reaper-audio-production)
- [DarkRoom: Local AI Podcast Editor — DEV.to](https://dev.to/drjoanneskiles/i-built-a-local-ai-podcast-editor-because-im-done-renting-my-own-workflow-1mpk)
- [Whispering — Slator](https://slator.com/whispering-open%E2%80%91source-local%E2%80%91first-transcription-app/)
- [faster-whisper repo](https://github.com/SYSTRAN/faster-whisper)
- [whisper.cpp repo](https://github.com/ggml-org/whisper.cpp)
- [Whisper variants comparison — Modal](https://modal.com/blog/choosing-whisper-variants)
- [Whisper accuracy 2026 — NovaScribe](https://novascribe.ai/how-accurate-is-whisper)
- [NPR host sues Google over NotebookLM voice clone](https://mediacopilot.ai/npr-host-sues-google-ai-voice-notebooklm/)
- [Voice cloning ethics 2025 — Mureka](https://www.mureka.ai/hub/aimusic/ai-voice-cloning-legal-issues/)
- [Consumer Reports — voice cloning safeguards 2025](https://www.consumerreports.org/media-room/press-releases/2025/03/consumer-reports-assessment-of-ai-voice-cloning-products/)
- [AI Podcast Editing Tools Comparison — PodRewind](https://podrewind.com/blog/ai-podcast-editing-tools-comparison)
- [AI vs Traditional Podcast Editing 2026 — Podcast Studio Glasgow](https://www.podcaststudioglasgow.com/podcast-studio-glasgow-blog/ai-vs-traditional-editing-for-podcasts-in-2026-which-one-actually-saves-you-time-and-sanity)
