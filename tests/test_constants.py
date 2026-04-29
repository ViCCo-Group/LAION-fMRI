import pytest

from laion_fmri._constants import (
    LICENSE_AGREEMENT_BODY,
    LICENSE_AGREEMENT_PROMPT,
    LICENSE_AGREEMENT_TEXT,
    STIMULI_LICENSE_BODY,
    STIMULI_LICENSE_PROMPT,
    STIMULI_LICENSE_TEXT,
    TERMS_OF_USE_TEXT,
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


# ── License texts ───────────────────────────────────────────────


def test_terms_of_use_text_is_nonempty():
    assert isinstance(TERMS_OF_USE_TEXT, str)
    assert len(TERMS_OF_USE_TEXT) > 0
    assert "I AGREE" in TERMS_OF_USE_TEXT


def test_license_agreement_text_is_nonempty():
    assert isinstance(LICENSE_AGREEMENT_TEXT, str)
    assert len(LICENSE_AGREEMENT_TEXT) > 0
    assert "I AGREE" in LICENSE_AGREEMENT_TEXT
    assert "CC0" in LICENSE_AGREEMENT_TEXT


def test_stimuli_license_text_is_nonempty():
    assert isinstance(STIMULI_LICENSE_TEXT, str)
    assert len(STIMULI_LICENSE_TEXT) > 0
    assert "I AGREE" in STIMULI_LICENSE_TEXT
    assert "non-commercial" in STIMULI_LICENSE_TEXT


def test_terms_of_use_is_stimuli_license():
    assert TERMS_OF_USE_TEXT is STIMULI_LICENSE_TEXT


def test_dataset_and_stimuli_licenses_are_distinct():
    assert LICENSE_AGREEMENT_TEXT != STIMULI_LICENSE_TEXT


def test_license_body_does_not_contain_prompt():
    """``BODY`` is display-only; the input-prompt suffix lives
    separately so callers that just print the license don't
    create the illusion of an awaiting prompt."""
    assert "I AGREE" not in LICENSE_AGREEMENT_BODY
    assert "I AGREE" not in STIMULI_LICENSE_BODY


def test_full_text_is_body_plus_prompt():
    assert (
        LICENSE_AGREEMENT_TEXT
        == LICENSE_AGREEMENT_BODY + LICENSE_AGREEMENT_PROMPT
    )
    assert (
        STIMULI_LICENSE_TEXT
        == STIMULI_LICENSE_BODY + STIMULI_LICENSE_PROMPT
    )
