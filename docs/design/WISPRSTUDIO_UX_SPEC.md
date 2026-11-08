# WisprStudio UX specification

**Status:** CANDIDATE SPEC — nothing built or tested. Applies the [design system](WISPRAL_DESIGN_SYSTEM.md) to the retained VoiceStudio fork ([source decision](../../research/wispral-world-class/SOURCE_DECISION_MATRIX.md#wisprstudio)). Capability IDs (ST-xx) refer to the [product capability catalog](../strategy/WISPRAL_PRODUCT_VISION.md#22-wisprstudio--creative-voice-production).

**Design priority:** creative workflow clarity. Timeline, engine selection, project structure, rendering progress and recovery must be coherent and professional. The donor already has a project, timeline, dubbing and engine UI; WisprStudio restructures the information architecture and applies the design system. It does **not** build a new editor.

## 1. Information architecture

```text
Home ─┬─ Projects (recent, templates, import)
      ├─ Voices (library + consent ledger)
      ├─ Engines & models (capability cards, rights, downloads)
      └─ Render queue (all projects)

Project ─┬─ Script view   (write / paste / import; speakers; pronunciation marks)
         ├─ Timeline view (multitrack clips, waveform, trims, gain, fades)
         ├─ Dub view      (source → transcript → translation → alignment → voices → mix)
         └─ Export        (formats, stems, subtitles, provenance sidecar)
```

A project is one folder on disk that the user owns (Obsidian principle): project file, media, renders and a provenance log. It can be zipped, moved and backed up without Wispral.

### 1.1 First run and new project

1. **Welcome + profile:** "Personal" or "Commercial" use. The profile decides which engines are allowed (non-commercial weights are blocked for Commercial) and is shown on every project.
2. **Engine:** the recommended engine card for this machine (CPU or GPU, languages, license). Its download starts after consent and runs in the background while the user writes or pastes a script.
3. **Start:** blank project, a **sample project** (pre-rendered, so the first playback needs no engine), or import a script.
4. **Empty states:** no engine installed → "Install an engine to generate speech" with the recommended card; no voices → stock voices first, cloning explained with its consent requirement.

## 2. Project editor layout

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Project name · engine badge · consent status · render status Ctrl+K │  top bar
├────────────┬──────────────────────────────────────┬──────────────────┤
│ Outline /  │ Script editor                         │ Inspector        │
│ speakers   │ (paragraph blocks, speaker chips,     │ (selection-bound:│
│            │  pronunciation marks, generate per    │  voice, speed,   │
│            │  block, block status)                 │  pitch, engine   │
│            │                                       │  params, consent)│
├────────────┴──────────────────────────────────────┴──────────────────┤
│ Segment timeline (VoiceStudio dub/long-form timeline); playhead; zoom│
├──────────────────────────────────────────────────────────────────────┤
│ Transport · loudness meter · job progress strip                      │
└──────────────────────────────────────────────────────────────────────┘
```

- Script and timeline are two views of the same blocks: selecting a paragraph highlights its clip and vice versa.
- **MVP scope:** the timeline is VoiceStudio's existing segment timeline for long-form and dubbing. A DAW-style multitrack editor is a later capability (tier L, Voicebox's MIT multitrack editor as the donor candidate).
- **Timeline direction never mirrors**, even in Arabic UI; panels around it do mirror. The script editor uses `dir="auto"` per block, so Arabic and English blocks each align correctly.
- Command menu (`Ctrl+K`) for every action. Single-key transport shortcuts (Space play/pause, `J`/`K`/`L` shuttle, `S` split) work **only while the timeline or transport has focus**, are remappable, and bind by physical key code; in the script editor these keys type text (WCAG 2.1 SC 2.1.4). `Ctrl+Z` undo everywhere.

## 3. Engine and model selection (ST-03)

Each engine/model appears as a **capability card**:

| Field | Example (illustrative only) |
| --- | --- |
| Name and version | "Engine X · v2 · revision abc123" |
| Languages | EN ✓ · AR (MSA) ✓ · AR (Gulf) *not measured* |
| Runs on this machine | CPU ✓ (slow) · GPU — |
| Offline | ✓ after download (1.2 GB) |
| Code license / **weight license** | MIT / CC BY-NC 4.0 → **Non-commercial: blocked in commercial projects** |
| Cloning | Requires consented reference |
| Measured quality | Link to WB-TTS results, or "Not measured" |

The engine is chosen **per project** and shown in the top bar. WisprStudio never switches engine, model or voice automatically, including on resume. Changing the engine on a project with existing renders asks whether to re-render or keep existing clips, and records the change in the provenance log.

## 4. Voices and consent ledger (ST-04)

- **Voice library** lists stock voices (with source and license) and cloned voices.
- Creating a cloned voice is a three-step flow: (1) upload or record reference audio; (2) **consent record** — subject name, relationship ("myself", "a person who gave written consent"), purpose (personal / commercial), scope, expiry, and a recorded or uploaded consent statement; (3) create the voice. Step 3 is disabled until step 2 is complete.
- Each voice shows a consent badge: **Consented** (green, with scope) · **Expiring soon** (amber) · **Revoked / expired** (red, voice unusable).
- **Revocation** is one action with a confirmation that lists affected projects and queued jobs; queued and resumable jobs using the voice are blocked, and cached embeddings are deleted. The UI states plainly that already-exported files cannot be recalled.

## 5. Rendering, queue and recovery (ST-07, ST-13, ST-01)

- **Take history:** regenerating a block keeps previous takes; the inspector offers A/B playback and "Use this take". Takes are deleted only explicitly.
- **Stale blocks:** editing text, voice or pronunciation marks a block stale; the top bar shows **Regenerate stale (n)**.

- Generation runs as jobs; each block shows its status (pending, generating, done, failed, stale because text changed).
- The render queue shows per-job progress with segment granularity, elapsed and estimated time, and a **Cancel** that reports the truth: "Cancelling…" → "Stopped" or "Finished before cancel" or "Stop not confirmed — engine still running (Force stop)".
- After a crash or forced quit, reopening the project shows a recovery banner: "Long-form render was interrupted at chapter 4 of 9. Resume / Discard partial". Resume verifies script, voice, consent and engine identity before continuing; if anything changed it explains what and offers a fresh render.
- Disk-full and out-of-memory errors are specific and keep completed segments.

## 6. Dubbing flow (ST-11, ST-12)

Editing an earlier stage marks every later stage **stale** and shows a diff of what changed (segments added, removed or retimed); nothing downstream is silently regenerated.

A stepper with an explicit review gate per stage; each stage's output is editable before the next stage runs.

1. **Source** — local media file (URL ingest is disabled in the first release).
2. **Transcript** — ASR with speaker labels; editable; timestamps visible.
3. **Translation** — side-by-side source and target, per segment; editable; glossary.
4. **Voices** — map each source speaker to a consented or stock voice.
5. **Timing** — duration fit preview; segments that cannot fit without exceeding speed limits are flagged (the validating guard rejects malformed timing before the donor fit planner runs).
6. **Mix & export** — background/stems handling, loudness normalization, subtitles.

## 7. Export (ST-08)

Formats: WAV, FLAC, MP3, per-speaker stems, SRT/VTT subtitles. Every export writes a provenance sidecar (JSON) listing engine, model revision and digest, voices and their consent IDs, and whether a watermark was applied. Exports are written atomically (temp file, then rename).

## 8. Core journeys and acceptance

| Journey | Acceptance (G-E2E) |
| --- | --- |
| S1 First narration: new project → paste script → pick stock voice → generate → export WAV | Under 5 minutes for a first-time user (*target*); export plays; sidecar present |
| S2 Consented clone: record reference → consent → create voice → generate | Cloning impossible without the consent step |
| S3 Revoke: revoke a voice used in a queued long-form job | Job blocked; UI lists the affected project; no audio rendered after revocation |
| S4 Crash recovery: kill the app at 40% of a long-form render → reopen → resume | Resume completes with identical segment identity; no partial file shown as final |
| S5 Arabic dub: 2-minute English clip → Arabic dub with two speakers | Every stage reviewable; timing violations flagged; export with subtitles |
| S6 Non-commercial weights | In a commercial-profile project the non-commercial engine is visibly blocked with the reason |
| S7 Keyboard-only edit | Trim, move and re-generate a clip without a mouse |
