from rest_framework import viewsets, parsers
from rest_framework.permissions import IsAuthenticated
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)

    def get_queryset(self):
        # Users can only access their own documents
        return Document.objects.filter(user=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        # Calculate file size before saving
        file_obj = self.request.data.get('file')
        file_size = file_obj.size if file_obj else 0
        document = serializer.save(user=self.request.user, file_size=file_size, status='processing')
        
        # Start background processing
        import threading
        from .services.pdf_loader import load_pdf
        from .services.text_splitter import split_documents
        from .services.vector_store import add_documents_to_store

        def process_document(doc_id):
            import time
            start_time = time.time()
            try:
                # Need to fetch a fresh instance inside the thread
                doc = Document.objects.get(id=doc_id)
                
                # 1. Load PDF
                pages = load_pdf(doc.file.path)
                
                # 2. Split into chunks
                chunks = split_documents(pages)
                
                # 3. Embed & Store in Chroma
                add_documents_to_store(chunks, doc.id)
                
                # Update status
                doc.status = 'completed'
                doc.processing_time = round(time.time() - start_time, 2)
                doc.save()
            except Exception as e:
                print(f"Error processing document {doc_id}: {e}")
                doc = Document.objects.get(id=doc_id)
                doc.status = 'error'
                doc.save()

        thread = threading.Thread(target=process_document, args=(document.id,))
        thread.start()

    def perform_destroy(self, instance):
        # 1. Delete from ChromaDB
        from .services.vector_store import delete_document_from_store
        delete_document_from_store(instance.id)
        
        # 2. Delete file from filesystem
        if instance.file:
            instance.file.delete(save=False)
            
        # 3. Delete database record
        instance.delete()
