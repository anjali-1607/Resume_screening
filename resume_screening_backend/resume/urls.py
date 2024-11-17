# resume/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_resume, name='upload_resume'),  # URL for uploading resumes
    path('get_results/', views.get_results, name='get_results'),  # URL to get extracted data
]
