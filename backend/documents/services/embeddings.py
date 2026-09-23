from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

_embeddings_instance = None

def get_embeddings_model():
    """
    Returns the FastEmbed model which is highly optimized for lightning fast offline CPU processing.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = FastEmbedEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            threads=None # Uses all available CPU threads
        )
    return _embeddings_instance
