TASK = "B2R14"
MATERIAL_CLASS = "DETERMINISTIC_SYNTHETIC_NON_PRIMARY_FIXTURE_ONLY"
FIXTURE_ID = "b2r14-sherpa-result-string-contract-v1"
SAMPLE_FORMAT = "PCM_S16LE"
PCM_SHA256 = "0c92bddb4e96f3ea9ec9f0f64a668255a6c15527ac09f6f119cafde60c7c4a39"

# Corrective requalification preserves this exact callable contract unchanged.
def extract_result(recognizer, stream):
    return recognizer.get_result(stream)
