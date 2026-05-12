"""LAION-fMRI dataset loader.

Top-level exports here intentionally avoid names that collide with
submodule names (e.g. ``download``, ``stimuli``) so that consumers can
keep doing ``from laion_fmri.download import download`` and
``monkeypatch.setattr("laion_fmri.download.download", ...)`` without
the function shadowing the module.

For downloading and access-service helpers, import from
:mod:`laion_fmri.download` directly.
"""

from laion_fmri.captions import Captions
from laion_fmri.embeddings import Embeddings
from laion_fmri.segmentations import Segmentations
from laion_fmri.stimuli import Stimuli, load_stimuli
from laion_fmri.subject import Subject, load_subject

# These don't collide with a module name (the module is `download`, not
# `download_stimuli` / `request_stimulus_access`), so re-exporting at the
# top level is safe.
from laion_fmri.download import (  # noqa: E402
    download_captions,
    download_embeddings,
    download_segmentations,
    download_stimuli,
    request_stimulus_access,
)

__all__ = [
    "Captions",
    "Embeddings",
    "Segmentations",
    "Stimuli",
    "Subject",
    "download_captions",
    "download_embeddings",
    "download_segmentations",
    "download_stimuli",
    "load_stimuli",
    "load_subject",
    "request_stimulus_access",
]
