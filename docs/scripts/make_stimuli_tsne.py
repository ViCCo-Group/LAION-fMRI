"""Generate the stimulus-set t-SNE figure for the docs.

Loads the CLIP image embeddings (one row per stimulus), projects them
to 2-D with t-SNE, and saves a coloured scatter plot grouped by
source dataset (LAION / NSD / THINGS / THINGS+ / OOD).

Re-run after the stimulus set or embeddings change::

    uv run python docs/scripts/make_stimuli_tsne.py

Output:

* ``docs/source/_static/stimuli_distribution.png``
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

import laion_fmri

OUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "source" / "_static" / "stimuli_distribution.png"
)

# Plot order + colours: natural-image pools first (in order of count),
# OOD on top so its points stay visible in dense regions.
DATASET_ORDER = ["LAION", "THINGSplus", "THINGS", "NSD", "OOD"]
DATASET_COLORS = {
    "LAION": "#4a90d9",
    "NSD": "#e67e22",
    "THINGS": "#27ae60",
    "THINGSplus": "#9b59b6",
    "OOD": "#e74c3c",
}
DATASET_LABEL = {
    "LAION": "LAION-natural",
    "NSD": "NSD",
    "THINGS": "THINGS",
    "THINGSplus": "THINGS+",
    "OOD": "OOD",
}


def main() -> None:
    stim = laion_fmri.load_stimuli()
    emb = stim.embeddings
    image_ids = emb.image_ids
    X = emb["CLIP"][:].astype(np.float32)
    # The metadata CSV is the source of truth for the dataset label per image.
    meta = stim.metadata.copy()
    stim.close()

    # Align metadata rows to embedding rows by image_name.
    meta_by_name = meta.set_index("image_name")
    aligned = meta_by_name.loc[image_ids]
    labels = aligned["dataset"].to_numpy()

    print(f"Loaded {X.shape[0]} stimuli (CLIP dim = {X.shape[1]}).")
    print("Per-dataset counts:")
    for d, n in pd.Series(labels).value_counts().items():
        print(f"  {d}: {n}")

    # Standard t-SNE recipe: PCA-reduce to 50 dims first, then t-SNE
    # with PCA init and auto learning rate. Deterministic via random_state.
    print("Running PCA(n=50)...")
    X50 = PCA(n_components=50, random_state=0).fit_transform(X)

    print("Running t-SNE...")
    coords = TSNE(
        n_components=2,
        perplexity=30,
        learning_rate="auto",
        init="pca",
        random_state=0,
        verbose=2,
    ).fit_transform(X50)

    # Draw: one scatter per dataset so we get legend entries.
    fig, ax = plt.subplots(figsize=(8, 8), dpi=160)
    for ds in DATASET_ORDER:
        m = labels == ds
        if not m.any():
            continue
        ax.scatter(
            coords[m, 0], coords[m, 1],
            s=4 if ds == "LAION" else 8,
            c=DATASET_COLORS[ds],
            alpha=0.55 if ds == "LAION" else 0.9,
            linewidths=0,
            label=f"{DATASET_LABEL[ds]} (n={int(m.sum())})",
        )

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(
        "Stimulus set in CLIP feature space (t-SNE)",
        fontsize=13, pad=10,
    )
    # Legend below the plot so it cannot overlap any data points (the OOD
    # cluster in the lower-right corner is the worst offender when the
    # legend lives inside the axes).
    legend = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=5,
        frameon=False,
        fontsize=10,
        markerscale=2.5,
        handletextpad=0.4,
        columnspacing=1.5,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUT_PATH, dpi=160,
        bbox_inches="tight",
        bbox_extra_artists=(legend,),
    )
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
