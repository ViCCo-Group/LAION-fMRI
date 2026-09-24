from pathlib import Path

from laion_fmri.derivatives import (
    localizer_effect_path,
    localizer_statmap_path,
)


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
