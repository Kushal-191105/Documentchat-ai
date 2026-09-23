from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from documents.models import Document

class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        document_id = self.request.data.get('document')
        # Verify the user owns the document
        document = Document.objects.filter(id=document_id, user=self.request.user).first()
        if not document:
            raise serializers.ValidationError("Document not found or you don't have permission.")
        
        # Optionally set title from document if not provided
        title = self.request.data.get('title', f"Chat with {document.title}")
        serializer.save(user=self.request.user, title=title)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        session = self.get_object()
        messages = session.messages.all().order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def ask(self, request, pk=None):
        session = self.get_object()
        question = request.data.get('question')
        
        if not question:
            return Response({"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Save user question
        ChatMessage.objects.create(session=session, role='user', content=question)

        # 2. Get Chat History
        recent_messages = session.messages.all().order_by('-created_at')[:4]
        chat_history = reversed(recent_messages)
        formatted_history = "\n".join([f"{msg.role.upper()}: {msg.content}" for msg in chat_history if msg.content])

        # 3. Setup Streaming Response
        from django.http import StreamingHttpResponse
        from .services.rag_pipeline import generate_answer_stream
        import json

        def event_stream():
            # Get the generator from RAG pipeline
            rag_generator = generate_answer_stream(
                document_id=session.document.id,
                question=question,
                chat_history=formatted_history
            )
            
            full_answer = ""
            sources = []
            
            for chunk in rag_generator:
                if isinstance(chunk, dict) and "sources" in chunk:
                    # Final chunk contains sources
                    sources = chunk["sources"]
                    yield f"data: {json.dumps({'sources': sources})}\n\n"
                else:
                    full_answer += chunk
                    # Send text chunk
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
            
            # Save the final message to DB after stream finishes
            ChatMessage.objects.create(
                session=session, 
                role='ai', 
                content=full_answer
            )
            yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        # DRF overrides StreamingHttpResponse sometimes, so disable content negotiation
        response['X-Accel-Buffering'] = 'no' # Disable nginx buffering if any
        response['Cache-Control'] = 'no-cache'
        return response
