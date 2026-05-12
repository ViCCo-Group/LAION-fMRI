"""LAION-fMRI dataset loader.

Top-level exports here intentionally avoid names that collide with
submodule names (e.g. ``download``, ``stimuli``) so that consumers can
keep doing ``from laion_fmri.download import download`` and
``monkeypatch.setattr("laion_fmri.download.download", ...)`` without
the function shadowing the module.

For downloading and access-service helpers, import from
:mod:`laion_fmri.download` directly.
"""

from laion_fmri.embeddings import Embeddings, load_embeddings
from laion_fmri.stimuli import Stimuli, load_stimuli

# These don't collide with a module name (the module is `download`, not
# `download_stimuli` / `request_stimulus_access`), so re-exporting at the
# top level is safe.
from laion_fmri.download import (  # noqa: E402
    download_embeddings,
    download_stimuli,
    request_stimulus_access,
)

__all__ = [
    "Embeddings",
    "Stimuli",
    "download_embeddings",
    "download_stimuli",
    "load_embeddings",
    "load_stimuli",
    "request_stimulus_access",
]
