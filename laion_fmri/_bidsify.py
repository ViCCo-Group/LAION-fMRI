"""Local-side BIDS normalization of bucket keys.

The bucket sometimes ships ``label-VALUE`` tokens whose ``VALUE``
contains hyphens (``label-FFA-1``, ``label-pSTS-faces``,
``label-laion-dorsal``, ...). BIDS Common Principles forbid
hyphens inside entity values -- the hyphen is reserved as the
key/value separator -- so we strip them when computing local
destination paths. Bucket-side keys are always passed through
verbatim; only the local path is rewritten.

The transform targets the ``label-`` entity exclusively. Other
entities (``sub-``, ``ses-``, ``hemi-``, ``space-``, ...) are
left untouched.
"""

import re

_LABEL_TOKEN = re.compile(r"label-([A-Za-z0-9-]+)(?=[_./]|$)")


def bidsify_local_key(key):
    """Return ``key`` with every ``label-VALUE`` value de-hyphenated.

    Idempotent: applying the transform twice yields the same
    string as applying it once.

    Parameters
    ----------
    key : str
        S3 key or relative file path.

    Returns
    -------
    str
        Same shape as ``key``, with hyphens removed from the
        value of every ``label-`` entity token.
    """
    return _LABEL_TOKEN.sub(
        lambda m: f"label-{m.group(1).replace('-', '')}",
        key,
    )
