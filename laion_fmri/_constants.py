"""Constants for the laion_fmri package."""

import os

from laion_fmri._errors import SubjectNotFoundError

# Base URL of the LAION-fMRI access service. Overridable via env for staging.
ACCESS_SERVICE_URL = os.environ.get(
    "LAION_FMRI_ACCESS_URL", "https://laion-fmri.hebartlab.com"
).rstrip("/")


LICENSE_AGREEMENT_BODY = """\
=== LAION-fMRI Dataset License (CC0 1.0) ===

The brain imaging and participant data in the LAION-fMRI dataset are
released under the Creative Commons Zero (CC0 1.0) Public Domain
Dedication. You are free to copy, modify, distribute, and use the
data for any purpose, including commercial, without asking permission.

Full license text: https://creativecommons.org/publicdomain/zero/1.0/

NOTE: Raw stimulus images are NOT covered by CC0. They are gated by a
separate Data Use Agreement enforced by the access service at
https://laion-fmri.hebartlab.com/terms — see
``laion-fmri request-access`` to obtain an image download. Stimulus
metadata, captions, embeddings, and segmentations are public
stimulus-derived files.
"""

LICENSE_AGREEMENT_PROMPT = (
    'Type "I AGREE" to accept and continue with the download: '
)

LICENSE_AGREEMENT_TEXT = LICENSE_AGREEMENT_BODY + LICENSE_AGREEMENT_PROMPT


def resolve_subject_id(subject):
    """Normalize a BIDS subject identifier to ``sub-XX`` form.

    Accepts either the full BIDS form (``"sub-01"``) or just the
    bare value (``"01"``). The actual existence of the subject is
    not checked here -- that's resolved against the bucket on
    download.

    Parameters
    ----------
    subject : str
        BIDS subject ID (e.g. ``"sub-01"``) or just its value
        (e.g. ``"01"``).

    Returns
    -------
    str
        The normalized BIDS subject ID, always in ``sub-XX`` form.

    Raises
    ------
    TypeError
        If ``subject`` is not a string.
    SubjectNotFoundError
        If ``subject`` is empty or has no value after the prefix.
    """
    if not isinstance(subject, str):
        raise TypeError(
            "subject must be a string in BIDS form "
            f"(e.g. 'sub-01' or '01'); got "
            f"{type(subject).__name__}."
        )
    if not subject or subject == "sub-":
        raise SubjectNotFoundError(
            f"Empty subject identifier: {subject!r}"
        )
    if subject.startswith("sub-"):
        return subject
    return f"sub-{subject}"
