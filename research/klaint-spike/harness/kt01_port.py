# Wispral KT-01: run Parlant's own hook tests unchanged on the deterministic fake provider.
# Loaded with `-p kt01_port`. It only installs the "fake" provider and switches SDKTest's default
# model map from {"*": "gemini"} to {"*": "fake"}; no upstream test file is edited.
import fake_provider

fake_provider.install()


def pytest_configure(config):
    from tests.sdk import utils
    utils.SDKTest.MODELS = {"*": "fake"}
