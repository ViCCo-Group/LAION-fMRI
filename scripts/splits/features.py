"""Feature loading and extraction helpers for split method scripts."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
from typing import Iterable

import numpy as np

from common import STIMULI_H5


RELEASE_EMBEDDING_NAMES = {
    "clip": "CLIP",
    "dinov2": "DINOv2",
    "pecore": "PEcore",
    "siglip2": "SigLIP2",
}


def feature_cache_key(space: str, image_ids: Iterable[str]) -> str:
    h = hashlib.sha1()
    h.update(space.lower().encode("utf-8"))
    for image_id in image_ids:
        h.update(b"\0")
        h.update(str(image_id).encode("utf-8"))
    return h.hexdigest()[:16]


def center_l2_normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    x = x - x.mean(0, keepdims=True)
    norm = np.linalg.norm(x, axis=1, keepdims=True)
    return (x / np.where(norm > 0, norm, 1.0)).astype(np.float32)


def embeddings_h5_path(stimuli_dir: Path, release_name: str) -> Path:
    return stimuli_dir / f"task-images_desc-{release_name}_embeddings.h5"


def _read_h5_rows(path: Path, image_ids: list[str]) -> np.ndarray:
    import h5py

    with h5py.File(path, "r") as h5:
        raw_ids = h5["image_ids"][:]
        h5_ids = [
            x.decode("utf-8") if isinstance(x, bytes) else str(x)
            for x in raw_ids
        ]
        lookup = {image_id: i for i, image_id in enumerate(h5_ids)}
        indices = np.array([lookup[image_id] for image_id in image_ids])
        order = np.argsort(indices)
        sorted_rows = h5["embedding"][indices[order], :]
        inverse = np.empty_like(order)
        inverse[order] = np.arange(len(order))
        return np.asarray(sorted_rows[inverse], dtype=np.float32)


def _metadata_index(rows: list[dict[str, str]]) -> dict[str, int]:
    return {row["image_name"]: i for i, row in enumerate(rows)}


def _image_batches(
    *,
    rows: list[dict[str, str]],
    stimuli_dir: Path,
    image_ids: list[str],
    batch_size: int,
):
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover
        raise ImportError("image feature extraction requires Pillow") from exc

    lookup = _metadata_index(rows)
    h5_path = stimuli_dir / STIMULI_H5
    if not h5_path.exists():
        raise FileNotFoundError(
            f"Missing stimulus image HDF5: {h5_path}. Download stimuli first."
        )

    import h5py

    with h5py.File(h5_path, "r") as h5:
        images = h5["images"]
        for start in range(0, len(image_ids), batch_size):
            names = image_ids[start:start + batch_size]
            pil_images = []
            for name in names:
                raw = bytes(images[lookup[name]])
                pil_images.append(Image.open(BytesIO(raw)).convert("RGB"))
            yield names, pil_images


def _as_batch_tensor(tensors):
    import torch

    fixed = []
    for tensor in tensors:
        if tensor.ndim == 4 and tensor.shape[0] == 1:
            tensor = tensor[0]
        fixed.append(tensor)
    return torch.stack(fixed, dim=0)


def extract_clip(
    *,
    rows: list[dict[str, str]],
    stimuli_dir: Path,
    image_ids: list[str],
    batch_size: int,
    device: str,
    model_name: str,
    pretrained: str,
) -> np.ndarray:
    try:
        import open_clip
        import torch
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "CLIP extraction requires torch and open_clip_torch. Install them "
            "or provide a cached CLIP feature .npz."
        ) from exc

    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name,
        pretrained=pretrained,
    )
    model.eval().to(device)
    batches = []
    with torch.no_grad():
        for _, images in _image_batches(
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            batch_size=batch_size,
        ):
            x = _as_batch_tensor([preprocess(img) for img in images]).to(device)
            batches.append(model.encode_image(x).float().cpu().numpy())
    return np.concatenate(batches, axis=0)


def extract_dinov2(
    *,
    rows: list[dict[str, str]],
    stimuli_dir: Path,
    image_ids: list[str],
    batch_size: int,
    device: str,
    model_name: str,
) -> np.ndarray:
    try:
        import torch
        import timm
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "DINOv2 extraction requires torch and timm. Install them "
            "or provide a cached DINOv2 feature .npz."
        ) from exc

    model = timm.create_model(
        model_name,
        pretrained=True,
        num_classes=0,
    ).to(device).eval()
    cfg = timm.data.resolve_model_data_config(model)
    preprocess = timm.data.create_transform(**cfg, is_training=False)

    batches = []
    with torch.no_grad():
        for _, images in _image_batches(
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            batch_size=batch_size,
        ):
            x = _as_batch_tensor([preprocess(img) for img in images]).to(device)
            batches.append(model(x).float().cpu().numpy())
    return np.concatenate(batches, axis=0)


def extract_dreamsim(
    *,
    rows: list[dict[str, str]],
    stimuli_dir: Path,
    image_ids: list[str],
    batch_size: int,
    device: str,
) -> np.ndarray:
    try:
        import torch
        from dreamsim import dreamsim
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "DreamSim extraction requires torch and dreamsim. Install them or "
            "provide a cached DreamSim feature .npz."
        ) from exc

    model, preprocess = dreamsim(pretrained=True, device=device)
    model.eval()
    batches = []
    with torch.no_grad():
        for _, images in _image_batches(
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            batch_size=batch_size,
        ):
            x = _as_batch_tensor([preprocess(img) for img in images]).to(device)
            batches.append(model.embed(x).float().cpu().numpy())
    return np.concatenate(batches, axis=0)


def load_or_extract_features(
    *,
    space: str,
    rows: list[dict[str, str]],
    stimuli_dir: Path,
    image_ids: list[str],
    cache_dir: Path,
    extract_missing: bool,
    batch_size: int,
    device: str,
    clip_model: str = "ViT-H-14",
    clip_pretrained: str = "laion2b_s32b_b79k",
    dinov2_model: str = "dinov2_vitl14",
    use_release_embeddings: bool = False,
) -> np.ndarray:
    """Load or compute features for ``image_ids`` in their requested order."""

    normalized = space.lower()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = (
        cache_dir
        / f"{normalized}_{feature_cache_key(normalized, image_ids)}.npz"
    )
    if cache_path.exists():
        data = np.load(cache_path)
        cached_ids = [str(x) for x in data["image_ids"]]
        if cached_ids == image_ids:
            return np.asarray(data["features"], dtype=np.float32)
        raise ValueError(f"cache image_ids differ from request: {cache_path}")

    release_name = RELEASE_EMBEDDING_NAMES.get(normalized)
    if use_release_embeddings and release_name is not None:
        h5_path = embeddings_h5_path(stimuli_dir, release_name)
        if h5_path.exists():
            features = _read_h5_rows(h5_path, image_ids)
            np.savez_compressed(
                cache_path,
                image_ids=np.asarray(image_ids),
                features=features,
            )
            return features

    if not extract_missing:
        raise FileNotFoundError(
            f"Missing cached/precomputed {space} features for this pool. "
            "Pass --extract-missing to compute them from task-images_stimuli.h5."
        )

    if normalized == "clip":
        features = extract_clip(
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            batch_size=batch_size,
            device=device,
            model_name=clip_model,
            pretrained=clip_pretrained,
        )
    elif normalized == "dinov2":
        features = extract_dinov2(
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            batch_size=batch_size,
            device=device,
            model_name=dinov2_model,
        )
    elif normalized == "dreamsim":
        features = extract_dreamsim(
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            batch_size=batch_size,
            device=device,
        )
    else:
        raise ValueError(f"unknown feature space {space!r}")

    features = np.asarray(features, dtype=np.float32)
    np.savez_compressed(
        cache_path,
        image_ids=np.asarray(image_ids),
        features=features,
    )
    return features


def load_feature_mats(
    *,
    spaces: list[str],
    rows: list[dict[str, str]],
    stimuli_dir: Path,
    image_ids: list[str],
    cache_dir: Path,
    extract_missing: bool,
    batch_size: int,
    device: str,
    clip_model: str,
    clip_pretrained: str,
    dinov2_model: str,
    use_release_embeddings: bool = False,
) -> dict[str, np.ndarray]:
    mats = {}
    for space in spaces:
        features = load_or_extract_features(
            space=space,
            rows=rows,
            stimuli_dir=stimuli_dir,
            image_ids=image_ids,
            cache_dir=cache_dir,
            extract_missing=extract_missing,
            batch_size=batch_size,
            device=device,
            clip_model=clip_model,
            clip_pretrained=clip_pretrained,
            dinov2_model=dinov2_model,
            use_release_embeddings=use_release_embeddings,
        )
        mats[space.lower()] = center_l2_normalize(features)
    return mats
