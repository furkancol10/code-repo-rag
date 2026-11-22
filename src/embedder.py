"""Embedding (KisiselNotArama/src/embedder.py'den sadeleştirilmiş kopya). GPU, hata olursa CPU."""
import logging
import os

import numpy as np

from . import config

log = logging.getLogger(__name__)
_models: dict[tuple[str, str], object] = {}
_cuda_broken = False


def _cuda_available() -> bool:
    if _cuda_broken:
        return False
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def resolve_device(setting: str) -> str:
    if setting == "auto":
        return "cuda" if _cuda_available() else "cpu"
    if setting.startswith("cuda") and not _cuda_available():
        return "cpu"
    return setting


def get_model(device: str = "cpu", name: str | None = None):
    from sentence_transformers import SentenceTransformer
    key = (name or config.EMBED_MODEL, device)
    if key not in _models:
        kw = {}
        if device.startswith("cuda") and config.EMBED_INDEX_DTYPE == "float16":
            kw["model_kwargs"] = {"torch_dtype": "float16"}
        _models[key] = SentenceTransformer(key[0], device=device, **kw)
    return _models[key]


def release_gpu() -> None:
    """GPU modellerini bırakır, VRAM'i geri verir."""
    for key in [k for k in _models if k[1].startswith("cuda")]:
        del _models[key]
    try:
        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def _disable_cuda(err: Exception) -> None:
    global _cuda_broken
    if not _cuda_broken:
        log.warning("CUDA hatası (%s); embedding CPU'ya düşüyor.", err)
    _cuda_broken = True
    release_gpu()


def _encode(texts, prefix, model, device, batch_size: int | None = None) -> np.ndarray:
    vecs = get_model(device, model).encode(
        [prefix + t for t in texts],
        batch_size=(batch_size or config.EMBED_BATCH_SIZE) if device != "cpu" else 8,
        normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype=np.float32)


def _run(texts, prefix, model, device, batch_size: int | None = None) -> np.ndarray:
    if device.startswith("cuda"):
        try:
            return _encode(texts, prefix, model, device, batch_size)
        except Exception as e:
            _disable_cuda(e)
            device = "cpu"
    return _encode(texts, prefix, model, device, batch_size)


def embed_passages(texts: list[str], model: str = config.EMBED_MODEL,
                   batch_size: int | None = None) -> np.ndarray:
    """Metinleri uzunluğa göre sıralayıp (az padding) gömer; sonuç orijinal sırada döner."""
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    bs = batch_size or int(os.environ.get("KRA_EMBED_BATCH", "32"))
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    vecs = _run([texts[i] for i in order], config.PASSAGE_PREFIX.get(model, ""), model,
                resolve_device(config.EMBED_DEVICE_INDEX), bs)
    out = np.empty_like(vecs)
    out[order] = vecs
    return out


def embed_query(text: str, model: str = config.EMBED_MODEL) -> np.ndarray:
    return _run([text], config.QUERY_PREFIX.get(model, ""), model,
                resolve_device(config.EMBED_DEVICE_QUERY))[0]
