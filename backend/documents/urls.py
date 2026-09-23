from django.urls import path
from .views import DocumentViewSet

document_list = DocumentViewSet.as_view({
    'get': 'list',
})

document_upload = DocumentViewSet.as_view({
    'post': 'create',
})

document_detail = DocumentViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

urlpatterns = [
    path('', document_list, name='document-list'),
    path('upload/', document_upload, name='document-upload'),
    path('<int:pk>/', document_detail, name='document-detail'),
]
