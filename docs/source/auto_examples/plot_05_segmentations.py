"""
Object Segmentations
====================

A lot of analyses on this dataset ask questions of the form
"is this voxel's response driven by the *piano* in the image,
or by the *hand* on the piano?". Answering that requires knowing,
for each image, exactly which pixels correspond to which object.
This example introduces the segmentation masks the dataset ships
to enable that kind of analysis, and shows how to retrieve them
from both the stimulus side (by image name) and the subject side
(by trial index).

Concretely, every shared stimulus image is accompanied by
object-level segmentation masks: for each noun that the upstream
detector found in the image, there is one binary ``(1000, 1000)``
mask per detected instance of that noun. For example, an image
of a person playing piano carries masks for ``"hand"`` (4
instances), ``"piano"`` (1 instance), and so on.

.. note::

   Segmentations are provided **for the shared stimulus set
   only** (the 1,492 images viewed by every subject). Subject-
   unique images do not carry masks. Use
   ``sub.segmentations.has_image(trial)`` to check before
   retrieval; ``nouns()`` and ``for_image()`` return empty
   results for uncovered images.
"""

# %%
# Bind the quickstart's data directory
# ------------------------------------
#
# Segmentations live in a small HDF5 + a metadata CSV that
# ship at the dataset level rather than per subject. The
# script reuses the quickstart's data directory so the
# stimulus images downloaded there can be combined with the
# masks. ``download_segmentations()`` is the dedicated
# accessor for the segmentation pair; it pulls the files
# (a few MB total) on the first call and is a no-op
# afterwards. No functional data is required beyond the
# stimulus images.

import os

from laion_fmri.config import dataset_initialize
from laion_fmri.download import download_segmentations

# define and initialize the data directory
data_dir = os.environ.get(
    "LAION_FMRI_EXAMPLE_DATA_DIR",
    os.path.join(os.getcwd(), "laion_fmri_quickstart"),
)
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)

# pull the dataset-wide segmentation files on the first run;
# the call is a no-op once the local files are already present
download_segmentations()

# %%
# Browsing masks from the stimulus side
# -------------------------------------
#
# Segmentation work usually starts with one of two questions:
# "what objects are in this image?" and "give me the mask for
# this specific object". The stimulus-side accessors at
# ``stim.segmentations`` answer both, and the cell below
# exercises the three of interest in the order they normally
# appear in an analysis.
#
# * ``nouns(image)`` returns the noun list, i.e. the
#   vocabulary of objects available for the image.
# * ``for_image(image)`` returns the per-mask metadata rows,
#   one row per detected instance, with the upstream
#   detector's confidence ``score`` and bounding info.
#   Iterating these rows is how to enumerate every individual
#   instance.
# * ``get(image, noun)`` returns the actual binary
#   ``(1000, 1000)`` ``uint8`` mask, which is what feeds into
#   any pixel-level analysis.

import laion_fmri

# load the stimulus namespace and pick one image to inspect
stim = laion_fmri.load_stimuli()
image_name = "shared_12rep_LAION_cluster_1003_i0.jpg"

# list the nouns the upstream detector found in this image
nouns = stim.segmentations.nouns(image_name)
print(f"Nouns in {image_name}: {nouns}")

# fetch the per-mask metadata slice, one row per detected
# instance
df = stim.segmentations.for_image(image_name)
print(df[["noun", "instance_id", "score", "localized"]].head())

# fetch a single mask: shape (1000, 1000), dtype uint8, values
# in {0, 1}
mask = stim.segmentations.get(image_name, nouns[0])
print(f"\n'{nouns[0]}' mask: shape={mask.shape}, dtype={mask.dtype}, "
      f"covered pixels={int(mask.sum())}")

# %%
# Overlaying a mask on the image
# ------------------------------
#
# Looking at a mask as a boolean array is rarely enough on its
# own. It is much easier to evaluate whether the detector got
# the object right by overlaying the mask on the image and
# checking by eye. The block below shows the canonical pattern
# for this case. Tint mask pixels with a soft red, then render
# the original image and the tinted overlay side-by-side.
#
# The matplotlib render itself is kept commented so the
# gallery does not redistribute stimulus content; uncomment
# it to inspect the overlay locally.

import numpy as np

# build a soft-red tinted overlay where the mask is set
img = np.array(stim.images.get(image_name))
overlay = img.copy()
overlay[mask == 1] = (
    0.55 * img[mask == 1] + 0.45 * np.array([230, 25, 75])
).astype(np.uint8)

# uncomment to render the original image and the overlay side-
# by-side locally:
# import matplotlib.pyplot as plt
# fig, axes = plt.subplots(1, 2, figsize=(10, 5))
# axes[0].imshow(img)
# axes[0].set_title("original")
# axes[0].axis("off")
# axes[1].imshow(overlay)
# axes[1].set_title(f"'{nouns[0]}' mask overlay")
# axes[1].axis("off")
# plt.tight_layout()
# plt.show()

# %%
# Subject-level access: masks per trial
# -------------------------------------
#
# Once the analysis commits to a specific subject, addressing
# masks by image name becomes awkward, the natural index is
# the trial that produced a beta, not the image string. The
# subject-side accessor takes care of that re-indexing. On
# ``sub.segmentations``, every retrieval is addressed by
# **trial index** (rows of ``sub.metadata``), so it stays
# aligned with the beta arrays loaded in earlier examples.
#
# Because masks ship only for the shared stimulus set,
# ``nouns()`` returns ``[]`` for any trial whose image was a
# subject-unique stimulus. ``has_image(trial)`` is the explicit
# check to use before retrieval.

# load the subject and count how many of their trials have masks
sub = laion_fmri.load_subject("sub-01")
n_covered = sum(
    sub.segmentations.has_image(t)
    for t in range(len(sub.metadata))
)
print(
    f"Trials whose image carries masks: {n_covered} / "
    f"{len(sub.metadata)}"
)

# list the nouns sub-01 saw across the first 5 trials
for trial in range(5):
    print(f"  trial {trial}: {sub.segmentations.nouns(trial)}")
