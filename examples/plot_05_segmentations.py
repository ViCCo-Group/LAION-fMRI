"""
Object Segmentations
====================

Every shared stimulus image is accompanied by object-level
segmentation masks: for each noun that the upstream detector found in
the image, there is one binary ``(1000, 1000)`` mask per detected
instance of that noun. For example, an image of a person playing
piano carries masks for ``"hand"`` (4 instances), ``"piano"`` (1
instance), and so on.

.. note::

   Segmentations are provided **for the shared stimulus set only**
   (the 1,492 images viewed by every subject). Subject-unique images
   do not carry masks. Use ``sub.segmentations.has_image(trial)`` to
   check before retrieval; ``nouns()`` and ``for_image()`` safely
   return empty results for uncovered images.
"""

# %%
# Bind the quickstart's data directory
# -------------------------------------

import os

from laion_fmri.config import dataset_initialize

data_dir = os.environ.get(
    "LAION_FMRI_EXAMPLE_DATA_DIR",
    os.path.join(os.getcwd(), "laion_fmri_quickstart"),
)
os.makedirs(data_dir, exist_ok=True)
dataset_initialize(data_dir)

# %%
# Browsing masks from the stimulus side
# --------------------------------------

import laion_fmri

stim = laion_fmri.load_stimuli()

image_name = "shared_12rep_LAION_cluster_1003_i0.jpg"

# Which nouns appear in this image?
nouns = stim.segmentations.nouns(image_name)
print(f"Nouns in {image_name}: {nouns}")

# All masks for one image, as a metadata slice (one row per mask):
df = stim.segmentations.for_image(image_name)
print(df[["noun", "instance_id", "score", "localized"]].head())

# Fetch a single mask -- shape (1000, 1000), dtype uint8, values in {0, 1}:
mask = stim.segmentations.get(image_name, nouns[0])
print(f"\n'{nouns[0]}' mask: shape={mask.shape}, dtype={mask.dtype}, "
      f"covered pixels={int(mask.sum())}")

# %%
# Overlaying a mask on the image
# -------------------------------

import matplotlib.pyplot as plt
import numpy as np

img = np.array(stim.images.get(image_name))
overlay = img.copy()
# Soft red tint where the mask is set.
overlay[mask == 1] = (0.55 * img[mask == 1] + 0.45 * np.array([230, 25, 75])).astype(np.uint8)

fig, axes = plt.subplots(1, 2, figsize=(10, 5))
axes[0].imshow(img)
axes[0].set_title("original")
axes[0].axis("off")
axes[1].imshow(overlay)
axes[1].set_title(f"'{nouns[0]}' mask overlay")
axes[1].axis("off")
plt.tight_layout()
plt.show()

# %%
# Subject-level access: masks per trial
# --------------------------------------
#
# On the subject side, segmentations are addressed by **trial index**
# (rows of ``sub.metadata``). Because masks ship only for the shared
# stimulus set, ``nouns()`` returns ``[]`` for any trial whose image
# was a subject-unique stimulus.

sub = laion_fmri.load_subject(1)

n_covered = sum(
    sub.segmentations.has_image(t) for t in range(len(sub.metadata))
)
print(f"Trials whose image carries masks: {n_covered} / {len(sub.metadata)}")

# What nouns did sub-01 see across their first 5 trials?
for trial in range(5):
    print(f"  trial {trial}: {sub.segmentations.nouns(trial)}")
