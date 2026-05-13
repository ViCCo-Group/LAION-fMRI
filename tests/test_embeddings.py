import h5py

from laion_fmri.embeddings import AVAILABLE_MODELS, Embeddings, load_embeddings


def _touch_embedding_file(data_dir, model):
    path = data_dir / "stimuli" / f"task-images_desc-{model}_embeddings.h5"
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as h5:
        h5.create_dataset("embedding", data=[[0.0]])
        h5.create_dataset("image_ids", data=[b"example.jpg"])
        h5.create_dataset("valid", data=[True])
    return path


def test_embeddings_accepts_single_model_string(tmp_path):
    _touch_embedding_file(tmp_path, "CLIP")

    emb = Embeddings("CLIP", data_dir=tmp_path)

    assert emb.models == ["CLIP"]


def test_load_embeddings_all_expands_available_models(tmp_path):
    for model in AVAILABLE_MODELS:
        _touch_embedding_file(tmp_path, model)

    emb = load_embeddings(data_dir=tmp_path)

    assert emb.models == list(AVAILABLE_MODELS)
