from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'title', 'file', 'file_size', 'status', 'uploaded_at', 'processing_time')
        read_only_fields = ('id', 'file_size', 'status', 'uploaded_at', 'processing_time')
