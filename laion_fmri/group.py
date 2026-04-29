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
    """Lightweight wrapper around several Subjects.

    Parameters
    ----------
    subjects_dict : dict[str, Subject]
        Mapping of BIDS ID to Subject.
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
            )
        return result

    def get_shared_images(self, format="pil"):
        """Load shared stimulus images from the first subject."""
        first_sub = self._subjects[self._ordered_ids[0]]
        return first_sub.get_images(
            stimuli="shared", format=format,
        )

    def get_shared_stimulus_metadata(self):
        """Return the shared subset of the stimulus-metadata TSV."""
        first_sub = self._subjects[self._ordered_ids[0]]
        meta = first_sub.get_stimulus_metadata()
        return meta[meta["shared"]].reset_index(drop=True)
