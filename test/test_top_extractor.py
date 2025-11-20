import sys
import types
from types import SimpleNamespace

import numpy as np

if not hasattr(np, "arg_max"):
    np.arg_max = np.argmax  # type: ignore[attr-defined]


def _ensure_sentence_transformers_stub():
    if "sentence_transformers" in sys.modules:
        return

    fake_module = types.ModuleType("sentence_transformers")

    class _FakeSentenceTransformer:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, texts, show_progress_bar=False):
            _ = show_progress_bar
            return np.zeros((len(texts), 3))

    fake_module.SentenceTransformer = _FakeSentenceTransformer
    sys.modules["sentence_transformers"] = fake_module


def _ensure_sklearn_stub():
    if "sklearn.metrics.pairwise" in sys.modules:
        return

    pairwise_module = types.ModuleType("sklearn.metrics.pairwise")

    def _cosine_similarity(x, y=None):
        a = np.array(x, dtype=float)
        b = a if y is None else np.array(y, dtype=float)
        norm_a = np.linalg.norm(a, axis=1, keepdims=True)
        norm_b = np.linalg.norm(b, axis=1, keepdims=True)
        norm_a[norm_a == 0] = 1.0
        norm_b[norm_b == 0] = 1.0
        return (a / norm_a) @ (b / norm_b).T

    pairwise_module.cosine_similarity = _cosine_similarity

    metrics_module = types.ModuleType("sklearn.metrics")
    metrics_module.pairwise = pairwise_module

    sklearn_module = sys.modules.setdefault("sklearn", types.ModuleType("sklearn"))
    sklearn_module.metrics = metrics_module

    sys.modules["sklearn.metrics"] = metrics_module
    sys.modules["sklearn.metrics.pairwise"] = pairwise_module


def _ensure_hdbscan_stub():
    if "hdbscan" in sys.modules:
        return

    fake_module = types.ModuleType("hdbscan")

    class _FakeHDBSCAN:
        def __init__(self, min_cluster_size=4):
            self.min_cluster_size = min_cluster_size

        def fit_predict(self, embeddings):
            raise RuntimeError("HDBSCAN stub should not be used in this test")

    fake_module.HDBSCAN = _FakeHDBSCAN
    sys.modules["hdbscan"] = fake_module


_ensure_sentence_transformers_stub()
_ensure_sklearn_stub()
_ensure_hdbscan_stub()

from top_extractor import TopExtractor


def test_cluster_medoids_returns_cluster_representatives():
    headlines = [
        "Tech stocks rally",
        "Markets surge worldwide",
        "Investors stay cautious",
        "Local team wins finals",
        "Championship parade scheduled",
        "Fans prepare celebrations",
        "Noise headline",
    ]

    embeddings = np.array([
        [1.0, 0.0],
        [0.9, 0.1],
        [0.2, 0.8],
        [0.0, 1.0],
        [0.2, 0.9],
        [0.6, 0.4],
        [0.5, 0.5],
    ])

    labels = np.array([0, 0, 0, 1, 1, 1, -1])

    medoid_headlines = TopExtractor.cluster_medoids(headlines, embeddings, labels)

    expected_headlines = {"Markets surge worldwide", "Championship parade scheduled"}
    assert set(medoid_headlines) == expected_headlines


def test_pick_top_articles_runs_pipeline(monkeypatch):
    headlines = [
        "Headline A",
        "Headline B",
        "Headline C",
    ]
    fake_embeddings = np.arange(9).reshape(3, 3)
    fake_labels = np.array([0, 0, 0])

    captured_calls = {}

    medoid_embeddings = np.array([[1.0, 0.0]])

    def fake_embed(texts):
        captured_calls.setdefault("embed_texts", []).append(list(texts))
        if texts == headlines:
            return fake_embeddings
        if list(texts) == ["Headline B"]:
            return medoid_embeddings
        raise AssertionError("Unexpected embed input")

    def fake_cluster_headlines(embeddings, min_cluster_size=4):
        captured_calls["cluster_headlines_input"] = embeddings
        return fake_labels

    def fake_cluster_medoids(headlines_arg, embeddings_arg, labels_arg):
        captured_calls["cluster_medoids_args"] = (headlines_arg, embeddings_arg, labels_arg)
        return ["Headline B"]

    def fake_mmr_select(candidates, embeddings, top_n=TopExtractor.TOP_N, lambda_param=1.0):
        captured_calls["mmr_args"] = (candidates, embeddings, top_n, lambda_param)
        return list(candidates)

    monkeypatch.setattr(TopExtractor, "embed", staticmethod(fake_embed))
    monkeypatch.setattr(TopExtractor, "cluster_headlines", staticmethod(fake_cluster_headlines))
    monkeypatch.setattr(TopExtractor, "cluster_medoids", staticmethod(fake_cluster_medoids))
    monkeypatch.setattr(TopExtractor, "mmr_select", staticmethod(fake_mmr_select))

    user = SimpleNamespace(
        selected_feeds=[
            SimpleNamespace(
                article=[
                    SimpleNamespace(title="Headline A", url="https://example.com/a"),
                    SimpleNamespace(title="Headline B", url="https://example.com/b"),
                ]
            ),
            SimpleNamespace(article=[SimpleNamespace(title="Headline C", url="https://example.com/c")]),
        ],
        top_articles=None,
    )

    TopExtractor.pick_top_articles([user])

    assert [article.title for article in user.top_articles] == ["Headline B"]
    assert captured_calls["embed_texts"][0] == headlines
    np.testing.assert_array_equal(captured_calls["cluster_headlines_input"], fake_embeddings)

    ch_headlines, ch_embeddings, ch_labels = captured_calls["cluster_medoids_args"]
    assert ch_headlines == headlines
    np.testing.assert_array_equal(ch_embeddings, fake_embeddings)
    np.testing.assert_array_equal(ch_labels, fake_labels)

    candidates, candidate_embeddings, top_n, lambda_param = captured_calls["mmr_args"]
    assert candidates == ["Headline B"]
    np.testing.assert_array_equal(candidate_embeddings, medoid_embeddings)
    assert top_n == TopExtractor.TOP_N
    assert lambda_param == 1.0
