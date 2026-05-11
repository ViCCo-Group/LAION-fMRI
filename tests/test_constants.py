import pytest

from laion_fmri._constants import (
    ACCESS_SERVICE_URL,
    LICENSE_AGREEMENT_BODY,
    LICENSE_AGREEMENT_PROMPT,
    LICENSE_AGREEMENT_TEXT,
    resolve_subject_id,
)
from laion_fmri._errors import SubjectNotFoundError


# ── resolve_subject_id ──────────────────────────────────────────


def test_resolve_subject_id_full_bids():
    assert resolve_subject_id("sub-01") == "sub-01"
    assert resolve_subject_id("sub-03") == "sub-03"


def test_resolve_subject_id_bare_value():
    """The BIDS-bare value is normalized to ``sub-XX``."""
    assert resolve_subject_id("01") == "sub-01"
    assert resolve_subject_id("03") == "sub-03"


def test_resolve_subject_id_alphanumeric_value():
    assert resolve_subject_id("ABC123") == "sub-ABC123"


def test_resolve_subject_id_rejects_int():
    with pytest.raises(TypeError, match="string"):
        resolve_subject_id(1)


def test_resolve_subject_id_rejects_float():
    with pytest.raises(TypeError, match="string"):
        resolve_subject_id(1.5)


def test_resolve_subject_id_rejects_none():
    with pytest.raises(TypeError, match="string"):
        resolve_subject_id(None)


def test_resolve_subject_id_rejects_empty_string():
    with pytest.raises(SubjectNotFoundError):
        resolve_subject_id("")


def test_resolve_subject_id_rejects_bare_prefix():
    with pytest.raises(SubjectNotFoundError):
        resolve_subject_id("sub-")


# ── CC0 license text (stimulus terms moved to the access service) ─


def test_license_agreement_text_is_nonempty():
    assert isinstance(LICENSE_AGREEMENT_TEXT, str)
    assert len(LICENSE_AGREEMENT_TEXT) > 0
    assert "I AGREE" in LICENSE_AGREEMENT_TEXT
    assert "CC0" in LICENSE_AGREEMENT_TEXT


def test_license_body_does_not_contain_prompt():
    assert "I AGREE" not in LICENSE_AGREEMENT_BODY


def test_full_text_is_body_plus_prompt():
    assert (
        LICENSE_AGREEMENT_TEXT
        == LICENSE_AGREEMENT_BODY + LICENSE_AGREEMENT_PROMPT
    )


# ── Access service URL ─────────────────────────────────────────


def test_access_service_url_default():
    assert ACCESS_SERVICE_URL == "https://laion-fmri.hebartlab.com"


def test_access_service_url_overridable(monkeypatch):
    monkeypatch.setenv("LAION_FMRI_ACCESS_URL", "https://staging.example.com/")
    import importlib
    import laion_fmri._constants as c
    importlib.reload(c)
    try:
        assert c.ACCESS_SERVICE_URL == "https://staging.example.com"
    finally:
        monkeypatch.delenv("LAION_FMRI_ACCESS_URL", raising=False)
        importlib.reload(c)
