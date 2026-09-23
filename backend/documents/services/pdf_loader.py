from langchain_community.document_loaders import PyMuPDFLoader

def load_pdf(file_path):
    """
    Loads a PDF file and extracts its text and metadata (including page numbers).
    :param file_path: Absolute or relative path to the PDF file
    :return: List of Document objects with .page_content and .metadata
    """
    try:
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
        return documents
    except Exception as e:
        raise Exception(f"Failed to load PDF {file_path}: {str(e)}")
