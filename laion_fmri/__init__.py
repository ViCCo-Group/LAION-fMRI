"""LAION-fMRI dataset loader.

Top-level exports here intentionally avoid names that collide with
submodule names (e.g. ``download``, ``stimuli``) so that consumers can
keep doing ``from laion_fmri.download import download`` and
``monkeypatch.setattr("laion_fmri.download.download", ...)`` without
the function shadowing the module.

For downloading and access-service helpers, import from
:mod:`laion_fmri.download` directly.
"""

from laion_fmri.stimuli import (
    Stimuli,
    load_stimulus,
    load_stimulus_metadata,
)

__all__ = [
    "Stimuli",
    "load_stimulus",
    "load_stimulus_metadata",
]
