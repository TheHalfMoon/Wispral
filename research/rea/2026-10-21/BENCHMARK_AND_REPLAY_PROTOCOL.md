# Benchmark and replay protocol

Date: 2026-10-21. **PROPOSED; planning only.** This document defines future evidence collection. No reported threshold, corpus size, trial count or workflow below is a completed experiment. Existing observations are indexed separately in [rea-runtime-observations.json](rea-runtime-observations.json), [ink-source-evidence.json](ink-source-evidence.json), [studio-mechanism-probe-results.json](studio-mechanism-probe-results.json) and the pillar studies.

## Authority and entry conditions

The frozen B2 experiment and its active canonical successor retain their existing identities, scope and claim guards. This protocol does **not** reopen ATTEMPT-003, alter preprocessing/C0, introduce a new candidate, authorize B2 scoring, convert harness failures into recognition errors, select production STT, or authorize product implementation. Future benchmark work needs its own READY Grain and applicable canonical authority. A public competitor observation may be collected with existing legitimate access; paid subscriptions, unconsented voices and account bypass are outside this plan.

Separate four evidence tracks in every result:

1. **Synthetic contract replay:** generated text/events/fake workers and declared synthetic audio. Useful for authority, ordering, cancellation, fault and recovery invariants. It provides no human speech-accuracy claim.
2. **Frozen historical benchmark:** the existing B2 artifacts, unchanged and governed by their own authority. No result is imported into a new score merely because it is accessible.
3. **Consented human study:** speakers, languages, accents and environments with documented purpose, retention and withdrawal. This is the only proposed track for human recognition, intelligibility and preference claims. It has not been collected here.
4. **Competitor workflow observation:** exact accessible product build or dated web deployment, account tier, allowed workflow and redacted artifacts. Public marketing, source inspection, first-party documentation and user workflow execution remain distinct evidence classes.

Run only after the exact candidate, permitted paths, corpus split, normalization/scorer, model artifacts, hardware cell and thresholds are frozen. An absent fixture, inaccessible account, skipped suite, model download failure or blocked device permission is **NOT_RUN / BLOCKED_EXTERNAL**, never PASS. Keep unsuccessful attempts and negative findings in the denominator and evidence ledger.

## Reproducible run identity

Use the following schema as a proposed contract, adapting field syntax to the repository's approved evidence dialect. Reject missing required identities instead of inventing defaults.

```json
{
  "schema_version": "wispral-replay-proposal-v1",
  "run_id": "unique-generated-id",
  "authority": {"grain": "exact-id", "authority_base": "full-git-sha", "candidate_head": "full-git-sha", "claim_scope": ["one-stated-claim"]},
  "track": "synthetic_contract|historical_frozen|consented_human|competitor_workflow",
  "scenario_id": "INK-S1",
  "attempt": 1,
  "started_at_utc": "ISO-8601",
  "source": {"repo": "owner/name", "commit": "full-git-sha", "file_sha256": {}, "application_build": "exact-or-NOT_OBSERVED"},
  "environment": {"os_build": "exact", "arch": "exact", "cpu": "exact", "ram_bytes": 0, "gpu": "none-or-exact", "driver": "exact-or-not-applicable", "power_profile": "exact", "microphone": "exact-or-synthetic", "sample_format": "exact", "audio_route": "exact"},
  "runtime": {"language_runtime": "exact", "package_lock_sha256": "digest", "native_binary_sha256": {}, "container_image_digest": "exact-or-not-applicable"},
  "model": {"provider": "local-or-explicit-provider", "id": "exact", "revision": "exact-or-unavailable", "artifact_sha256": {}, "tokenizer_sha256": {}, "configuration_sha256": "digest"},
  "data": {"manifest_sha256": "digest", "split": "development|held-out", "speaker_pseudonym": "synthetic-or-consented-pseudonym", "language_stratum": "exact", "consent_record_ref": "non-sensitive-opaque-reference", "noise_recipe_sha256": "digest-or-none"},
  "permissions": {"microphone": "state", "context": "bounded-purpose", "network_route": "policy-id", "voice_consent": "state", "tenant_scope": "synthetic-id"},
  "timing": {"clock": "monotonic", "units": "nanoseconds", "cold_or_warm": "cold", "events_path": "relative-artifact-path"},
  "result": {"status": "PASS|FAIL|NOT_RUN|BLOCKED_EXTERNAL|INCOMPLETE", "raw_path": "relative-artifact-path", "raw_sha256": "digest", "expected_path": "fixture-path", "failure_class": "none-or-specific", "attempts_total": 1},
  "limitations": ["exact missing observations"],
  "review": {"independent_reviewer": "identity-or-NOT_RUN", "reviewed_head": "full-git-sha-or-none"}
}
```

Zero numeric placeholders above illustrate field types, not measurements. Capture exact prompt/template, glossary, seed where available, decoding/VAD/endpoint configuration, quantization, thread count, batch size, caches, service region, transport, paid/free tier and source/model terms. Web builds without exposed version get dated URL, browser version and bounded artifact hashes; record **deployment identity unavailable**, rather than treating a page hash as the complete service identity. Preserve request IDs only when safe and useful; redact tokens, customer identities, query values and proprietary content. Store hashes and bounded observations in GitHub, not confidential raw voices or closed-vendor runtime dumps.

Retain raw provider hypotheses, normalized scoring text, approved final text and interpreted intent as separate artifacts. Never overwrite source text with formatting output. Include timeouts, cancellations, rejected tasks and missing outputs. Report both all-attempt completion rates and accuracy among completed attempts; silently dropping failed jobs invalidates the comparison. Record test order, repeat count, warmup, missing-data rule and exclusion reasons before running.

## Success, failure and boundary replay families

Each target gets three independent records: successful workflow (**S**), failed/recovered workflow (**F**) and permission/platform/access boundary (**B**). Reusing a family fixture is allowed; claiming a target passed because another application ran that fixture is not. Source tests and public homepages do not satisfy a real dictation, studio or agent session.

### WisprSide

**INK-S1:** in a disposable editor, explicitly activate capture, dictate the same approved English and Arabic number/name passage, pause, self-correct one phrase, finish, review raw versus formatted text and deliver to the captured intended target. Verify accepted text through the editor fixture's actual document content, including code-switching, punctuation, Arabic direction, emoji and a developer path. A key-posted or clipboard-reader receipt is weaker than document insertion.

**INK-F1:** change focus to a decoy editor between capture and delivery; close the intended window; simulate target-identity reuse, clipboard mutation, permission denial, empty recording and delayed STT result. Expect visible failure and manual-copy recovery with no decoy insertion. After partial typing, expect no automatic full retry or duplicate text. Cancel before/after finalization and restart capture; late results must not land in the next session.

**INK-B1:** fresh OS account/profile, permission denied then granted then revoked, locked/resumed session, elevated target, disconnected microphone and offline network. Validate keyboard/button fallback. Run Windows native target integrity, macOS AX/TCC and Linux X11/Wayland portal limitations separately; no extrapolation across those platforms.

| Target | Target-specific success focus | Failure/recovery focus | Boundary focus |
| --- | --- | --- | --- |
| Wispr Flow | App-specific formatting and correction in two disposable editors | Wrong-window delivery and service loss | Document actual Windows/macOS availability and real install permissions; homepage CTA alone is insufficient |
| Aqua Voice | Vocabulary, code/name retention and correction | Interrupted session and changed selection | Actual installed build, microphone/context permission and network route |
| Superwhisper | Selected mode's raw/processed distinction | Failed local/remote model then explicit recovery | Chosen model offline behavior and macOS permissions; other platforms only if genuinely offered/tested |
| VoiceInk | Native Unicode delivery and explicit partial result | Clipboard marker changed or partial typing | macOS AX denial/revocation; no Windows support inference |
| OpenWhispr | Captured target and terminal-specific chord | Focus restoration fails; no foreground fallback | Windows UIPI/elevation and explicit provider routing |
| Handy | Capture completeness, hold/toggle and streamed hypothesis lifecycle | Dropped frames, worker crash and cancel race | Exact recorder/keys/native dependency build and platform permissions |
| FreeFlow | Bounded selection-driven rewrite with consent | Selection becomes stale; screenshot unavailable | macOS AX and screenshot opt-in; no silent screenshot fallback |
| Voicebox | Capture/transcribe route without duplicate microphone owner | Queue cancellation and late result suppression | Desktop shell permissions and explicit local/network engine choice |

### WisprStudio

**ST-S1:** generate a short approved script with a licensed preset voice, retain input/output metadata, edit one segment on the timeline, apply a pronunciation/glossary entry where supported and export WAV plus one supported compressed format. Verify sample rate, channel count, duration, clipping, silent/mute behavior and whether the rendered output reflects edits. Separately run a two-speaker consent-backed dubbing fixture: frozen source transcript, human-reviewed translation, aligned segments and export. Voice cloning is a distinct optional experiment requiring actual voice-specific consent; preset success does not imply cloning or dubbing parity.

**ST-F1:** cancel queued and active render jobs, induce one corrupt/missing model or output segment and one worker crash, restart, resume only unchanged valid segments and export again. Verify immutable original media and no output marked complete before atomic finalization. Include zero-volume export, malformed/overlapping timing arrays, OOM, timeout and disk-full fixtures. Measure stopped state and orphan processes independently of a coroutine's cancellation receipt.

**ST-B1:** revoke voice consent with a clone job queued; alter accepted model terms/digest; disable networking after staging admitted artifacts; open a project on a machine missing its selected engine; test unsupported language and unlicensed voice-pack refusal. Verify keyboard navigation, RTL script editing, caption/transcript availability and recoverable schema migration. Run on each claimed OS; a Python backend import is not an installed application result.

| Target | Target-specific success focus | Failure/recovery focus | Boundary focus |
| --- | --- | --- | --- |
| VoiceStudio | Segment fit, timeline, long-form resume and dubbing export | Interrupted render and corrupt cache | Model terms, consent and local artifact routing |
| Voicebox | Profile/engine selection and edited export | Queued versus running cancellation and mute export | Native shell plus model-worker boundary |
| ElevenLabs | Legitimately accessible generation, pronunciation and export; authenticated dubbing separately | Rejected generation or cancelled export and retry | Account/tier, consent and supported language; a disabled public Play button is not generated audio |
| Cartesia | Legitimately accessible streamed speech and export where offered | Transport disconnect and explicit restart | Sign-in/account boundary, exact API tier and selected voice rights |
| Resemble AI | Preset generation; optional consent-backed clone and watermark behavior | Failed generation and recovery | Account entitlement, consent and asset rights |
| Chatterbox | Exact multilingual/Turbo/Nano engine with admitted assets | Process stop, missing checkpoint and OOM | Model family language limits, reference duration and watermark recording |

### Klaint

**KL-S1:** use a synthetic customer account and fake CRM/payment/ticket tools. Resolve a question, ask for a missing field, propose a reversible ticket update and perform it only through the deterministic broker with tenant/action/evidence binding. Then transfer to an authorized human inbox, showing transcript, unresolved work and tool outcomes. Once takeover is committed, the AI epoch cannot respond or mutate state. Voice adds a separately recorded barge-in while speech is playing; text success alone does not qualify voice.

**KL-F1:** inject instructions through retrieved knowledge and tool output; forge another tenant's IDs; repeat a webhook; return 429/500; time out after the fake CRM commits; crash the bridge before acknowledgement. Reconcile the same idempotency key to the existing effect rather than blindly retrying. Test no-human-available, transfer rejection, provider disconnect, interrupted tool completion and cancel racing a committed action. Preserve committed effects in the audit and report uncertainty; cancellation cannot reverse an already completed external action.

**KL-B1:** tenant A cannot read or mutate tenant B with any user/model-supplied identifier. Reject stale/future/nonfinite webhook timestamps, signature mismatch and replay. Customer speech cannot select credentials, account domains or tool scope. Recording disabled/revoked must affect queued/new media retention; outbound phone destinations require authorized test numbers and explicit telephony permission. Test private deployment and cloud integration claims separately.

| Target | Target-specific success focus | Failure/recovery focus | Boundary focus |
| --- | --- | --- | --- |
| Decagon | Permitted sandbox support resolution, action and human handoff | Failed tool and conversation recovery | Sandbox access and tenant/action scope; public homepage is not a support session |
| Sierra | Permitted Agent Studio/support workflow and verified action | Interrupted journey and human escalation | Sandbox role and customer-data isolation |
| Ada | Permitted knowledge response and authorized escalation | Unanswerable request and transfer failure | Accessible workspace, role and tenant boundary |
| Intercom Fin | Permitted answer, ticket action and inbox takeover | Repeated event and no-human path | Fin workspace entitlement and scoped inbox identity |
| Parlant | Guideline match through brokered ToolService | Prompt injection, contradictory guideline and provider timeout | Authorization must remain deterministic outside model guideline matching |
| Botpress | Selected connector schema and HITL event through fake endpoint | OAuth refresh failure and unknown POST outcome | Public SDK versus hosted runtime distinction; connector tenant credentials |
| Chatwoot | Account-scoped inbox assignment with transcript | Duplicate webhook and bot/human race | Community versus enterprise subtree; account policy enforcement |
| Rasa | Bounded rule/tracker scenario and handoff | Lock conflict, stale tracker and restart | Actual maintained version/Python environment and isolated action server |
| Retell AI | Authorized test-call interruption and warm transfer | Provider/tool timeout, call drop and retry | Test number, recording consent, region and account entitlement |
| Vapi | Authorized assistant test session and selected tool action | Transport interruption and tool reconciliation | Provider credentials, call destinations and tenant isolation |
| Bland AI | Authorized test-call multi-turn and handoff | Failed destination and call termination | Current API/version, test number, recording and workspace limits |

### Realtime speech backends and developer control

**RT-S1:** replay the same declared audio sequence through the selected transport, capturing partial/final text, speech start/stop, end-of-turn, tool proposals, audio generation and actual playback position. Preserve provider event IDs and mapping. **RT-F1:** disconnect mid-frame, inject duplicate/out-of-order events, pause at end-of-turn then resume, cancel model output during playback and time out a tool. **RT-B1:** expired credentials, explicit offline route denial, microphone permission revoked, unsupported audio format and account/region boundary. No live paid API request is implied by this recipe.

| Target | Specific observation required | Unproven boundary to test |
| --- | --- | --- |
| OpenAI Realtime | Select WebRTC/SIP or WebSocket; observe actual interruption and conversation truncation | Server-managed playback in WebRTC/SIP versus client playback/truncation in WebSocket; no universal cancel translation |
| Gemini Live | Freeze API/model version and observe session/audio/tool event mapping | Session resumption, interruption and capability limits for that exact transport/model |
| Deepgram | Flux v2 turn index, EagerEndOfTurn, TurnResumed and final EndOfTurn | Speculative work cancellation and exact accepted audio encoding; eager event cannot authorize a tool |
| AssemblyAI | Actual streaming events, end/termination and connection duration | Reconnect continuity and session-duration billing boundary; documentation is not an executed stream |
| Speechmatics | StartRecognition, audio acknowledgements, partial/final and EndOfTranscript | Temporary credential/region/format policy and stream completion |
| LiveKit Agents | Actual session interruption, protected speech and tool cancellation | Self-hosted/local topology, recording options and room/SIP boundary |
| Pipecat | PipelineWorker frames and cancel propagation to output | CancelFrame queued versus output stopped; selected local transports and provider extras |
| Local alternatives | Qualified sherpa-onnx, whisper.cpp, Moonshine or staged TTS adapter event trace | Windowed batch versus incremental semantics, process lifetime and no network escape |

**DEV-S1:** send a reviewed transcript through a structured ACP adapter to a fake agent, bind offered permission options, approve one reversible test action and record the actual result. **DEV-F1:** cancel before transport registration, during a permission prompt and after an accepted asynchronous turn; reject late events and ambiguous permission correlation. **DEV-B1:** adapter unavailable, unsupported protocol version, invalid option, changed repository/session and agent-requested authority widening. No spoken phrase bypasses the underlying agent's permission boundary.

| Target | Required exact identity and scope |
| --- | --- |
| Codex / codex-acp | Exact installed CLI and adapter SHAs, protocol version and permission/cancel race fixture |
| Claude Code / claude-agent-acp | Exact CLI and adapter SHAs; offered-option decoding, session binding and cooperative stop observation |
| Gemini CLI / ACP clients | Actual installed version and advertised protocol capabilities; mark unsupported operations explicitly |
| Orcel | Exact active policy entry point, approved provider and native process identity; do not assume legacy lib.rs is the active library |

## Human language and audio design

Propose a consented development pilot, followed by a held-out study with **40 speakers and 400 utterances**: ten speakers per primary stratum and ten utterances per speaker. Primary strata are English, read Modern Standard Arabic, natural Saudi Arabic and natural non-Saudi Gulf Arabic. Strata describe the recorded task and speaker's self-description; do not infer dialect from nationality. Use separate development speakers (proposed twenty) and ensure the held-out participants, scripts and audio never tune the final model, glossary or normalizer. The numbers are minimum planning targets, not a power calculation or sufficient basis for all language claims.

Balance short commands, spontaneous thought, names/numbers, negation, paths/code tokens and support dialogue. Include separately tagged Arabic-English code-switching in Saudi/Gulf tasks; report it separately rather than averaging away failures. Participants review reference transcripts and consent to the actual intended use. Voice cloning and speaker similarity need additional purpose-specific consent and revocation; speech-transcription consent alone is insufficient. Test withdrawal and deletion without publishing participant audio by default.

Keep clean microphone recordings separate from deterministic noise/reverberation variants. Specify microphone distance, gain, clipping, sample format and playback path. Freeze noise source rights, exact mixing recipe and SNR (proposed clean, 20 dB and 10 dB cells) and hash derived files. Speaker-independent splits must remain independent after noise augmentation. A replayed recording tests acoustic ingestion, while live speaking tests interaction; neither substitutes for the other.

## Metrics and honest denominators

| Surface | Metric and interpretation |
| --- | --- |
| STT | WER = (substitutions + deletions + insertions) / reference words; CER equivalently over declared character units. Preserve raw and normalized scores; specify Arabic diacritics, hamza/alef/ya, punctuation, case, numerals and tokenization before scoring. Do not normalize away negation, names, numbers or code tokens. Report by speaker, language, task, noise, device, model and completed/all attempts. |
| Meaning | Blinded bilingual annotation for changed intent, polarity, quantity, named entity, target/path and omitted instruction. Report critical semantic error count / eligible utterances, disagreements and adjudication. WER alone cannot authorize actions. Review raw, formatted and intent stages separately to locate the distortion. |
| Dictation | Release-to-final, release-to-accepted-text, end-to-end completion, wrong-target/duplicate/partial insertion counts; actual document verification, not key-post success. |
| TTS | Monotonic request-accepted to first generated PCM and first audible output separately; full generation time, real-time factor (generation time / audio duration), p50/p95, warm/cold, peak RSS/VRAM and failures. Record tokenizer/preparation/cache time and format. A vendor marketing latency is not a sample. |
| TTS quality | Blinded intelligibility, naturalness and pronunciation; optional consented speaker-similarity evaluation. Randomized paired A/B or ABX at loudness-controlled playback, matched script/voice rights, anonymized engine order and a predeclared rubric. Report listeners, clips, ratings, ties, missing ratings and confidence intervals; do not invent a single MOS from source claims. |
| Turn handling | Last input speech sample to final endpoint decision; false cutoff and unwanted continuation rates. Measure barge-in onset to audible output cessation, queued PCM discarded, model cancel receipt and independently observed worker stop as separate events. |
| Actions | Denied actions attempted/executed, tenant leakage, exact idempotent effects, uncertain outcomes reconciled, human takeover stale replies, authorization freshness and audit completeness. No model guideline-adherence score substitutes for these invariants. |
| Privacy/resources | Observed network connections/bytes by declared purpose, denied-route attempts, recording indicators, persisted content and deletion; CPU, RSS, VRAM, disk, cold install and dependency/native/model artifact size. An unplugged cable alone does not prove no attempted egress. |

Use an event clock on the same host for latency, or document clock synchronization uncertainty. Capture independent audio loopback/fixture timestamps for audible output, not a GUI animation. For deterministic fixture paths, compare expected event sequence and final state. For performance cells, propose 100 warm repetitions and twenty cold starts, randomized/interleaved by engine; publish all samples and workload lengths. Mark a p95 based on too few samples as exploratory. Separate transport/server latency from full user-perceived time.

For human comparisons, use paired results on the same frozen clips. Bootstrap by **speaker** for STT/meaning confidence intervals so repeated utterances from one person are not treated as independent. For listening studies, account for both listener and clip clustering; report method/seed and uncertainty, ties and multiple comparisons. Split selection/pilot from confirmation; do not choose winners and report the same samples as untouched validation. Report medians, tails and per-stratum harm, not only a pooled mean. A zero observed failure count is not proof of zero risk; provide its denominator and a binomial upper bound where assumptions are appropriate (approximately 3/n for a one-sided 95% upper bound after zero independent failures).

## Proposed release thresholds

These are **initial acceptance proposals**, chosen for a scoped first release and subject to explicit approval/freeze before a qualifying run. They are not current results, promises, vendor comparisons or retroactive B2 criteria. If pilot evidence shows a target is infeasible, revise the plan transparently before held-out confirmation; do not silently lower a threshold to pass a candidate.

| Claim/release boundary | Proposed gate |
| --- | --- |
| Authority and target integrity | Zero unauthorized or wrong-target effects in the complete declared negative suite; zero cross-tenant reads/writes, duplicate committed fake-tool effects and stale AI replies after committed takeover. Include at least 1,000 randomized authority/race sequences plus named adversarial cases. Counts and uncovered classes remain visible. |
| Privacy/offline scoped path | Zero undeclared successful outbound connections/bytes during the instrumented offline replay after admitted artifact staging; every denied attempt visible. Recording indicators and revocation match actual capture. “Offline” applies only to the exact tested path/engine/OS. |
| Cancellation contracts | All named stale-result tests reject late output. Proposed warm reference target: p95 audible barge-in stop <=250 ms; fake/local worker observed stop <=2 s after cancel, or explicit stopped-unconfirmed failure with no reuse of its capacity/authority. Native engines need their own qualified bound; request acknowledgement cannot pass the stop gate. |
| Dictation utility | Proposed clean held-out WER <=8% English, <=12% MSA and <=20% for each declared Saudi/Gulf stratum; code-switching/noise reported separately with no general claim until separately qualified. Zero unreviewed critical number/negation/target distortion reaches an executable action. Formatting errors and manual corrections are reported, not normalized away. |
| PTT responsiveness | On the frozen reference device and approved short-utterance cell, warm p95 release-to-final <=1.5 s and release-to-accepted-text <=2 s; report long-utterance and cold results separately. Devices missing the bound receive a narrower support claim or remain unsupported. |
| Studio preset baseline | Admitted exact model/voice, valid export and all corruption/mute/recovery fixtures pass; proposed short-script warm p95 first audible output <=1 s and sustained RTF <=1 for any “realtime” claim on its stated device. Otherwise ship only a clearly qualified batch capability. |
| TTS/language quality | No target-language quality claim before held-out native/bilingual listening. Proposed minimum: 90% of rated clips marked intelligible without a critical content error, per claimed language, with confidence intervals and at least twenty qualified listeners across the panel. Preference superiority requires a predeclared paired analysis whose interval supports that particular claim. |
| Klaint first release | Text/fake-tool and human-inbox workflow passes before phone/real customer actions. All tenant, replay, unknown-outcome and takeover fixtures pass; proposed >=95% successful completion on a frozen bounded synthetic support scenario set, with every failure retained. Human support/voice quality remains separate. |
| Install/stability/accessibility | Clean install, launch, update/rollback and uninstall on each specifically claimed OS build; keyboard fallback and visible capture/permission/error states pass. Proposed 1,000-turn synthetic soak has no orphan worker, unbounded queue or unexplained persistent resource growth. Full interactive accessibility/native tests remain necessary. |

Reference hardware is not yet frozen. Proposed first performance cell is an available Windows x64 CPU-only machine with 16 GB RAM; record the actual CPU/OS/power state before execution. Add an explicit macOS Apple Silicon cell, Linux X11 cell and Linux Wayland cell before claiming those combinations. GPU cells need exact GPU/driver/runtime and measured memory, separately from CPU. Mobile iOS/Android needs actual device permissions, lifecycle/background and audio-focus testing; desktop source or a responsive web layout does not establish mobile support. Hardware absence is a blocked cell, not permission to extrapolate.

## Current gaps and next smallest executable step

The entries below describe unresolved research coverage, not a demand for the founder to purchase access. Continue other work when one cell is blocked. Each future operator should first recheck legitimate existing access; do not repeat setup or silently install software merely because a previous tool session was unavailable.

| Target/cell | Present limit | Smallest next step when authorized resources exist |
| --- | --- | --- |
| Flow/Aqua/Superwhisper native | Public/partial page evidence; no native dictation triad | Resolve one legitimate installed exact build; record microphone permission boundary in a disposable editor, then INK-S1/F1/B1 one platform at a time |
| Handy/OpenWhispr/VoiceInk/FreeFlow/Voicebox native | Pinned source and selected pure probes, no installed capture/paste proof | Build/install one approved exact artifact in a disposable test environment; start with wrong-target/manual-copy fixture without private audio |
| VoiceStudio/Voicebox | Pinned mechanisms and synthetic non-audio probes only | Reproduce timing/export fixtures, then a licensed preset short script on one staged engine; no cloning required |
| Chatterbox and other local TTS | No weights/audio/GPU measurement | Admit exact checkpoint/tokenizer/voice rights and hashes; run one isolated preset generation and observed-stop test, then expand to held-out language panel |
| ElevenLabs | Public demo text entry observed; no verified generated/playable audio | With legitimate existing entitlement, generate/export one synthetic preset script; record failure cause only if observed, then authenticated dubbing separately |
| Cartesia | Public sign-in transition/return observed; no authenticated generation | Use legitimate accessible sandbox if present; one streamed synthetic preset request and disconnect test |
| Resemble AI | Source/docs references, no account workflow | Existing free accessible preset workflow first; keep voice-clone test absent until voice-specific consent exists |
| Decagon/Sierra/Ada/Fin | Public documentation/pages; no permitted customer-agent sandbox triad | Use an existing authorized demo/sandbox if available; one synthetic support exchange and handoff boundary; otherwise retain BLOCKED_EXTERNAL |
| Parlant/Botpress/Chatwoot/Rasa | Source traces, no full dialogue/inbox integration suite | Isolate fake provider/tools/inbox and run one denied tenant action plus explicit human takeover before real credentials |
| Retell/Vapi/Bland | Official docs, no authorized phone runtime | Prefer free browser/test session if already accessible; otherwise retain blocked phone cell; never call arbitrary real numbers |
| OpenAI/Gemini/Deepgram/AssemblyAI/Speechmatics | Transport documentation only; no live API audio run | Check existing permitted no-cost entitlement, freeze protocol/model, run one synthetic short stream; no purchase or secret committed |
| LiveKit/Pipecat | Pinned source trace, no full media session | Local loopback synthetic audio with selected fake providers; one output interruption and observed stop; select one turn owner |
| Developer agent adapters | Pinned ACP source; no new authenticated CLI compatibility run | Fake-agent permission/cancellation race first; qualify one installed exact CLI only after protocol-only contract passes |
| Human Arabic/Gulf/codeswitch | No consented human corpus or measured quality | Refine consent and participant-independent corpus manifest; approve collection/evaluation Grain before recording; do not substitute synthetic B2 |
| macOS/Linux/mobile/GPU | Missing measured platform/device cells | Reserve actual test hardware; one fresh-install permission/failure triad per claimed combination; retain unsupported labels until evidence exists |
| REA provider/session | Initial launch cleanup failures; some connect observations succeeded; tool availability changed | Reuse advertised connected tool if available, bind one task-owned browser target, run bounded scenario and verify disconnect/owned cleanup; no repeated global setup |

## Reproduction and handoff checklist

For a single future trial, choose one row/scenario, freeze its authority/run manifest, check artifact hashes and permissions, run the positive case, inject one named failure, run its boundary case and record cleanup. Write a bounded redacted result and raw-artifact digests. Independently review expected/observed outcomes at the exact candidate head. Update the feature matrix only for the actual tested target/build/platform. A future contributor should be able to rerun from recorded artifacts/configuration without inferring missing credentials, hidden normalizers or excluded failures.

Existing replay helpers execute narrower evidence only: [reproduce_ink_pure_units.mjs](reproduce_ink_pure_units.mjs) replays pinned pure Node tests; [studio_mechanism_probe.py](studio_mechanism_probe.py) replays timing/coroutine fixtures. Their success does not satisfy any native, human-audio, tenant-security, product-performance or release threshold in this proposal.
