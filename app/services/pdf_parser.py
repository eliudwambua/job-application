import re
from typing import Dict, Any, List
from pypdf import PdfReader
import io

def parse_pdf_resume(file_bytes: bytes) -> Dict[str, Any]:
    """Extracts text and key profile information from a resume/CV PDF."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        extracted = {
            "raw_text": full_text.strip(),
            "email": "",
            "phone": "",
            "linkedin_url": "",
            "github_url": "",
            "skills": [],
            "gpa": None,
            "graduation_year": None
        }

        # Email regex
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', full_text)
        if email_match:
            extracted["email"] = email_match.group(0)

        # Phone regex
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', full_text)
        if phone_match:
            extracted["phone"] = phone_match.group(0)

        # LinkedIn regex
        linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', full_text, re.IGNORECASE)
        if linkedin_match:
            extracted["linkedin_url"] = "https://" + linkedin_match.group(0)

        # GitHub regex
        github_match = re.search(r'github\.com/[\w\-]+', full_text, re.IGNORECASE)
        if github_match:
            extracted["github_url"] = "https://" + github_match.group(0)

        # GPA regex
        gpa_match = re.search(r'GPA\s*[:=]?\s*([0-4]\.\d{1,2}|[5-9]\.\d{1,2}|10(?:\.0)?)\s*(?:/\s*(?:4(?:\.0)?|10(?:\.0)?))?', full_text, re.IGNORECASE)
        if gpa_match:
            try:
                extracted["gpa"] = float(gpa_match.group(1))
            except ValueError:
                pass

        # Year regex (e.g. 2021-2025)
        year_match = re.findall(r'20[12]\d', full_text)
        if year_match:
            years = [int(y) for y in year_match]
            extracted["graduation_year"] = max(years)

        # Common Tech & Academic Skills scan
        common_skills = [
            "Python", "JavaScript", "TypeScript", "C++", "Java", "SQL", "PostgreSQL",
            "FastAPI", "React", "Next.js", "Node.js", "Docker", "Kubernetes", "Git",
            "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Computer Vision",
            "Natural Language Processing", "NLP", "Data Analysis", "Pandas", "NumPy",
            "Algorithms", "Data Structures", "Cloud Computing", "AWS", "Azure", "GCP",
            "Research Methodology", "Academic Writing", "Statistics", "Optimization"
        ]
        found_skills = []
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', full_text, re.IGNORECASE):
                found_skills.append(skill)
        extracted["skills"] = found_skills

        return extracted
    except Exception as e:
        return {"raw_text": "", "error": str(e)}

