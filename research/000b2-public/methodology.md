# 000B2 Public-Corpus Execution Methodology

## Decision

Replace the unstarted private participant-collection execution path with a public-corpus execution lane for the founding STT comparison.

This is a prospective methodology supersession. It does not rewrite or invalidate the historical B1 preregistration evidence. No primary human developer-speech decoding occurred under the old path.

## Motivation

The private 20-speaker path is structurally prepared but externally dependent on participant/media authority and private recording operations. That dependency is not necessary to answer the narrower founding decision: whether current local STT candidates are operationally viable enough to produce a bounded shortlist for a replaceable first-product speech boundary.

The parent `000B` specification already allows closure when human developer-speech evidence is absent, provided the absence is explicit enough to prevent false ranking. The amended lane exercises that option directly rather than fabricating consent, collecting unnecessary private data, or allowing the project to remain indefinitely blocked.

## Public human corpus

Primary public-human baseline:

- resource: LibriSpeech ASR corpus, OpenSLR SLR12;
- source: `https://www.openslr.org/12/`;
- license recorded by OpenSLR: `CC BY 4.0`;
- official `test-clean.tar.gz` MD5: `32fa31d27d2e1cad72775fee3f4849a9`;
- official `test-other.tar.gz` MD5: `fb5a50374b501bb3bac4815ee91d3135`;
- official checksum source: `https://www.openslr.org/resources/12/md5sum.txt`.

The benchmark will additionally compute SHA-256 over the exact fetched archive bytes and over every selected/preprocessed audio artifact.

## Why LibriSpeech is used

LibriSpeech is not developer speech. It is used because it provides openly distributed, labeled human English speech suitable for a reproducible ordinary-recognition baseline without new private data collection.

The project therefore limits claims to the exact frozen public subset and ordinary read-English recognition behavior.

## Developer vocabulary handling

Developer identifiers and repository terms remain product-relevant but cannot be honestly evaluated as human developer speech without suitable human media.

A separately frozen synthetic developer-term stress lane may therefore be used only as a diagnostic. It can reveal obvious token/vocabulary failures and provide stable regression material, but it cannot establish human developer-speech accuracy or accent/cadence robustness.

## Decision consequence

B2 can produce a public-baseline shortlist or insufficient-evidence conclusion. B3 may test deterministic repository resolution on frozen C0 transcripts and diagnostic developer material. B4 and 000G must carry forward the explicit uncertainty:

`HUMAN_DEVELOPER_SPEECH_ACCURACY_EVIDENCE=ABSENT`

A first product Grain, if eventually selected by 000G, must preserve a replaceable speech backend boundary and must not market the selected default as proven best for human developer speech.

## Privacy consequence

This lane does not require new Wispral participant identities, signatures, consent artifacts, private raw audio, identity mappings, or withdrawal records. Historical private-authority preparation remains preserved but is not an active gate for this lane.

## Reproducibility consequence

Public distribution does not remove provenance rigor. The execution still requires exact source URLs, upstream checksums, exact fetched-byte SHA-256 values, deterministic subset selection, frozen manifests, identical audio across candidates, exact runtime/model/config provenance, scorer freeze, attempt chronology, raw outputs, failures, and independent review.

## Invalid interpretations

The amendment must not be interpreted as evidence that:

- consent is unnecessary when Wispral itself records people;
- public audiobook speech is representative developer speech;
- synthetic speech is equivalent to human speech;
- general STT superiority has been established;
- the product may add a permanent STT dependency before 000G.
