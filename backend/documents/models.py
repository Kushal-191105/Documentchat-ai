from django.db import models
from django.contrib.auth.models import User

def document_upload_path(instance, filename):
    # Upload path will be media/documents/user_<id>/<filename>
    return f'documents/user_{instance.user.id}/{filename}'

class Document(models.Model):
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_path)
    file_size = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title
