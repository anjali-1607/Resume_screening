# resume/models.py

from django.db import models

class Resume(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=20)
    skills = models.TextField(blank=True)  # Stores skills as comma-separated values

    # Add any other fields that you need to store

    def __str__(self):
        return self.name
