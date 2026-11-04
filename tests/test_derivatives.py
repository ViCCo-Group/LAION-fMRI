from pathlib import Path

import pytest

from laion_fmri.derivatives import (
    localizer_effect_path,
    localizer_statmap_path,
    prf_map_path,
)


def test_public_prf_map_path_uses_explicit_data_dir(tmp_path):
    expected = (
        tmp_path / "derivatives/retinotopy/sub-03/func/"
        "sub-03_paradigm-best_hemi-L_space-fsnative_param-angle_"
        "model-dnhrf_statmap.func.gii"
    )
    expected.parent.mkdir(parents=True)
    expected.touch()

    assert prf_map_path(
        "sub-03", "angle", space="fsnative", hemi="L", data_dir=tmp_path,
    ) == expected


def test_public_localizer_statmap_path(tmp_path):
    expected = Path(
        tmp_path,
        "derivatives/localizers/sub-03/ses-MotionLocBarsSML/func/"
        "sub-03_ses-MotionLocBarsSML_task-MotionLeft_hemi-L_"
        "space-fsnative_contrast-movingVsStatic_stat-z_"
        "statmap.func.gii",
    )
    expected.parent.mkdir(parents=True)
    expected.touch()

    assert localizer_statmap_path(
        "sub-03", "MotionLeft", "movingVsStatic",
        "MotionLocBarsSML", hemi="L", data_dir=tmp_path,
    ) == expected


def test_public_localizer_effect_path(tmp_path):
    expected = Path(
        tmp_path,
        "derivatives/localizers/sub-03/ses-31/func/"
        "sub-03_ses-31_task-oloc_run-02_hemi-R_space-fsnative_"
        "contrast-scrambled_stat-effect_statmap.func.gii",
    )
    expected.parent.mkdir(parents=True)
    expected.touch()

    assert localizer_effect_path(
        "sub-03", "oloc", "scrambled", "31", 2, hemi="R",
        data_dir=tmp_path,
    ) == expected


def test_public_localizer_statmap_path_refuses_acq(tmp_path):
    with pytest.raises(ValueError, match="acq= was removed"):
        localizer_statmap_path(
            "sub-03", "MotionLoc", "movingVsStatic",
            "MotionLocBarsSML", data_dir=tmp_path, acq="left",
        )
