import numpy as np

from src import embedder


class FakeModel:
    def __init__(self):
        self.batches = []

    def encode(self, texts, batch_size, **kw):
        self.batches.append(list(texts))
        return np.array([[float(len(t)), 1.0] for t in texts], dtype=np.float32)


def test_embed_passages_sorted_but_order_preserved(monkeypatch):
    fm = FakeModel()
    monkeypatch.setattr(embedder, "get_model", lambda d, n=None: fm)
    monkeypatch.setattr(embedder, "resolve_device", lambda s: "cpu")
    texts = ["aaaa", "a", "aaaaaaaa", "aa", "aaa"]
    out = embedder.embed_passages(texts, model="m", batch_size=2)
    assert [int(v[0]) for v in out] == [len(t) for t in texts]
    flat = [t for b in fm.batches for t in b]
    assert [len(t) for t in flat] == sorted(len(t) for t in texts)


def test_embed_passages_empty(monkeypatch):
    monkeypatch.setattr(embedder, "resolve_device", lambda s: "cpu")
    assert len(embedder.embed_passages([], model="m")) == 0
