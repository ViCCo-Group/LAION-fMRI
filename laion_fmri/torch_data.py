"""PyTorch Dataset integration for laion_fmri."""

import importlib.util

import numpy as np

from laion_fmri._paths import stimuli_dir_path


def _check_torch_available():
    """Raise ImportError if torch is not installed."""
    if importlib.util.find_spec("torch") is None:
        raise ImportError(
            "PyTorch is required for LaionFMRIDataset. "
            "Install it with: pip install laion-fmri[torch]"
        )


class LaionFMRIDataset:
    """PyTorch Dataset wrapping one session of a LAION-fMRI subject.

    Parameters
    ----------
    subject : Subject
        A loaded Subject instance.
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
    """

    def __init__(
        self,
        subject,
        session,
        roi=None,
        mask=None,
        nc_threshold=None,
        image_transform=None,
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
        )
        self._stim_meta = subject.get_stimulus_metadata()
        self._trial_info = subject.get_trial_info(session=session)
        self._stim_indices = subject.get_trial_stimulus_indices(
            session=session,
        )

        stim_dir = stimuli_dir_path(subject._data_dir)
        self._image_paths = [
            stim_dir / fn for fn in self._stim_meta["filename"]
        ]

    def __len__(self):
        return len(self._betas)

    def __getitem__(self, idx):
        from PIL import Image

        betas_tensor = self._torch.tensor(
            self._betas[idx], dtype=self._torch.float32,
        )

        stim_idx = int(self._stim_indices[idx])
        img = Image.open(
            self._image_paths[stim_idx],
        ).convert("RGB")
        img_array = np.array(img, dtype=np.float32) / 255.0
        # HWC -> CHW
        img_tensor = self._torch.tensor(
            img_array.transpose(2, 0, 1),
        )

        if self._image_transform is not None:
            img_tensor = self._image_transform(img_tensor)

        trial_row = self._trial_info.iloc[idx]
        return {
            "betas": betas_tensor,
            "image": img_tensor,
            "stimulus_id": self._stim_meta.iloc[stim_idx][
                "stimulus_id"
            ],
            "session": self._session,
            "rep_index": int(trial_row["rep_index"]),
        }
