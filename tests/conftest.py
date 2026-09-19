import pytest

from sdoc.config import settings
from sdoc.inbox import LocalInbox


@pytest.fixture(scope="session")
def inbox():
    if not (settings.data_dir / "inbox").is_dir():
        pytest.skip("participant dataset not present")
    return LocalInbox(settings.data_dir)
