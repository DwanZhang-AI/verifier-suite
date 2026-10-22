"""A deterministic, offline stand-in for tau2's embedder.

banking_knowledge builds an EmbeddingEncoder at ENVIRONMENT-CONSTRUCTION time,
and that constructor instantiates OpenAIEmbedder, which raises without
OPENAI_API_KEY. The failure is eager: it happens before a single task is graded,
so all 88 certifiable banking tasks were unreachable. Ark cannot substitute --
its chat endpoint works with our key but every text-embedding model reports
InvalidEndpointOrModel.NotFound (not enabled on this account).

The stub returns a fixed pseudo-random vector per text, seeded from the text
itself, so it is deterministic across processes and replays (G5 depends on
that).

WHY THIS DOES NOT FAKE A RESULT: the DB comparison runs the SAME stub in both
the gold environment and the candidate environment. Retrieval that depends on
embeddings returns the same thing on both sides, so the hashes agree exactly
when the candidate's writes agree. What the stub CANNOT support is a task whose
obligation is the CONTENT retrieved -- so every call is counted, and any task
that actually invokes it is reported separately rather than silently counted as
verified.
"""
import hashlib

import numpy as np

CALLS = {"n": 0, "texts": 0}


class StubEmbedder:
    def __init__(self, *a, **k):
        self.dim = int(k.get("dim", 256))

    def embed(self, texts):
        CALLS["n"] += 1
        CALLS["texts"] += len(texts)
        out = []
        for t in texts:
            h = hashlib.sha256(str(t).encode()).digest()
            rng = np.random.default_rng(int.from_bytes(h[:8], "big"))
            v = rng.standard_normal(self.dim)
            out.append(v / (np.linalg.norm(v) or 1.0))
        return np.array(out)


# There is more than one registry, and patching only the query-side one left
# the failure untouched: the traceback says "Computing embeddings for 698
# documents", which is the DOCUMENT indexer, a separate module with its own
# EMBEDDER_REGISTRY dict. Patch every module that owns one, then assert.
_TARGETS = (
    "tau2.knowledge.input_preprocessors.embedding_encoder",
    "tau2.knowledge.document_preprocessors.embedding_indexer",
    "tau2.knowledge.embeddings_cache",
)


def install():
    """Swap the stub into every registry that can construct an embedder."""
    import importlib
    patched = 0
    for name in _TARGETS:
        try:
            m = importlib.import_module(name)
        except Exception:
            continue
        reg = getattr(m, "EMBEDDER_REGISTRY", None)
        if isinstance(reg, dict):
            for k in list(reg):
                reg[k] = StubEmbedder
            patched += 1
        # some modules construct OpenAIEmbedder by name rather than via the dict
        if hasattr(m, "OpenAIEmbedder"):
            m.OpenAIEmbedder = StubEmbedder
        if hasattr(m, "OpenRouterEmbedder"):
            m.OpenRouterEmbedder = StubEmbedder
    # a no-op patch looks exactly like "the domain happens to work now", which
    # is the silent-mutation failure 16_ 5.2 warns about
    assert patched >= 2, f"只打到 {patched} 个 registry，桩没装全"
    from tau2.knowledge.document_preprocessors import embedding_indexer as DI
    assert DI.EMBEDDER_REGISTRY["openai"] is StubEmbedder, "文档侧桩没装上"
