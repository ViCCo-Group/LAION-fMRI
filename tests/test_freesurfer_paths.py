"""Tests for FreeSurfer-recon path-builders in ``laion_fmri._paths``.

The recon ships per-subject under ``derivatives/freesurfer/sub-XX/``
and is what the template-space chain (``laion_fmri.templates``)
reads to project T1w-volume data onto fsnative surfaces and to
apply the ``talairach.lta`` affine for MNI305.
"""

from laion_fmri._paths import (
    freesurfer_mri_path,
    freesurfer_subject_dir,
    freesurfer_surf_path,
    freesurfer_transforms_dir,
)


def test_freesurfer_subject_dir_resolves(synthetic_data_dir):
    """The recon root for a subject is at the BIDS-standard path."""
    fs_dir = freesurfer_subject_dir(synthetic_data_dir, "sub-01")
    assert fs_dir.is_dir()
    assert fs_dir.name == "sub-01"
    assert fs_dir.parent.name == "freesurfer"


def test_freesurfer_mri_path_brain_mgz(synthetic_data_dir):
    """``mri/brain.mgz`` resolves through the path-builder."""
    path = freesurfer_mri_path(
        synthetic_data_dir, "sub-01", "brain.mgz",
    )
    assert path.is_file()
    assert path.parent.name == "mri"


def test_freesurfer_mri_path_arbitrary_filename(synthetic_data_dir):
    """The builder accepts any filename under ``mri/``."""
    path = freesurfer_mri_path(
        synthetic_data_dir, "sub-01", "aparc+aseg.mgz",
    )
    assert path.is_file()


def test_freesurfer_surf_path_lh_white(synthetic_data_dir):
    """``surf/lh.white`` resolves; hemi is ``"L"`` or ``"R"``."""
    path = freesurfer_surf_path(
        synthetic_data_dir, "sub-01", hemi="L", name="white",
    )
    assert path.is_file()
    assert path.name == "lh.white"


def test_freesurfer_surf_path_rh_sphere_reg(synthetic_data_dir):
    """Right-hemi ``sphere.reg`` -- the file the surface chain needs."""
    path = freesurfer_surf_path(
        synthetic_data_dir, "sub-01", hemi="R", name="sphere.reg",
    )
    assert path.is_file()
    assert path.name == "rh.sphere.reg"


def test_freesurfer_surf_path_rejects_bad_hemi(synthetic_data_dir):
    """Hemi must be ``"L"`` or ``"R"`` -- guard against typos."""
    import pytest

    with pytest.raises(ValueError, match="hemi"):
        freesurfer_surf_path(
            synthetic_data_dir, "sub-01", hemi="left", name="white",
        )


def test_freesurfer_transforms_dir_resolves(synthetic_data_dir):
    """The transforms dir holds ``talairach.lta`` / ``talairach.xfm``."""
    xfm_dir = freesurfer_transforms_dir(
        synthetic_data_dir, "sub-01",
    )
    assert xfm_dir.is_dir()
    assert (xfm_dir / "talairach.lta").is_file()
    assert (xfm_dir / "talairach.xfm").is_file()
