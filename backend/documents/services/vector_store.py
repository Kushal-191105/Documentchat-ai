import os
from django.conf import settings
from langchain_chroma import Chroma
from .embeddings import get_embeddings_model

# Path where ChromaDB will persist the vectors
CHROMA_PERSIST_DIR = os.path.join(settings.BASE_DIR, 'chroma_db')

def get_vector_store():
    """
    Returns an instance of the Chroma vector store.
    """
    embeddings = get_embeddings_model()
    return Chroma(
        collection_name="documents_collection_v5",
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )

def add_documents_to_store(chunks, document_id):
    """
    Adds document chunks to the vector store with their associated document_id.
    :param chunks: List of Document chunks
    :param document_id: ID of the Django Document model
    """
    # Inject document_id into metadata for all chunks
    for chunk in chunks:
        chunk.metadata['document_id'] = str(document_id)

    vector_store = get_vector_store()
    
    # Since we are using local HuggingFace embeddings now, there are no rate limits!
    # We can upload all chunks instantly without sleeping.
    try:
        vector_store.add_documents(chunks)
    except Exception as e:
        print(f"Error adding to local vector store: {e}")
        raise e

def delete_document_from_store(document_id):
    """
    Deletes all vectors associated with a specific document_id.
    :param document_id: ID of the Django Document model
    """
    vector_store = get_vector_store()
    # Chroma allows deleting by metadata using a where clause
    try:
        # Unfortunately Chroma's delete method expects ids. 
        # Alternatively, we can use collection.delete(where={"document_id": str(document_id)})
        collection = vector_store._collection
        collection.delete(where={"document_id": str(document_id)})
    except Exception as e:
        print(f"Warning: Failed to delete document {document_id} from Chroma: {e}")
