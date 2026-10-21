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

## 2. Final founder-selected product naming

**Founder decision date:** 2026-10-21. **Status:** Final founder choice for product naming and planning; separate trademark/domain/app-store clearance is not established by this record.

**Use the exact names and capitalization below in all new Wispral product planning, roadmaps, specifications, examples, product UI proposals, architecture diagrams, and transplants.**

| Product | Exact founder-selected name | Product role |
| --- | --- | --- |
| Umbrella | **Wispral** | Voice intelligence platform, shared core, models, routing, privacy, interoperability and developer tooling |
| Creative studio | **WisprStudio** | Voice creation, authorized voice cloning, speech synthesis, editing, multilingual dubbing and audio production |
| Voice typing | **WisprInk** | Cross-application dictation, contextual voice-to-text, spoken writing/editing and developer voice interaction |
| Conversational agents | **Klaint** | AI voice/chat agents, business workflows, customer experience, escalations, testing, integrations and enterprise controls |

**Superseded historical names — NOT approved customer-facing brands:**

- `Wispral Studio` → **WisprStudio**.
- `WisperType`, `WisperOne`, `Wispral Ink`, `WisprInk [PROVISIONAL]`, `Wispral One` and `Wispivo` → **WisprInk**.
- `Wispral Flow` and `Wispral Agents` were early working labels and must not be promoted as these product names. The corresponding capabilities map into WisprInk and Klaint.
- Historic citations, archived research and PR conversation may preserve the old names if explicitly identified as historical. Do not rewrite or falsify frozen evidence to erase them.

**Developer instruction:** The names are chosen; do not re-open a naming brainstorm or ask the founder to select among alternatives. Do not block independent REA or architecture work awaiting public trademark clearance. Do not invent a legal clearance or domain ownership claim: conduct an explicit clearance review ahead of commercial launch, including the recorded Wispr/Wispr Flow similarity issue, as separate non-blocking planning work.

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
├── WisprStudio (creation, production and dubbing)
├── WisprInk (cross-app dictation and developer voice interface)
├── Klaint (customer-facing conversational voice and chat agents)
└── Wispral Platform (APIs, SDKs, integration and evaluation services)
```

This extends the previously narrow agent-control strategy. The existing `CONSTITUTION.md`, `AGENTS.md`, founding roadmap, and benchmarks **have not yet been amended** to authorize this broadened product thesis. A dedicated, explicit constitutional/program amendment PR and replan are required before claiming the new hierarchy as binding repository architecture or beginning currently unauthorized product work. Preserve the current research frontier and exact-head evidence.

## 5. Concrete Codex obligations for Issue #122

Codex must:
- Read this recorded founder permission statement before concluding any donor is out of scope merely for lack of source-reuse authority.
- Implement a useful `FOUNDER_AUTHORIZATION` column/status in its source transplant matrix, distinguished from independently checked upstream open license and unrelated weight/data rights.
- Use the **final founder-selected product names** exactly: **Wispral** (platform), **WisprStudio** (studio), **WisprInk** (voice typing), **Klaint** (voice/chat agents). Do not silently revert to historical names or request a new naming decision. Trademark/domain/app-store clearance remains a separate prelaunch check.
- Produce a short-list of reusable *specific files and modules*, not only a competitor survey or “reimplement it” roadmap.
- Keep this PR/planning lane separate from existing `B2R17` research and controls; no benchmark, production, trademark clearance or deployment claims are made by this document.

**Recorded outcome:** the founder states that legally valid source-code copy/modify/rename permissions already exist and the supporting documents are confidential and intentionally withheld; the fact of non-disclosure is **not** a reuse-planning blocker. Founder-selected final platform and product names (Wispral, WisprStudio, WisprInk and Klaint) are recorded; public naming clearance remains a separate launch qualification. Commercial name clearance, donor-by-donor provenance, separate model/asset rights where applicable, source transplantation, implementation and evidence-based release qualification remain future work.
