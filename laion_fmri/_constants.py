"""Constants for the laion_fmri package."""

from laion_fmri._errors import SubjectNotFoundError

LICENSE_AGREEMENT_BODY = """\
=== LAION-fMRI Dataset License (CC0 1.0) ===

The brain imaging and participant data in the LAION-fMRI dataset are
released under the Creative Commons Zero (CC0 1.0) Public Domain
Dedication. You are free to copy, modify, distribute, and use the
data for any purpose, including commercial, without asking permission.

Full license text: https://creativecommons.org/publicdomain/zero/1.0/

NOTE: Stimulus images are NOT covered by CC0. They are subject to a
separate, restrictive license. You will be prompted to accept it if
you choose to download stimuli.
"""

LICENSE_AGREEMENT_PROMPT = (
    'Type "I AGREE" to accept and continue with the download: '
)

LICENSE_AGREEMENT_TEXT = LICENSE_AGREEMENT_BODY + LICENSE_AGREEMENT_PROMPT


STIMULI_LICENSE_BODY = """\
=== LAION-fMRI Stimulus License ===

The LAION-fMRI stimulus images are provided under a closed license.
All rights are reserved by the original copyright holders.

You may ONLY use these images for non-commercial academic research.
All other uses are strictly prohibited. In particular, you may NOT:

  1. Share, redistribute, or make the images available to others.
  2. Use the images for any commercial purpose.
  3. Use the images to train, fine-tune, or evaluate commercial
     AI/ML models or services.
  4. Create derivative works from the images for any purpose
     other than non-commercial academic research.

Full terms: https://laion-fmri.github.io/terms
"""

STIMULI_LICENSE_PROMPT = 'Type "I AGREE" to accept: '

STIMULI_LICENSE_TEXT = STIMULI_LICENSE_BODY + STIMULI_LICENSE_PROMPT

TERMS_OF_USE_TEXT = STIMULI_LICENSE_TEXT


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
