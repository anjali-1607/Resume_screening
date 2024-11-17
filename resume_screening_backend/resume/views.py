# resume/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Resume
import os
import PyPDF2
import docx
import re
import spacy



# View to handle fetching resume data
def get_results(request):
    try:
        # Retrieve all processed resumes from the database
        resumes = Resume.objects.all()
        
        # Check if any resumes are available
        if not resumes.exists():
            return JsonResponse({'status': 'success', 'data': [], 'message': 'No resumes found'}, status=200)
        
        # Prepare data to send back
        resume_data = [
            {
                'id': resume.id,  # Include the primary key or unique identifier if needed
                'name': resume.name,
                'email': resume.email,
                'phone': resume.phone,
                'skills':resume.skills
            }
            for resume in resumes
        ]
        
        # Send response back as JSON
        return JsonResponse({'status': 'success', 'data': resume_data}, status=200)

    except Exception as e:
        # Handle any unexpected exceptions
        return JsonResponse({'status': 'error', 'message': f'Error fetching resumes: {str(e)}'}, status=500)


# Function to extract data from uploaded resume (example)
def extract_resume_data(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        # Extract text from the file
        if file_extension == '.pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
        elif file_extension == '.docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            raise ValueError("Unsupported file format: Only .pdf and .docx files are supported")

    except Exception as e:
        raise ValueError(f"Error extracting data from resume: {str(e)}")

    if not text.strip():
        raise ValueError("No text could be extracted from the file")

    # Extract dynamic information using regex
    extracted_data = {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'skills':extract_skills_nlp(text)
    }

    return extracted_data


def extract_email(text):
    """Extract email from text using regex."""
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None


def extract_phone(text):
    """Extract phone number from text using regex."""
    # Regex to match 10-digit phone numbers, optionally with country code
    phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{4,10}'
    matches = re.findall(phone_pattern, text)

    # Return the first match if found, else None
    return matches[0] if matches else None


def extract_name(text):
    """Extract name using heuristics or libraries like spaCy."""
    # Basic heuristic: Assume the name is in the first 2-3 lines of the resume
    lines = text.split('\n')[:5]  # First few lines of the text
    name = None
    for line in lines:
        if re.match(r'^[A-Z][a-z]+\s[A-Z][a-z]+$', line.strip()):  # Matches "First Last"
            name = line.strip()
            break
    return name



# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_skills_nlp(text):
    """Extract skills using NLP (spaCy)."""
    # Predefined skill keywords
    skill_keywords = [
        "Python", "Java", "C++", "SQL", "JavaScript", "React", "Angular", "Node.js", "HTML", "CSS", "Docker",
        "Kubernetes", "AWS", "Azure", "Data Analysis", "Machine Learning", "Deep Learning", "AI", "DevOps",
        "TensorFlow", "Pandas", "NumPy", "Scikit-learn", "Excel", "Tableau", "Power BI", "Git", "Jenkins"
    ]

    # Process text with spaCy
    doc = nlp(text)
    skills = []

    # Match skills based on spaCy tokens
    for token in doc:
        if token.text in skill_keywords:
            skills.append(token.text)

    return list(set(skills))  # Remove duplicates

# View for handling file upload and processing
@csrf_exempt
def upload_resume(request):
    if request.method == 'POST' and request.FILES.get('resume'):
        try:
            # Save the uploaded file
            resume_file = request.FILES['resume']
            upload_dir = "uploaded_resumes"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, resume_file.name)

            with open(file_path, 'wb') as f:
                for chunk in resume_file.chunks():
                    f.write(chunk)
            
            # Extract data
            extracted_data = extract_resume_data(file_path)

            # Save to database
            Resume.objects.create(
                name=extracted_data['name'],
                email=extracted_data['email'],
                phone=extracted_data['phone'],
                skills=", ".join(extracted_data['skills'])  # Save skills as a string
            ),

            return JsonResponse(
                {'message': 'Resume uploaded and data saved successfully!', 'data': extracted_data},
                status=200
            )

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)
