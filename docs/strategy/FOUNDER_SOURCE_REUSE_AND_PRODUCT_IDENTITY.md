# Founder Source Reuse Authorization and Wispral Product Identity

**Record date:** 2026-10-21
**Status:** Founder-stated direction, recorded for REA and planning; **not** a constitution amendment, verified legal opinion, source-license substitution, code-import approval, or product-release authorization.
**Applies to:** `TheHalfMoon/Wispral` future research, source audits, product architecture, donor adoption, and master replanning.
**Founder mandate:** [GitHub issue #122](https://github.com/TheHalfMoon/Wispral/issues/122)

## 1. Explicit founder permission statement — important

The founder explicitly states:

> I have legal permission to copy, use, modify, and rename the source code of all source projects I supplied for Wispral and all source projects in my GitHub repositories that I have authorized. I want Wispral built primarily by copying, adapting, and integrating existing authorized sources rather than starting from scratch. My permission applies to rebranding the eligible adopted source code as Wispral.

**This is recorded as the founder's own assertion of permission and engineering intent, not as a legal permission independently examined or authenticated by this repository.** Do **not** mischaracterize the founder as lacking any permission simply because a separate grant document was not committed to this repository. It is acceptable for private rights evidence to be stored outside the public tree and referenced by a non-sensitive record.

Practical requirements for Codex and contributing agents:

1. Treat qualified source reuse as the **default engineering path**, not as an incidental optimization.
2. Systematically inventory founder-supplied GitHub links and accessible founder-authorized public/private repositories.
3. For each source, record the actual upstream owner, immutable SHA/tag, module/function, intended Wispral landing path, integration method, license, third-party notices, model checkpoints if applicable, technical risks, and relevant founder-stated authorization.
4. Choose `COPY`, `ADAPT`, `WRAP`, `OUT_OF_PROCESS`, `REFERENCE_ONLY`, or `REJECT`; justify any `BUILD_NEW` decision against known qualified donor options.
5. Rename eligible copied product-facing code, user-facing UX and branding to the approved Wispral product names. **Do not remove original authorship/copyright notices, required attribution, or third-party provenance.** Renaming is not a declaration of original authorship or ownership.
6. Distinguish software source authorization from separate licenses for model weights, tokenizers, datasets, music, speech samples, third-party dependencies, registered marks and people's voice/likeness. Do not infer that a right to copy a repository's code also grants those separate rights.
7. For source licenses that impose redistributable-source or network-service obligations (e.g. VoiceStudio's AGPL), document the conditions that apply **unless** an additional valid permission for those exact rights is in scope. Private-repo status does not itself erase license obligations.
8. Do not demand public disclosure of confidential grants merely to proceed with research. For distribution or special rights beyond public license terms, record whether those specific rights are supported by available founder documentation or still need rights verification. Do not claim such verification has occurred unless it has.
9. Do not copy closed competitors' unprovided or unauthorized code merely because they are REA targets. Black-box observation and source transplants are separate activities.
10. Do not silently alter existing frozen research results, benchmark assertions, trusted-control files, product implementation authority or constitutional governance. This record is **direction for planning**, not permission to bypass those controls.

## 2. Founder-selected product naming

The founder has selected the following product-facing labels and exact spelling:

| Pillar | Founder-selected name | Product role | External competitive reference |
| --- | --- | --- | --- |
| Umbrella | **Wispral** | Voice intelligence company, cross-product core, engine/model routing, privacy and developer platform | Open voice AI platform |
| Creation | **Wispral Studio** | Audio creation, multilingual dubbing, authorized voice cloning, TTS, editing, multi-track work, models and exports | VoiceStudio, Voicebox, ElevenLabs |
| Dictation | **WisperType** | Universal app-aware dictation, spoken writing/editing, accessible hotkeys and local STT | Wispr Flow, Handy, OpenWhispr, FreeFlow |
| Conversational agents | **Klaint** | Voice/chat agents, business workflows, customer care, escalations, evaluations, integrations | Decagon, Parlant, Chatwoot, Botpress, Rasa |

**Do not replace these with the previous provisional consumer-brand names `Wispral Flow` and `Wispral Agents` in any new plans.** Legacy references may remain as explicitly labeled historical context, and technical modules may use descriptive internal names. The original coding-agent control concept remains a WisperType/Klaint platform integration capability, not the exclusive product definition.

Founder naming preference is established; commercial trademark uniqueness or availability is **not** established. Conduct a professional commercial naming review before broad launch. Known preliminary collision leads, not final legal determinations:

- `WisperType` differs by one letter from already used `WhisperType`, a speech-dictation product name: https://whispertype.com/ ; compare other similarly named software and registered marks.
- `Klaint` is an existing word/name in business usage, for example a Brazilian consulting company at https://www.klaint.com.br/ . A different field does not automatically clear the name.
- `Wispral` has an existing phonetic/visual similarity concern against `Wispr`/Wispr Flow acknowledged in repository brand research.

Until clearance, the labels are **founder-selected product names, pending trademark, domain and app-store review**. Do not invent “legally cleared”, “unique globally”, “registered trademark”, or confirmed available domains.

## 3. Founder-nominated source families for source-first REA

At minimum inventory, pin, classify and evaluate the following direct source candidates. This list is nonexclusive and must be extended with relevant authorized founder GitHub repositories:

- Studio and models: https://github.com/debpalash/VoiceStudio ; https://github.com/jamiepine/voicebox ; https://github.com/resemble-ai/chatterbox ; relevant CosyVoice, Kokoro, Qwen and Voxtral code/model artifacts when access and individual rights permit.
- Dictation: https://github.com/OpenWhispr/openwhispr ; https://github.com/cjpais/Handy ; https://github.com/zachlatta/freeflow ; additional qualified VoiceInk, whisper.cpp, sherpa-onnx, Moonshine components.
- Agents and customer service: https://github.com/emcie-co/parlant ; https://github.com/botpress/botpress ; https://github.com/chatwoot/chatwoot ; https://github.com/RasaHQ/rasa ; plus directly inspectable LiveKit Agents and Pipecat components.
- Authorized internal candidate repos: `TheHalfMoon/Orcel`, `TheHalfMoon/Hala`, `TheHalfMoon/Sentrdel`, `TheHalfMoon/Skilit`, `TheHalfMoon/Ninerr`, and any other founder-authorized repository that passes a concrete technical donor audit.

**Source donor vs competitive REA target:** Wispr Flow, Decagon and proprietary competitors are key functional benchmarks; they are not automatically declared copyable source code in the absence of specifically identified accessible authorized sources.

## 4. Architectural and planning consequence

The proposed long-term product hierarchy is:

```text
Wispral (umbrella platform)
├── Wispral Core (speech and realtime engine contracts, safety, consent, routing)
├── Wispral Studio (creation, production and dubbing)
├── WisperType (cross-app dictation and developer voice interface)
├── Klaint (customer-facing conversational voice and chat agents)
└── Wispral Platform (APIs, SDKs, integration and evaluation services)
```

This extends the previously narrow agent-control strategy. The existing `CONSTITUTION.md`, `AGENTS.md`, founding roadmap, and benchmarks **have not yet been amended** to authorize this broadened product thesis. A dedicated, explicit constitutional/program amendment PR and replan are required before claiming the new hierarchy as binding repository architecture or beginning currently unauthorized product work. Preserve the current research frontier and exact-head evidence.

## 5. Concrete Codex obligations for Issue #122

Codex must:
- Read this recorded founder permission statement before concluding any donor is out of scope merely for lack of source-reuse authority.
- Implement a useful `FOUNDER_AUTHORIZATION` column/status in its source transplant matrix, distinguished from independently checked upstream open license and unrelated weight/data rights.
- Respect the founder-selected exact names **Wispral Studio**, **WisperType**, and **Klaint** throughout the new master plan, with collision/clearance risk clearly labeled, not silently renamed.
- Produce a short-list of reusable *specific files and modules*, not only a competitor survey or “reimplement it” roadmap.
- Keep this PR/planning lane separate from existing `B2R17` research and controls; no benchmark, production, trademark clearance or deployment claims are made by this document.

**Recorded outcome:** founder rights assertion and naming decisions are visible to all future planning work; full rights verification, commercial naming clearance, source transplantation, implementation and evidence-based release qualification remain future work.
