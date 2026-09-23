from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents, chunk_size=5000, chunk_overlap=500):
    """
    Splits a list of documents into smaller chunks.
    :param documents: List of Document objects
    :param chunk_size: Maximum size of chunks to return
    :param chunk_overlap: Overlap in characters between chunks
    :return: List of split Document objects
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    return chunks
