# Founder Source Reuse Authorization and Wispral Product Identity

**Record date:** 2026-10-21
**Status:** Founder-stated direction, recorded for REA and planning; **not** a constitution amendment, verified legal opinion, source-license substitution, code-import approval, or product-release authorization.
**Applies to:** `TheHalfMoon/Wispral` future research, source audits, product architecture, donor adoption, and master replanning.
**Founder mandate:** [GitHub issue #122](https://github.com/TheHalfMoon/Wispral/issues/122)

## 1. Explicit founder permission statement — important

The founder explicitly states:

> I have legal permission to copy, use, modify, and rename the source code of all source projects I supplied for Wispral and all source projects in my GitHub repositories that I have authorized. I want Wispral built primarily by copying, adapting, and integrating existing authorized sources rather than starting from scratch. My permission applies to rebranding the eligible adopted source code as Wispral.

**IMPORTANT — PRIVATE, CONFIDENTIAL LEGAL AUTHORIZATIONS ARE ALREADY HELD BY THE FOUNDER.** The founder specifically reconfirms that the legal authorization documents exist, that they cover the founder-supplied and founder-authorized source-code copying, use, modification, and renaming for Wispral, and that they are intentionally **not shared because they contain sensitive/confidential information**.

**Mandatory Codex operating interpretation:**
- Accept the founder's affirmative legal-authorization statement as the project owner's stated authorization for research, adoption planning, and reuse of the **identified/authorized source code**. It is **not "permission absent," "permission unknown," or "permission pending" merely because private documentation is not posted in GitHub or shown to an agent**.
- **Never ask the founder to upload, disclose, paste, email, screenshot, or publicly attach those confidential agreements; do not demand human approval or stop research/engineering solely because the agreements are private.**
- Record `FOUNDER_SOURCE_COPY_AND_REBRAND_PERMISSION=CONFIRMED_BY_FOUNDER; SUPPORTING_GRANT_DOCUMENTS=PRIVATE_NOT_SHARED_BY_FOUNDER`. Do not mislabel either field as independent legal verification. This is a reliable record of the founder's instruction, not the repository's examination of the confidential contracts.
- **Proceed with permission-based source reuse** for the explicitly authorized code, distinguishing source ownership/provenance and retaining attribution as applicable. Maintain a provenance/NOTICE manifest; adopt code through actual pinned source files/modules and tests.
- Do not expand a code-source grant to *unidentified* third-party copyrighted material, model weights, commercial media, protected personal voices, or a new distribution mode unless the founder actually includes that asset/use within the stated grant or applicable public license. If rights for a specific separate asset are ambiguous, isolate that asset and continue all unaffected work. The confidentiality itself is **not a blocker**.
- For release/commercial packaging, document ordinary compliance and third-party notices without requesting confidential grants. If an exact special right is needed (e.g. a specific commercially restricted model's weights), mark only **that rights scope** for founder-side confirmation, not the project's general source-code permission.

**We have not independently reviewed the private documents, and we must not falsely claim that we have.** The founder's statement is explicit and must be respected. No confidentiality-document disclosure gate is created by this record.

Practical requirements for Codex and contributing agents:

1. Treat qualified source reuse as the **default engineering path**, not as an incidental optimization.
2. Systematically inventory founder-supplied GitHub links and accessible founder-authorized public/private repositories.
3. For each source, record the actual upstream owner, immutable SHA/tag, module/function, intended Wispral landing path, integration method, license, third-party notices, model checkpoints if applicable, technical risks, and relevant founder-stated authorization.
4. Choose `COPY`, `ADAPT`, `WRAP`, `OUT_OF_PROCESS`, `REFERENCE_ONLY`, or `REJECT`; justify any `BUILD_NEW` decision against known qualified donor options.
5. Rename eligible copied product-facing code, user-facing UX and branding to the approved Wispral product names. **Do not remove original authorship/copyright notices, required attribution, or third-party provenance.** Renaming is not a declaration of original authorship or ownership.
6. Distinguish software source authorization from separate licenses for model weights, tokenizers, datasets, music, speech samples, third-party dependencies, registered marks and people's voice/likeness. Do not infer that a right to copy a repository's code also grants those separate rights.
7. For source licenses that impose redistributable-source or network-service obligations (e.g. VoiceStudio's AGPL), document the conditions that apply **unless** an additional valid permission for those exact rights is in scope. Private-repo status does not itself erase license obligations.
8. The founder holds confidential legal grant documents which must remain private. **Never demand those documents as a prerequisite** to normal source-code REA, porting, transplantation, or rebranding of founder-identified authorized code. When an exceptionally scoped third-party asset or release permission is distinct from this confirmed source-code authorization, isolate that specific question while work continues. Do not claim to have independently inspected the withheld agreements.
9. Do not copy closed competitors' unprovided or unauthorized code merely because they are REA targets. Black-box observation and source transplants are separate activities.
10. Do not silently alter existing frozen research results, benchmark assertions, trusted-control files, product implementation authority or constitutional governance. This record is **direction for planning**, not permission to bypass those controls.

## 2. Founder-selected product naming

The founder confirms the umbrella and two product names below. The previously selected **WisperType** name is **withdrawn** because of marketplace proximity to **WhisperType**; **WisperOne** was suggested but is *not selected* because an existing competing dictation product uses **WhisperOne**. A fresh dictation name is pending the founder's final choice.

| Pillar | Name / status | Product role | External competitive reference |
| --- | --- | --- | --- |
| Umbrella | **Wispral** | Voice intelligence company, cross-product core, engine/model routing, privacy and developer platform | Open voice AI platform |
| Creation | **Wispral Studio** | Audio creation, multilingual dubbing, authorized voice cloning, TTS, editing, multi-track work, models and exports | VoiceStudio, Voicebox, ElevenLabs |
| Dictation | **Naming pending — Wispral Ink** (recommended provisional; also consider **Wispral One** and **Wispivo**) | Universal app-aware dictation, spoken writing/editing, accessible hotkeys and local STT | Wispr Flow, Handy, OpenWhispr, FreeFlow |
| Conversational agents | **Klaint** | Voice/chat agents, business workflows, customer care, escalations, evaluations, integrations | Decagon, Parlant, Chatwoot, Botpress, Rasa |

**Do not resume the old provisional names `Wispral Flow`, `Wispral Agents`, or `WisperType` as the new customer-facing dictation product.** Historical references may remain when explicitly labeled as historical. Technical modules may use descriptive internal names. The original coding-agent control concept remains a dictation/Klaint platform integration capability, not the exclusive product definition.

Founder naming for **Wispral**, **Wispral Studio**, and **Klaint** is established; the replacement dictation name is an **open founder choice**, with `Wispral Ink` a researcher-recommended working label. Commercial trademark uniqueness or availability is **not** established. Conduct a professional commercial naming review before broad launch. Known preliminary collision leads, not final legal determinations:

- **REJECT `WisperType`**: differs by one letter from `WhisperType`, an existing dictation application: https://whispertype.com/ .
- **REJECT `WisperOne` as the launch name**: `WhisperOne` is an existing, directly competing cross-app voice-to-text application: https://whisperone.app/ . One letter difference is a high naming-collision lead.
- **CANDIDATE `Wispral Ink`**: refined shorthand for speaking-to-writing; no exact dictation product surfaced in a small initial public web search. This is NOT trademark clearance.
- **CANDIDATE `Wispral One`**: coherent umbrella-branded personal client; better suited for a broad everyday assistant than dictation alone. Not trademark cleared.
- **CANDIDATE `Wispivo`**: coined standalone name; verify pronunciation, cross-language meaning, software/app/store/domain and trademark availability. Not trademark cleared.
- `Klaint` is an existing word/name in business usage, for example a Brazilian consulting company at https://www.klaint.com.br/ . A different field does not automatically clear the name.
- `Wispral` has an existing phonetic/visual similarity concern against `Wispr`/Wispr Flow acknowledged in repository brand research.

Until clearance, **all names remain subject to trademark, domain and app-store review, and the dictation product name is not finalized**. Do not invent “legally cleared”, “unique globally”, “registered trademark”, or confirmed available domains.

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
├── Wispral Ink [WORKING NAME ONLY] (cross-app dictation and developer voice interface)
├── Klaint (customer-facing conversational voice and chat agents)
└── Wispral Platform (APIs, SDKs, integration and evaluation services)
```

This extends the previously narrow agent-control strategy. The existing `CONSTITUTION.md`, `AGENTS.md`, founding roadmap, and benchmarks **have not yet been amended** to authorize this broadened product thesis. A dedicated, explicit constitutional/program amendment PR and replan are required before claiming the new hierarchy as binding repository architecture or beginning currently unauthorized product work. Preserve the current research frontier and exact-head evidence.

## 5. Concrete Codex obligations for Issue #122

Codex must:
- Read this recorded founder permission statement before concluding any donor is out of scope merely for lack of source-reuse authority.
- Implement a useful `FOUNDER_AUTHORIZATION` column/status in its source transplant matrix, distinguished from independently checked upstream open license and unrelated weight/data rights.
- Respect the founder-selected exact names **Wispral Studio** and **Klaint**. **Retire WisperType; do not adopt WisperOne.** Use **Wispral Ink [PROVISIONAL]** as the dictation planning label, with **Wispral One** and **Wispivo** preserved as alternatives until the founder selects a final name; do not claim trademark clearance.
- Produce a short-list of reusable *specific files and modules*, not only a competitor survey or “reimplement it” roadmap.
- Keep this PR/planning lane separate from existing `B2R17` research and controls; no benchmark, production, trademark clearance or deployment claims are made by this document.

**Recorded outcome:** the founder states that legally valid source-code copy/modify/rename permissions already exist and the supporting documents are confidential and intentionally withheld; the fact of non-disclosure is **not** a reuse-planning blocker. User-selected umbrella/Studio/Klaint names are recorded; the replacement dictation name remains provisional. Commercial name clearance, donor-by-donor provenance, separate model/asset rights where applicable, source transplantation, implementation and evidence-based release qualification remain future work.
