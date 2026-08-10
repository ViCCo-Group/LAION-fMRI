"""PyTorch Dataset integration for laion_fmri."""

import importlib.util

import numpy as np


def _check_torch_available():
    """Raise ImportError if torch is not installed."""
    if importlib.util.find_spec("torch") is None:
        raise ImportError(
            "PyTorch is required for LaionFMRIDataset. Install it with: "
            "python -m pip install 'laion-fmri[torch] @ "
            "git+https://github.com/ViCCo-Group/LAION-fMRI.git@main'"
        )


def _resolve_rep_indices(trial_info):
    """Return a per-trial ``rep_index`` array.

    Real bucket trial TSVs ship only ``session/run/beta_index/
    label`` -- no ``rep_index`` column -- so the index is
    derived by counting prior occurrences of each stimulus
    identifier. When the column is already present (synthetic
    fixtures, future schemas), it's used verbatim.
    """
    if "rep_index" in trial_info.columns:
        return trial_info["rep_index"].to_numpy()
    if "label" in trial_info.columns:
        ids = trial_info["label"]
    elif "stimulus_id" in trial_info.columns:
        ids = trial_info["stimulus_id"]
    else:
        raise ValueError(
            "Trial info has neither 'label' nor 'stimulus_id' "
            "column; cannot derive rep_index."
        )
    seen = {}
    rep = []
    for sid in ids:
        rep.append(seen.get(sid, 0))
        seen[sid] = seen.get(sid, 0) + 1
    return np.array(rep)


class LaionFMRIDataset:
    """PyTorch Dataset wrapping one session of a LAION-fMRI subject.

    Parameters
    ----------
    subject : laion_fmri.subject.Subject
        A loaded subject object.
    session : str
        BIDS session ID. Required -- single-trial betas are stored
        per session.
    roi : str or None
        ROI name for voxel selection.
    mask : np.ndarray[bool] or None
        Custom boolean mask.
    nc_threshold : float or None
        Minimum noise ceiling for voxel inclusion.
    image_transform : callable or None
        Transform applied to image tensors.
    mask_source : ``"anatomical"`` (default) | ``"rsquare"``
        Forwarded to :meth:`Subject.get_betas`; see
        :meth:`Subject.get_brain_mask` for the difference.
    """

    def __init__(
        self,
        subject,
        session,
        roi=None,
        mask=None,
        nc_threshold=None,
        image_transform=None,
        mask_source="anatomical",
    ):
        _check_torch_available()
        import torch

        self._subject = subject
        self._session = session
        self._image_transform = image_transform
        self._torch = torch

        self._betas = subject.get_betas(
            session=session,
            roi=roi,
            mask=mask,
            nc_threshold=nc_threshold,
            mask_source=mask_source,
        )
        # Slice the subject's global trial table down to this session,
        # preserving global trial indices.
        trial_table = subject.metadata
        self._session_rows = trial_table[
            trial_table["session"] == session
        ].reset_index(drop=False).rename(columns={"index": "global_trial"})
        self._rep_indices = _resolve_rep_indices(
            subject.get_trial_info(session=session),
        )
        self._subject = subject

    def __len__(self):
        return len(self._betas)

    def __getitem__(self, idx):
        betas_tensor = self._torch.tensor(
            self._betas[idx], dtype=self._torch.float32,
        )

        global_trial = int(self._session_rows.iloc[idx]["global_trial"])
        img = self._subject.images.get(global_trial, as_displayed=True)
        img_array = np.array(img, dtype=np.float32) / 255.0
        img_tensor = self._torch.tensor(
            img_array.transpose(2, 0, 1),
        )

        if self._image_transform is not None:
            img_tensor = self._image_transform(img_tensor)

        return {
            "betas": betas_tensor,
            "image": img_tensor,
            "image_name": self._session_rows.iloc[idx]["image_name"],
            "session": self._session,
            "rep_index": int(self._rep_indices[idx]),
        }
