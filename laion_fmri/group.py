"""Multi-subject Group wrapper for cross-subject analyses."""

from laion_fmri.discovery import get_subjects
from laion_fmri.subject import load_subject


def load_subjects(subjects):
    """Load multiple subjects into a Group.

    Parameters
    ----------
    subjects : list[str | int] or "all"
        List of subject identifiers, or ``"all"`` to load every
        subject in the dataset.

    Returns
    -------
    Group
    """
    if subjects == "all":
        subject_ids = get_subjects()
    else:
        subject_ids = subjects

    subjects_dict = {}
    for sub in subject_ids:
        s = load_subject(sub)
        subjects_dict[s.subject_id] = s

    return Group(subjects_dict)


class Group:
    """Holds several ``Subject`` instances and dispatches to them.

    Parameters
    ----------
    subjects_dict : dict[str, laion_fmri.subject.Subject]
        Mapping of BIDS ID to loaded subject objects.
    """

    def __init__(self, subjects_dict):
        self._subjects = dict(subjects_dict)
        self._ordered_ids = sorted(self._subjects.keys())

    def __len__(self):
        return len(self._subjects)

    def __getitem__(self, key):
        if isinstance(key, int):
            sub_id = self._ordered_ids[key]
            return self._subjects[sub_id]
        if isinstance(key, str):
            if key not in self._subjects:
                raise KeyError(f"Subject '{key}' not in group.")
            return self._subjects[key]
        raise TypeError(
            f"Key must be int or str, got {type(key).__name__}"
        )

    def __iter__(self):
        for sub_id in self._ordered_ids:
            yield sub_id, self._subjects[sub_id]

    # ── Cross-subject loaders ───────────────────────────────────

    def get_shared_betas(
        self, session, roi=None, mask=None, nc_threshold=None,
        mask_source="anatomical",
    ):
        """Load shared-stimulus single-trial betas for all subjects.

        Parameters
        ----------
        session : str
            BIDS session ID. Required -- single-trial betas are
            stored per session.
        roi : str or None
        mask : np.ndarray[bool] or None
        nc_threshold : float or None
        mask_source : ``"anatomical"`` (default) | ``"rsquare"``
            Forwarded to :meth:`Subject.get_betas`; see
            :meth:`Subject.get_brain_mask` for the difference.

        Returns
        -------
        dict[str, np.ndarray]
            Mapping of subject ID to a betas array of shape
            ``(n_shared_trials, n_voxels)``.
        """
        result = {}
        for sub_id, sub in self:
            result[sub_id] = sub.get_betas(
                session=session,
                stimuli="shared",
                roi=roi,
                mask=mask,
                nc_threshold=nc_threshold,
                mask_source=mask_source,
            )
        return result

    def get_shared_images(self, format="pil"):
        """Load shared stimulus images from disk.

        Parameters
        ----------
        format : ``"pil"`` or ``"numpy"``
            Output container -- a list of :class:`PIL.Image.Image`
            or a stacked ``(N, H, W, 3)`` uint8 array.
        """
        from laion_fmri.stimuli import Stimuli
        meta = self.get_shared_stimulus_metadata()
        with Stimuli(data_dir=self._data_dir()) as stim:
            images = [
                stim.images.get(
                    name,
                    as_displayed=(format == "numpy"),
                )
                for name in meta["image_name"]
            ]
        if format == "pil":
            return images
        if format == "numpy":
            import numpy as np
            return np.stack([np.array(img) for img in images]).astype(np.uint8)
        raise ValueError(f"Unknown format: {format!r}")

    def get_shared_stimulus_metadata(self):
        """Return the shared subset of the stimulus metadata."""
        import pandas as pd
        from laion_fmri._paths import stimuli_metadata_path
        path = stimuli_metadata_path(self._data_dir())
        meta = pd.read_csv(path)
        return meta[meta["unique_or_shared"] == "shared"].reset_index(drop=True)

    def _data_dir(self):
        """All subjects share the same data dir; return it via the first."""
        return self._subjects[self._ordered_ids[0]]._data_dir
