# resume/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .models import Resume
import os
import PyPDF2
import docx
import re

# View to handle fetching resume data
def get_results(request):
    try:
        # Retrieve all processed resumes from the database
        resumes = Resume.objects.all()  # Adjust based on your model's fields
        
        # Process resumes and prepare data to send back
        resume_data = [
            {
                'name': resume.name,
                'email': resume.email,
                'phone': resume.phone,
                # Include any other fields you need
            }
            for resume in resumes
        ]
        
        # Send response back as JSON
        return JsonResponse({'status': 'success', 'data': resume_data}, status=200)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Function to extract data from uploaded resume (example)
def extract_resume_data(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    text = ""

    if file_extension == '.pdf':
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text()
    elif file_extension == '.docx':
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text
    else:
        raise ValueError("Unsupported file format")

    return text

# View for handling file upload and processing
def upload_resume(request):
    if request.method == 'POST' and request.FILES['resume']:
        try:
            resume_file = request.FILES['resume']
            file_path = f"uploaded_resumes/{resume_file.name}"
            
            # Save the file
            with open(file_path, 'wb') as f:
                for chunk in resume_file.chunks():
                    f.write(chunk)
            
            # Extract text from the resume file
            resume_text = extract_resume_data(file_path)
            
            # Here you can process the resume data, e.g., extracting name, email, phone, etc.
            # Add that information to the Resume model or any other processing you need
            
            # For simplicity, let's pretend we extracted name, email, phone:
            extracted_data = {
                'name': "John Doe",
                'email': "johndoe@example.com",
                'phone': "1234567890"
            }
            
            # Save the extracted data in the database (if needed)
            # resume = Resume.objects.create(name=extracted_data['name'], ...)
            
            # Return the success response with the extracted data
            return JsonResponse({'message': 'Resume uploaded successfully!', 'data': extracted_data}, status=200)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)
