"""LAION-fMRI dataset loader.

Top-level re-exports skip submodule names (e.g. ``download``,
``stimuli``) so the submodules themselves remain importable
without shadowing -- ``from laion_fmri.download import download``
and ``monkeypatch.setattr("laion_fmri.download.download", ...)``
keep working.

For downloading and access-service helpers, import from
:mod:`laion_fmri.download` directly.
"""

from importlib.metadata import PackageNotFoundError, version

from laion_fmri._constants import resolve_subject_id
from laion_fmri._errors import (
    DataDirNotSetError,
    DataNotDownloadedError,
    DataNotFoundError,
    LicenseNotAcceptedError,
    NoMatchingDataError,
    StimuliNotDownloadedError,
    SubjectNotFoundError,
)
from laion_fmri.captions import Captions
from laion_fmri.config import dataset_initialize, get_data_dir
from laion_fmri.discovery import describe, get_rois, get_subjects
from laion_fmri.embeddings import Embeddings, load_embeddings
from laion_fmri.group import Group, load_subjects
from laion_fmri.segmentations import Segmentations
from laion_fmri.stimuli import Stimuli, as_displayed_rgb, load_stimuli
from laion_fmri.subject import Subject, load_subject

try:
    __version__ = version("laion-fmri")
except PackageNotFoundError:
    __version__ = "0+unknown"

set_data_dir = dataset_initialize

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
    "DataDirNotSetError",
    "DataNotDownloadedError",
    "DataNotFoundError",
    "Embeddings",
    "Group",
    "LicenseNotAcceptedError",
    "NoMatchingDataError",
    "Segmentations",
    "StimuliNotDownloadedError",
    "Stimuli",
    "Subject",
    "SubjectNotFoundError",
    "__version__",
    "as_displayed_rgb",
    "dataset_initialize",
    "describe",
    "download_captions",
    "download_embeddings",
    "download_segmentations",
    "download_stimuli",
    "get_data_dir",
    "get_rois",
    "get_subjects",
    "load_embeddings",
    "load_subjects",
    "load_stimuli",
    "load_subject",
    "request_stimulus_access",
    "resolve_subject_id",
    "set_data_dir",
]
