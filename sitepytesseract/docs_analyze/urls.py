from django.urls import path

from . import views

urlpatterns = [
    path('', views.DocsHome.as_view(), name='home'),
    path('upload/', views.UploadDocs.as_view(), name='upload'),
    path('doc_text/<int:docs_id>', views.GetTextDocs.as_view(), name='get_text'),
    path('delete/<int:pk>', views.DeleteDocs.as_view(), name='delete'),
    path('analyze_doc/<int:doc_id>', views.AnalyzeDocs.as_view(), name='analyze_doc'),
]