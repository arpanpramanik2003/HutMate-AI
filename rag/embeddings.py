from typing import List

# Initialize singleton FastEmbed model lazily (BAAI/bge-small-en-v1.5: 384 dimensions)
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from fastembed import TextEmbedding
        _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embedding_model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate dense vector embeddings for a list of strings."""
    model = get_embedding_model()
    embeddings_generator = model.embed(texts)
    return [e.tolist() for e in embeddings_generator]
