# resume/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Resume
import os
import PyPDF2
import docx
import re
import spacy
import json


# View to handle fetching resume data
KNOWN_SKILLS = [
    "react.js", "javascript", "redux", "python", "java", "django",
    "html", "css", "typescript", "node.js", "git", "restful apis",
    "tailwind css", "material-ui", "sql", "mongodb", "graphql",
]

def extract_skills_from_text(text):
    """
    Extract skills from text using spaCy and a predefined list of known skills.
    """
    # Process the text with spaCy
    doc = nlp(text.lower())
    
    # Extract matching skills from the known skills list
    extracted_skills = [
        skill for skill in KNOWN_SKILLS if skill in text.lower()
    ]
    
    # Return unique skills
    return list(set(extracted_skills))

@csrf_exempt
def get_results(request):
    try:
        # Ensure the request method is POST
        if request.method != "POST":
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

        # Parse JSON data from the request body
        try:
            data = json.loads(request.body)
            job_description = data.get("job_description", "")
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload'}, status=400)

        # Ensure job description is provided
        if not job_description or not job_description.strip():
            return JsonResponse({'status': 'error', 'message': 'Job description is required'}, status=400)

        # Extract skills from the job description
        jd_skills = extract_skills_from_text(job_description)
        if not jd_skills:
            return JsonResponse({'status': 'error', 'message': 'No skills found in job description'}, status=400)

        # Fetch resumes with non-empty `skills` field
        resumes = Resume.objects.exclude(skills__isnull=True).exclude(skills__exact="")
        if not resumes.exists():
            return JsonResponse({'status': 'success', 'data': [], 'message': 'No resumes found'}, status=200)

        # Prepare data for comparison
        shortlisted_resumes = []
        for resume in resumes:
            # Extract skills from the resume
            resume_skills = [skill.strip().lower() for skill in resume.skills.split(",") if skill.strip()]
            
            # Check if all JD skills are in the resume's skills
            if all(skill in resume_skills for skill in jd_skills):
                shortlisted_resumes.append({
                    'id': resume.id,
                    'name': resume.name,
                    'email': resume.email,
                    'phone': resume.phone,
                    'skills': resume.skills,
                })

        # Return the shortlisted resumes
        return JsonResponse({'status': 'success', 'data': shortlisted_resumes}, status=200)

    except Exception as e:
        # Handle unexpected exceptions
        return JsonResponse({'status': 'error', 'message': f'Error processing resumes: {str(e)}'}, status=500)
    try:
        # Ensure the request method is POST
        if request.method != "POST":
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

        # Initialize job_description with a default value
        job_description = None

        # Parse JSON data from the request body
        try:
            data = json.loads(request.body)
            job_description = data.get("job_description", "")
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload'}, status=400)

        # Ensure job description is provided
        if not job_description or not job_description.strip():
            return JsonResponse({'status': 'error', 'message': 'Job description is required'}, status=400)

        # Fetch resumes with non-empty `resume_text`
        resumes = Resume.objects.exclude(resume_text__isnull=True).exclude(resume_text__exact="")
        if not resumes.exists():
            return JsonResponse({'status': 'success', 'data': [], 'message': 'No resumes found'}, status=200)

        # Prepare data for comparison
        resume_data = [
            {
                'id': resume.id,
                'name': resume.name,
                'email': resume.email,
                'phone': resume.phone,
                'skills': resume.skills,
                'resume_text': resume.resume_text
            }
            for resume in resumes
        ]

        # Combine job description with all resumes' text
        documents = [job_description] + [resume['resume_text'] for resume in resume_data]

        # Calculate TF-IDF vectors
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)

        # Compute cosine similarity
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # Filter resumes with similarity >= 85% and prepare results
        threshold = 0.85
        matching_resumes = [
            {
                'id': resume_data[idx]['id'],
                'name': resume_data[idx]['name'],
                'email': resume_data[idx]['email'],
                'phone': resume_data[idx]['phone'],
                'skills': resume_data[idx]['skills'],
                'similarity': round(similarity * 100, 2)  # Convert similarity to percentage
            }
            for idx, similarity in enumerate(similarities) if similarity >= threshold
        ]

        # Sort matching resumes by similarity in descending order
        matching_resumes = sorted(matching_resumes, key=lambda x: x['similarity'], reverse=True)

        # Return the ranked results
        return JsonResponse({'status': 'success', 'data': matching_resumes}, status=200)

    except Exception as e:
        # Handle unexpected exceptions
        return JsonResponse({'status': 'error', 'message': f'Error processing resumes: {str(e)}'}, status=500)
    try:
        if request.method != "POST":
            return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

        # Get job description from the request
            data = json.loads(request.body)
            job_description = data.get("job_description", "")
        if not job_description:
            return JsonResponse({'status': 'error', 'message': 'Job description is required'}, status=400)

        # Fetch resumes with non-empty `resume_text`
        resumes = Resume.objects.exclude(resume_text__isnull=True).exclude(resume_text__exact="")
        if not resumes.exists():
            return JsonResponse({'status': 'success', 'data': [], 'message': 'No resumes found'}, status=200)

        # Prepare data for comparison
        resume_data = [
            {
                'id': resume.id,
                'name': resume.name,
                'email': resume.email,
                'phone': resume.phone,
                'skills': resume.skills,
                'resume_text': resume.resume_text
            }
            for resume in resumes
        ]

        # Combine job description with all resumes' text
        documents = [job_description] + [resume['resume_text'] for resume in resume_data]

        # Calculate TF-IDF vectors
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)

        # Compute cosine similarity
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # Filter resumes with similarity >= 85% and prepare results
        threshold = 0.01
        matching_resumes = [
            {
                'id': resume_data[idx]['id'],
                'name': resume_data[idx]['name'],
                'email': resume_data[idx]['email'],
                'phone': resume_data[idx]['phone'],
                'skills': resume_data[idx]['skills'],
                'similarity': round(similarity * 100, 2)  # Convert similarity to percentage
            }
            for idx, similarity in enumerate(similarities) if similarity >= threshold
        ]

        # Sort matching resumes by similarity in descending order
        matching_resumes = sorted(matching_resumes, key=lambda x: x['similarity'], reverse=True)

        # Return the ranked results
        return JsonResponse({'status': 'success', 'data': matching_resumes}, status=200)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error processing resumes: {str(e)}'}, status=500)

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
                skills=", ".join(extracted_data['skills']),  # Save skills as a string
                resume_text=extracted_data
            ),

            return JsonResponse(
                {'message': 'Resume uploaded and data saved successfully!', 'data': extracted_data},
                status=200
            )

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'No file uploaded'}, status=400)
