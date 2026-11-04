"""Source configuration for the LAION-fMRI S3 bucket."""

LAION_FMRI_BUCKET = "laion-fmri"
LAION_FMRI_REGION = "us-west-2"

#: Subjects of each dataset. Fixed here rather than read from the
#: bucket, so a subject uploaded for one dataset never appears in the
#: other. ``"main"``: the main experiment (betas); ``"mapping"``:
#: precision mapping (retinotopy, localizers), which adds two subjects
#: without main-experiment data.
DATASET_SUBJECTS = {
    "main": ("sub-01", "sub-03", "sub-05", "sub-06", "sub-07"),
    "mapping": (
        "sub-01", "sub-03", "sub-04", "sub-05", "sub-06", "sub-07",
        "sub-08",
    ),
}

#: Raw sessions of the precision-mapping dataset. They sit beside
#: LAION's numbered sessions under ``sub-XX/``; the LAION raw download
#: leaves them out, and ``download_mapping(include_raw=True)`` fetches
#: them together with ``ses-PrismaAnat``, which both datasets share.
MAPPING_SESSIONS = (
    "ses-4BarScreenfLoc", "ses-BarsLMSEyeCalib", "ses-Corners1",
    "ses-Corners2", "ses-Foveal", "ses-MotionLocBarsSML",
)
SHARED_ANATOMY_SESSION = "ses-PrismaAnat"

#: Sessions whose objects are protected by a deny rule on the S3
#: bucket. Public callers receive 403 on GET, so the package excludes
#: them from every download to spare callers a hard crash on the first
#: protected key.
HELD_OUT_SESSIONS = ("ses-31", "ses-32", "ses-33", "ses-34")

#: Tasks whose *localizer derivatives* are released from inside a
#: held-out session. The object localizer was acquired in ses-31; its
#: derived maps expose none of the held-out stimuli. The exemption is
#: limited to ``HELD_OUT_EXEMPT_PREFIX``, so raw or preprocessed ses-31
#: files of the same task stay embargoed. The bucket policy carves out
#: the same keys.
HELD_OUT_EXEMPT_TASKS = ("oloc",)
HELD_OUT_EXEMPT_PREFIX = "derivatives/localizers/"
