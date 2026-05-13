"""Tests for the template-space projection module."""

import nibabel as nib
import numpy as np
import pytest

from laion_fmri.subject import load_subject

# Skip the whole module if the optional ``[template]`` extra isn't
# installed -- the production module imports nitransforms / nilearn
# / neuromaps / templateflow on demand and raises ``ImportError``
# at call time, so the test suite stays usable for users who
# haven't opted into the heavier extras.
nitransforms = pytest.importorskip("nitransforms")

from laion_fmri.templates import to_template  # noqa: E402

from tests.conftest import (  # noqa: E402
    N_BRAIN_VOXELS,
    N_FSNATIVE_VERTICES,
)


@pytest.fixture
def configured_subject(synthetic_data_dir, monkeypatch):
    """Subject loaded from the synthetic data dir."""
    config_home = synthetic_data_dir / ".." / "tpl_cfg"
    config_home.mkdir(exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    from laion_fmri.config import dataset_initialize
    dataset_initialize(str(synthetic_data_dir))

    return load_subject("sub-01")


# ── MNI305 volume route ────────────────────────────────────────


def test_to_template_mni305_returns_nifti(configured_subject):
    """Projecting brain-mask values to MNI305 yields a 3-D NIfTI."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(configured_subject, values, "MNI305")
    assert isinstance(out, nib.Nifti1Image)
    assert out.ndim == 3


def test_to_template_mni305_identity_preserves_data(configured_subject):
    """With the fixture's identity LTA, the MNI305 output values
    match the input values voxel-for-voxel (brain-masked area).
    """
    rng = np.random.default_rng(0)
    values = rng.standard_normal(N_BRAIN_VOXELS).astype(np.float32)
    out = to_template(configured_subject, values, "MNI305")
    data = np.asarray(out.dataobj)
    # Round-trip via the brain mask: scatter the input into a 3-D
    # volume on the T1w grid, apply the identity transform, and
    # the non-zero voxels should equal the input.
    brain_mask = configured_subject.get_brain_mask()
    flat = data.ravel()
    np.testing.assert_allclose(
        flat[brain_mask], values, rtol=1e-5, atol=1e-5,
    )


def test_to_template_rejects_unknown_target(configured_subject):
    """Unrecognised target -> ValueError with the accepted list."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="target"):
        to_template(configured_subject, values, "MNI999")


def test_to_template_mni305_rejects_surface_route(configured_subject):
    """MNI305 is volume-only; route='surface' is rejected."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="surface"):
        to_template(
            configured_subject, values, "MNI305", route="surface",
        )


# ── Surface chain: T1w volume -> fsaverage ─────────────────────


# fsaverage5 default density: 10242 vertices per hemisphere.
FSAVERAGE5_N_VERTICES = 10242


def test_to_template_fsaverage_left_hemi(configured_subject):
    """Single-hemi surface output: 1-D array of fsaverage5 length."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values, "fsaverage", hemi="L",
    )
    assert isinstance(out, np.ndarray)
    assert out.shape == (FSAVERAGE5_N_VERTICES,)
    assert np.isfinite(out).all()


def test_to_template_fsaverage_right_hemi(configured_subject):
    """Right hemi works the same way as left."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values, "fsaverage", hemi="R",
    )
    assert isinstance(out, np.ndarray)
    assert out.shape == (FSAVERAGE5_N_VERTICES,)


def test_to_template_fsaverage_both_hemis_returns_dict(
    configured_subject,
):
    """``hemi=None`` returns both hemispheres in a dict."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(configured_subject, values, "fsaverage")
    assert isinstance(out, dict)
    assert set(out) == {"L", "R"}
    assert out["L"].shape == (FSAVERAGE5_N_VERTICES,)
    assert out["R"].shape == (FSAVERAGE5_N_VERTICES,)


def test_to_template_fsaverage_rejects_volume_route(configured_subject):
    """fsaverage is surface-only; ``route='volume'`` is rejected."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="volume"):
        to_template(
            configured_subject, values, "fsaverage",
            hemi="L", route="volume",
        )


# fsLR and CIVET are intentionally out of scope for this PR --
# their fsaverage hand-off goes through neuromaps' multimodal
# surface matching, which requires Connectome Workbench's
# ``wb_command`` binary. See the docstring on
# ``laion_fmri.templates._SUPPORTED_TARGETS``.


def test_to_template_rejects_fslr(configured_subject):
    """fsLR is not in this PR's supported-targets list."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="target"):
        to_template(configured_subject, values, "fsLR", hemi="L")


def test_to_template_rejects_civet(configured_subject):
    """CIVET is not in this PR's supported-targets list."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="target"):
        to_template(configured_subject, values, "CIVET", hemi="L")


# ── MNI152 volume route (route="volume", via MNI305) ───────────


def test_to_template_mni152_volume_returns_nifti(configured_subject):
    """T1w -> MNI305 -> MNI152NLin6Asym, ending on the MNI152 grid."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values,
        "MNI152NLin6Asym", route="volume",
    )
    assert isinstance(out, nib.Nifti1Image)
    assert out.ndim == 3


def test_to_template_mni152_volume_on_mni152_grid(configured_subject):
    """Output volume sits on the templateflow MNI152 reference grid."""
    import templateflow.api as tflow

    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values,
        "MNI152NLin6Asym", route="volume",
    )
    ref_path = tflow.get(
        "MNI152NLin6Asym", suffix="T1w", resolution=1,
        extension=".nii.gz", desc=None,
    )
    if isinstance(ref_path, list):
        ref_path = ref_path[0]
    ref_img = nib.load(str(ref_path))
    assert out.shape == ref_img.shape


# MNI152 surface route is intentionally not supported: neuromaps
# only ships ``mni152_to_fsaverage`` (volume→surface), not the
# reverse, and the surface→volume direction would need
# Connectome Workbench's ``wb_command`` for the fsaverage→fsLR
# stop. See the docstring on
# ``laion_fmri.templates._VOLUME_ONLY_TARGETS``.


def test_to_template_mni152_rejects_surface_route(configured_subject):
    """MNI152 variants are volume-only in this PR."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="surface"):
        to_template(
            configured_subject, values, "MNI152NLin6Asym",
            route="surface",
        )


# ── MNI152NLin2009cAsym (fmriprep's default) ───────────────────


def test_to_template_mni152_2009c_returns_nifti(configured_subject):
    """T1w -> MNI305 -> NLin6Asym -> 2009cAsym yields a 3-D NIfTI."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values, "MNI152NLin2009cAsym",
    )
    assert isinstance(out, nib.Nifti1Image)
    assert out.ndim == 3


def test_to_template_mni152_2009c_on_target_grid(configured_subject):
    """Output volume sits on the templateflow 2009cAsym grid."""
    import templateflow.api as tflow

    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values, "MNI152NLin2009cAsym",
    )
    ref_path = tflow.get(
        "MNI152NLin2009cAsym", suffix="T1w", resolution=1,
        extension=".nii.gz", desc=None,
    )
    if isinstance(ref_path, list):
        ref_path = ref_path[0]
    ref_img = nib.load(str(ref_path))
    assert out.shape == ref_img.shape


# ── Out-of-scope MNI variants are rejected ─────────────────────


@pytest.mark.parametrize(
    "variant",
    [
        "MNI152Lin",
        "MNI152NLin6Sym",
        "MNI152NLin2009aAsym",
        "MNI152NLin2009aSym",
        "MNI152NLin2009bAsym",
        "MNI152NLin2009bSym",
        "MNI152NLin2009cSym",
        "MNIColin27",
    ],
)
def test_to_template_rejects_unsupported_mni_variants(
    configured_subject, variant,
):
    """MNI variants without a templateflow path raise ValueError."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="target"):
        to_template(configured_subject, values, variant)


# ── BIDS-conformant output writer ──────────────────────────────


def test_to_template_writes_mni305_nifti(configured_subject, tmp_path):
    """MNI305 + output_dir writes a BIDS-named .nii.gz."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values, "MNI305",
        output_dir=tmp_path, desc="MeanBeta", session="ses-01",
    )
    expected = (
        tmp_path
        / "sub-01_ses-01_space-MNI305_desc-MeanBeta_statmap.nii.gz"
    )
    assert expected.exists()
    assert isinstance(out, nib.Nifti1Image)


def test_to_template_writes_mni152_nifti(configured_subject, tmp_path):
    """MNI152NLin6Asym + output_dir writes a BIDS-named .nii.gz."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    to_template(
        configured_subject, values, "MNI152NLin6Asym",
        route="volume",
        output_dir=tmp_path, desc="MeanBeta", session="ses-01",
    )
    expected = (
        tmp_path
        / "sub-01_ses-01_space-MNI152NLin6Asym"
        "_desc-MeanBeta_statmap.nii.gz"
    )
    assert expected.exists()


def test_to_template_writes_fsaverage_single_hemi(
    configured_subject, tmp_path,
):
    """fsaverage hemi='L' writes one func.gii with den-/hemi- tokens."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = to_template(
        configured_subject, values, "fsaverage", hemi="L",
        output_dir=tmp_path, desc="MeanBeta", session="ses-01",
    )
    expected = (
        tmp_path
        / "sub-01_ses-01_space-fsaverage_den-10k_hemi-L"
        "_desc-MeanBeta_statmap.func.gii"
    )
    assert expected.exists()
    assert isinstance(out, np.ndarray)


def test_to_template_writes_fsaverage_both_hemis(
    configured_subject, tmp_path,
):
    """fsaverage hemi=None writes one func.gii per hemisphere."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    to_template(
        configured_subject, values, "fsaverage",
        output_dir=tmp_path, desc="MeanBeta", session="ses-01",
    )
    expected_l = (
        tmp_path
        / "sub-01_ses-01_space-fsaverage_den-10k_hemi-L"
        "_desc-MeanBeta_statmap.func.gii"
    )
    expected_r = (
        tmp_path
        / "sub-01_ses-01_space-fsaverage_den-10k_hemi-R"
        "_desc-MeanBeta_statmap.func.gii"
    )
    assert expected_l.exists()
    assert expected_r.exists()


def test_to_template_writes_omits_session_and_desc(
    configured_subject, tmp_path,
):
    """No session / no desc -> the corresponding tokens are absent."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    to_template(
        configured_subject, values, "MNI305",
        output_dir=tmp_path,
    )
    expected = tmp_path / "sub-01_space-MNI305_statmap.nii.gz"
    assert expected.exists()


def test_to_template_writes_strips_ses_prefix(
    configured_subject, tmp_path,
):
    """Passing ``session='ses-01'`` or ``session='01'`` both work."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    to_template(
        configured_subject, values, "MNI305",
        output_dir=tmp_path, session="01",
    )
    expected = tmp_path / "sub-01_ses-01_space-MNI305_statmap.nii.gz"
    assert expected.exists()


# ── Subject.to_template thin wrapper ───────────────────────────


def test_subject_to_template_mni305(configured_subject):
    """``Subject.to_template`` mirrors the module-level call."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = configured_subject.to_template(values, "MNI305")
    assert isinstance(out, nib.Nifti1Image)
    assert out.ndim == 3


def test_subject_to_template_fsaverage_hemi(configured_subject):
    """``Subject.to_template`` forwards surface-target kwargs."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = configured_subject.to_template(
        values, "fsaverage", hemi="L",
    )
    assert isinstance(out, np.ndarray)
    assert out.shape == (FSAVERAGE5_N_VERTICES,)


def test_subject_to_template_writes_to_disk(
    configured_subject, tmp_path,
):
    """``output_dir`` flows through the wrapper to the writer."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    configured_subject.to_template(
        values, "MNI305",
        output_dir=tmp_path, desc="MeanBeta", session="ses-01",
    )
    expected = (
        tmp_path
        / "sub-01_ses-01_space-MNI305_desc-MeanBeta_statmap.nii.gz"
    )
    assert expected.exists()


# ── Explicit per-direction helpers ─────────────────────────────


def test_volume_to_surface_single_hemi(configured_subject):
    """``volume_to_surface`` is the volume->fsaverage shortcut."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = configured_subject.volume_to_surface(values, hemi="L")
    assert isinstance(out, np.ndarray)
    assert out.shape == (FSAVERAGE5_N_VERTICES,)


def test_volume_to_surface_both_hemis(configured_subject):
    """``hemi=None`` returns both hemispheres as a dict."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = configured_subject.volume_to_surface(values)
    assert isinstance(out, dict)
    assert set(out) == {"L", "R"}


def test_volume_to_surface_rejects_volume_target(configured_subject):
    """``volume_to_surface`` refuses volume targets."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="surface"):
        configured_subject.volume_to_surface(values, target="MNI305")


def test_volume_to_template_mni305(configured_subject):
    """``volume_to_template`` is the volume->MNI shortcut."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    out = configured_subject.volume_to_template(values, "MNI305")
    assert isinstance(out, nib.Nifti1Image)
    assert out.ndim == 3


def test_volume_to_template_rejects_surface_target(configured_subject):
    """``volume_to_template`` refuses ``fsaverage``."""
    values = np.ones(N_BRAIN_VOXELS, dtype=np.float32)
    with pytest.raises(ValueError, match="volume"):
        configured_subject.volume_to_template(values, "fsaverage")


def test_surface_to_template_single_hemi(configured_subject):
    """fsnative array -> fsaverage5 array (one hemi)."""
    fsnative = np.ones(N_FSNATIVE_VERTICES, dtype=np.float32)
    out = configured_subject.surface_to_template(fsnative, hemi="L")
    assert isinstance(out, np.ndarray)
    assert out.shape == (FSAVERAGE5_N_VERTICES,)
    assert np.isfinite(out).all()


def test_surface_to_template_both_hemis_dict_in_dict_out(
    configured_subject,
):
    """``{"L": ..., "R": ...}`` in, dict out."""
    fsnative = {
        "L": np.ones(N_FSNATIVE_VERTICES, dtype=np.float32),
        "R": np.ones(N_FSNATIVE_VERTICES, dtype=np.float32),
    }
    out = configured_subject.surface_to_template(fsnative)
    assert isinstance(out, dict)
    assert set(out) == {"L", "R"}
    assert out["L"].shape == (FSAVERAGE5_N_VERTICES,)
    assert out["R"].shape == (FSAVERAGE5_N_VERTICES,)


def test_surface_to_template_rejects_volume_target(configured_subject):
    """``surface_to_template`` only accepts surface targets."""
    fsnative = np.ones(N_FSNATIVE_VERTICES, dtype=np.float32)
    with pytest.raises(ValueError, match="surface"):
        configured_subject.surface_to_template(
            fsnative, "MNI305", hemi="L",
        )


def test_surface_to_template_rejects_wrong_vertex_count(
    configured_subject,
):
    """fsnative input has to match the recon's vertex count."""
    bad = np.ones(N_FSNATIVE_VERTICES + 7, dtype=np.float32)
    with pytest.raises(ValueError, match="vertices"):
        configured_subject.surface_to_template(bad, hemi="L")
