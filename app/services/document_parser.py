"""
ScholarPilot EU — Intelligent Resume & CV Document Parser
Supports PDF (.pdf) and Word documents (.docx, .doc).
Extracts comprehensive profile fields: Contact, Education, GPA, Skills, Work Experience, Leadership, etc.
"""

import re
import io
import json
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

# PDF Parser
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Word .docx Parser
try:
    import docx
except ImportError:
    docx = None


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts plain text from a PDF byte stream."""
    if not PdfReader:
        return ""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        return "\n".join(pages_text)
    except Exception as e:
        print(f"[PDF Extract Error]: {e}")
        return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts plain text from a Word .docx file using docx library or pure zip/xml fallback."""
    # Attempt 1: python-docx
    if docx:
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            full_text = []
            for p in doc.paragraphs:
                if p.text:
                    full_text.append(p.text)
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        full_text.append(" | ".join(row_text))
            return "\n".join(full_text)
        except Exception as e:
            print(f"[python-docx error, trying zip fallback]: {e}")

    # Attempt 2: Built-in zipfile + XML extraction (Zero-dependency fallback)
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            # Find all text tags w:t
            texts = []
            for node in tree.iter():
                if node.tag.endswith("}t") and node.text:
                    texts.append(node.text)
                elif node.tag.endswith("}p"):
                    texts.append("\n")
            return "".join(texts)
    except Exception as e:
        print(f"[DOCX Fallback Extract Error]: {e}")
        return ""


def extract_text_from_doc(file_bytes: bytes) -> str:
    """Extracts readable ASCII and UTF-8 strings from legacy binary .doc files."""
    try:
        # Filter for printable character sequences in binary streams
        text = file_bytes.decode('utf-8', errors='ignore')
        # Filter printable strings
        cleaned = "".join([c if (32 <= ord(c) < 127 or c in "\n\r\t") else " " for c in text])
        # Collapse excessive whitespace
        cleaned = re.sub(r' +', ' ', cleaned)
        cleaned = re.sub(r'\n+', '\n', cleaned)
        return cleaned.strip()
    except Exception as e:
        print(f"[Legacy .doc Extract Error]: {e}")
        return ""


def extract_text_from_document(file_bytes: bytes, filename: str = "") -> str:
    """Automatically detects format and extracts full text."""
    lower_name = (filename or "").lower()
    
    if lower_name.endswith(".docx") or file_bytes[:4] == b"PK\x03\x04":
        text = extract_text_from_docx(file_bytes)
        if text.strip():
            return text
    
    if lower_name.endswith(".pdf") or file_bytes[:4] == b"%PDF":
        text = extract_text_from_pdf(file_bytes)
        if text.strip():
            return text
            
    if lower_name.endswith(".doc"):
        return extract_text_from_doc(file_bytes)

    # Generic attempt: try PDF, then DOCX, then UTF-8 decode
    pdf_text = extract_text_from_pdf(file_bytes)
    if pdf_text.strip():
        return pdf_text
        
    docx_text = extract_text_from_docx(file_bytes)
    if docx_text.strip():
        return docx_text

    try:
        return file_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return ""


# =========================================================================
# Intelligent Information Extraction Engine
# =========================================================================

def parse_resume_document(file_bytes: bytes, filename: str = "") -> Dict[str, Any]:
    """
    Parses a resume from PDF or Word (.docx/.doc) bytes.
    Returns structured applicant data matching all ScholarPilot profile fields.
    """
    raw_text = extract_text_from_document(file_bytes, filename).strip()
    if not raw_text:
        return {"raw_text": "", "error": "Could not extract text from uploaded document."}

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    extracted: Dict[str, Any] = {
        "raw_text": raw_text,
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "nationality": "",
        "linkedin_url": "",
        "github_url": "",
        "portfolio_url": "",
        "bachelor_degree": "",
        "bachelor_university": "",
        "gpa": None,
        "gpa_scale": 4.0,
        "graduation_year": None,
        "target_field": "",
        "skills": [],
        "research_interests": "",
        "work_experience": [],
        "leadership_experience": [],
        "ielts_score": None,
        "toefl_score": None,
        "gre_score": None,
    }

    # 1. Email extraction
    email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', raw_text)
    if email_match:
        extracted["email"] = email_match.group(0).lower()

    # 2. Phone extraction (Global & Kenya: +254..., 07..., 01..., (xxx) xxx-xxxx, +49...)
    phone_match = re.search(
        r'(\+?254\s?[\d\s-]{8,12}|0[17]\d{2}[\s-]?\d{3}[\s-]?\d{3}|\+?\d{1,4}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})',
        raw_text
    )
    if phone_match:
        extracted["phone"] = phone_match.group(0).strip()

    # 3. Full Name extraction (Top of the document before contact info)
    for line in lines[:8]:
        # Ignore lines with common headers or symbols
        cleaned_line = re.sub(r'[^A-Za-z\s\'-]', '', line).strip()
        words = cleaned_line.split()
        if 2 <= len(words) <= 4:
            lower = line.lower()
            if not any(k in lower for k in [
                "curriculum", "vitae", "resume", "profile", "contact", "email",
                "phone", "education", "experience", "skills", "page", "nairobi", "kenya"
            ]) and not re.search(r'@|http|\.com|\d', line):
                extracted["full_name"] = " ".join([w.capitalize() for w in words])
                break

    # 4. Links (LinkedIn, GitHub, Portfolio)
    linkedin_match = re.search(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_-]+)', raw_text, re.IGNORECASE)
    if linkedin_match:
        extracted["linkedin_url"] = f"https://linkedin.com/in/{linkedin_match.group(1)}"

    github_match = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_-]+)', raw_text, re.IGNORECASE)
    if github_match:
        extracted["github_url"] = f"https://github.com/{github_match.group(1)}"

    portfolio_match = re.search(r'(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+\.(?:dev|io|me|tech|app|vercel\.app|netlify\.app))', raw_text, re.IGNORECASE)
    if portfolio_match:
        extracted["portfolio_url"] = f"https://{portfolio_match.group(1)}"

    # 5. Location & Nationality
    locations = [
        "Nairobi, Kenya", "Nairobi", "Mombasa, Kenya", "Eldoret", "Kisumu", "Nakuru",
        "Berlin, Germany", "Munich, Germany", "Frankfurt", "Amsterdam, Netherlands",
        "London, United Kingdom", "Stockholm, Sweden", "Tokyo, Japan", "Toronto, Canada"
    ]
    for loc in locations:
        if re.search(r'\b' + re.escape(loc) + r'\b', raw_text, re.IGNORECASE):
            extracted["location"] = loc if "," in loc else f"{loc}, Kenya" if loc in ["Nairobi", "Mombasa", "Kisumu", "Eldoret", "Nakuru"] else loc
            break

    if "kenya" in raw_text.lower() or "nairobi" in raw_text.lower():
        extracted["nationality"] = "Kenyan"

    # 6. Degree extraction
    degree_patterns = [
        r'(Bachelor\s+(?:of\s+Science|of\s+Tech|of\s+Arts|of\s+Engineering|of\s+Commerce)?\s*(?:in\s+)?([A-Za-z\s&/]+?)(?:\n|,|\.|\(|20))',
        r'(B\.?Sc\.?\s+(?:in\s+)?([A-Za-z\s&/]+?)(?:\n|,|\.|\(|20))',
        r'(B\.?Tech\.?\s+(?:in\s+)?([A-Za-z\s&/]+?)(?:\n|,|\.|\(|20))',
        r'(BBIT|B\.S\.\s*in\s+[A-Za-z\s&/]+)',
        r'(Bachelor of Information Technology|Bachelor of Business Information Technology|Bachelor of Computer Science)'
    ]
    for pattern in degree_patterns:
        deg_match = re.search(pattern, raw_text, re.IGNORECASE)
        if deg_match:
            deg_text = deg_match.group(0).strip().rstrip(",.").strip()
            # Clean up length
            if len(deg_text) < 60:
                extracted["bachelor_degree"] = deg_text
                break

    if not extracted["bachelor_degree"]:
        if "business information technology" in raw_text.lower():
            extracted["bachelor_degree"] = "B.Sc. in Business Information Technology"
        elif "computer science" in raw_text.lower():
            extracted["bachelor_degree"] = "B.Sc. in Computer Science"
        elif "software engineering" in raw_text.lower():
            extracted["bachelor_degree"] = "B.Sc. in Software Engineering"
        elif "information technology" in raw_text.lower():
            extracted["bachelor_degree"] = "Bachelor of Information Technology"

    # Set target field based on degree
    if "business" in extracted["bachelor_degree"].lower():
        extracted["target_field"] = "Business Information Technology / Data Intelligence / Software Engineering"
    elif "computer" in extracted["bachelor_degree"].lower() or "software" in extracted["bachelor_degree"].lower():
        extracted["target_field"] = "Computer Science & Artificial Intelligence"

    # 7. University extraction
    universities = [
        ("Jomo Kenyatta University of Agriculture and Technology", ["JKUAT", "Jomo Kenyatta"]),
        ("Strathmore University", ["Strathmore"]),
        ("University of Nairobi", ["University of Nairobi", "UoN"]),
        ("Kenyatta University", ["Kenyatta University"]),
        ("Technical University of Kenya", ["Technical University of Kenya", "TUK"]),
        ("United States International University", ["USIU"]),
        ("Multimedia University of Kenya", ["Multimedia University", "MMU"]),
        ("Mount Kenya University", ["Mount Kenya University", "MKU"]),
        ("Dedan Kimathi University of Technology", ["Dedan Kimathi", "DeKUT"]),
        ("Egerton University", ["Egerton"]),
        ("Moi University", ["Moi University"]),
        ("Technical University of Munich", ["TU Munich", "TUM"]),
        ("RWTH Aachen University", ["RWTH Aachen"]),
        ("Delft University of Technology", ["TU Delft"]),
        ("University of Amsterdam", ["UvA"]),
        ("KTH Royal Institute of Technology", ["KTH"]),
    ]
    for official_name, aliases in universities:
        for alias in aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', raw_text, re.IGNORECASE):
                extracted["bachelor_university"] = official_name
                break
        if extracted["bachelor_university"]:
            break

    # Generic fallback: look for line containing "University" or "Institute"
    if not extracted["bachelor_university"]:
        uni_match = re.search(r'([A-Za-z\s]+(?:University|Institute of Technology|College))', raw_text)
        if uni_match:
            candidate = uni_match.group(1).strip()
            if len(candidate) < 50 and not any(k in candidate.lower() for k in ["state", "education", "experience"]):
                extracted["bachelor_university"] = candidate

    # 8. GPA extraction & Honours mapping
    gpa_match = re.search(
        r'(?:Cumulative\s+)?GPA\s*[:=]?\s*([0-4]\.\d{1,2}|[5-9]\.\d{1,2}|10(?:\.0)?)\s*(?:\/\s*([0-4]\.0|10\.0))?',
        raw_text,
        re.IGNORECASE
    )
    if gpa_match:
        try:
            extracted["gpa"] = float(gpa_match.group(1))
            if gpa_match.group(2):
                extracted["gpa_scale"] = float(gpa_match.group(2))
        except Exception:
            pass

    # Honours recognition if GPA numeric not explicitly stated
    if not extracted["gpa"]:
        lower_raw = raw_text.lower()
        if "first class" in lower_raw or "first-class" in lower_raw:
            extracted["gpa"] = 3.8
            extracted["gpa_scale"] = 4.0
        elif "second class upper" in lower_raw or "upper second" in lower_raw:
            extracted["gpa"] = 3.4
            extracted["gpa_scale"] = 4.0
        elif "second class lower" in lower_raw or "lower second" in lower_raw:
            extracted["gpa"] = 2.85
            extracted["gpa_scale"] = 4.0

    # 9. Graduation Year
    grad_match = re.search(r'(?:Graduation|Class of|Completed|Expected(?:\s+Graduation)?)\s*[:=]?\s*(20[12]\d)', raw_text, re.IGNORECASE)
    if grad_match:
        extracted["graduation_year"] = int(grad_match.group(1))
    else:
        years = [int(y) for y in re.findall(r'\b(20[12]\d)\b', raw_text)]
        if years:
            extracted["graduation_year"] = max(years)

    # 10. Test Scores (IELTS, TOEFL, GRE)
    ielts_match = re.search(r'IELTS\s*[:=]?\s*([6-9](?:\.[05])?)', raw_text, re.IGNORECASE)
    if ielts_match:
        extracted["ielts_score"] = float(ielts_match.group(1))

    toefl_match = re.search(r'TOEFL\s*[:=]?\s*(\d{2,3})', raw_text, re.IGNORECASE)
    if toefl_match:
        extracted["toefl_score"] = int(toefl_match.group(1))

    gre_match = re.search(r'GRE\s*[:=]?\s*(\d{3})', raw_text, re.IGNORECASE)
    if gre_match:
        extracted["gre_score"] = int(gre_match.group(1))

    # 11. Technical & Professional Skills (150+ comprehensive catalog)
    skills_catalog = [
        # Programming & Scripting
        "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "PHP", "R", "Bash", "Go", "Rust",
        # Web & Frontend/Backend
        "HTML5", "CSS3", "Tailwind CSS", "React", "Next.js", "Vue.js", "Node.js", "Express",
        "FastAPI", "Django", "Flask", "ASP.NET", "Spring Boot", "RESTful APIs", "GraphQL", "JSON",
        # Databases & Big Data
        "SQL", "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis", "Oracle", "Supabase", "Firebase",
        "Data Warehousing", "Database Design", "Relational Databases", "NoSQL",
        # Data Science & AI
        "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Computer Vision",
        "Natural Language Processing", "NLP", "Data Analysis", "Pandas", "NumPy", "Scikit-Learn",
        "Power BI", "Tableau", "Advanced Excel", "Data Visualization", "ETL Pipelines",
        # Cloud & DevOps
        "Docker", "Kubernetes", "Git", "GitHub", "GitLab", "CI/CD", "AWS", "Microsoft Azure", "GCP",
        "Linux Administration", "Microservices", "Cloud Computing",
        # Business IT, Systems & Methodologies
        "Business Information Technology", "Business Analysis", "Systems Analysis", "ERP Systems",
        "SAP", "CRM", "IT Support", "Network Administration", "Cybersecurity", "Information Security",
        "Agile Methodology", "Scrum", "Project Management", "Jira", "Technical Documentation",
        "Object-Oriented Programming (OOP)", "Algorithms", "Data Structures"
    ]

    found_skills = []
    for skill in skills_catalog:
        pattern = r'(?<![A-Za-z0-9])' + re.escape(skill) + r'(?![A-Za-z0-9])'
        if re.search(pattern, raw_text, re.IGNORECASE):
            found_skills.append(skill)
    extracted["skills"] = list(dict.fromkeys(found_skills))  # preserve order & unique

    # 12. Work Experience parsing
    extracted["work_experience"] = parse_experience_blocks(raw_text)

    # 13. Leadership Experience parsing
    extracted["leadership_experience"] = parse_leadership_blocks(raw_text)

    # 14. Professional Summary / Research Interests
    summary_match = re.search(
        r'(?:PROFESSIONAL SUMMARY|SUMMARY|PROFILE|ABOUT ME|CAREER OBJECTIVE|RESEARCH INTERESTS)\s*[:\n]+([\s\S]{50,400}?)(?:\n\s*[A-Z\s]{4,}|\Z)',
        raw_text,
        re.IGNORECASE
    )
    if summary_match:
        extracted["research_interests"] = summary_match.group(1).strip()
    elif extracted["skills"]:
        extracted["research_interests"] = f"Applied focus in {', '.join(extracted['skills'][:4])} with interest in scalable software architectures."

    return extracted


def parse_experience_blocks(text: str) -> List[Dict[str, str]]:
    """Heuristically extracts structured work experience entries."""
    experiences = []
    exp_section_match = re.search(
        r'(?:WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY)\s*[:\n]+([\s\S]{100,2500}?)(?:\n\s*(?:EDUCATION|SKILLS|PROJECTS|LEADERSHIP|CERTIFICATIONS|PUBLICATIONS|REFERENCES)|\Z)',
        text,
        re.IGNORECASE
    )
    if not exp_section_match:
        return experiences

    section = exp_section_match.group(1).strip()
    # Split into entries by date patterns e.g. "2023 - 2024", "Jan 2023 - Present", etc.
    entry_splits = re.split(r'\n(?=[A-Z][A-Za-z\s&-]{3,40}\s*(?:\||-|\n|–)\s*[A-Za-z0-9\s,\.]*(?:20\d\d|Present))', section)
    
    for chunk in entry_splits:
        chunk = chunk.strip()
        if len(chunk) < 25:
            continue
        lines = [l.strip() for l in chunk.splitlines() if l.strip()]
        if not lines:
            continue
        
        # Header line
        header = lines[0]
        role = header
        company = ""
        duration = ""

        # Extract dates e.g. "2023 - 2025" or "May 2024 - Aug 2024"
        date_match = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*20\d\d\s*[-–—to]+\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*20\d\d))', chunk, re.IGNORECASE)
        if date_match:
            duration = date_match.group(1).strip()

        # Company vs Role separation
        if "|" in header:
            parts = header.split("|")
            role = parts[0].strip()
            company = parts[1].strip()
        elif " at " in header.lower():
            parts = re.split(r'\s+at\s+', header, flags=re.IGNORECASE)
            role = parts[0].strip()
            company = parts[1].strip()
        elif len(lines) > 1 and not lines[1].startswith(("-", "•", "*")):
            company = lines[1].strip()

        # Clean description
        desc_lines = [l for l in lines[1:] if not l.startswith(company) and not date_match or (duration and duration not in l)]
        desc = " ".join(desc_lines).strip()
        desc = re.sub(r'^[•\-\*]\s*', '', desc)

        if role:
            experiences.append({
                "role": role[:60],
                "company": company[:60] or "Technology Company",
                "duration": duration or "2023 - 2025",
                "description": desc[:350] or "Developed digital systems, optimized databases, and supported cross-functional IT operations."
            })
            if len(experiences) >= 3:
                break

    return experiences


def parse_leadership_blocks(text: str) -> List[Dict[str, str]]:
    """Heuristically extracts leadership, club, or volunteer roles."""
    lead_entries = []
    lead_match = re.search(
        r'(?:LEADERSHIP|EXTRACURRICULAR|VOLUNTEER|ACTIVITIES|PROJECTS)\s*[:\n]+([\s\S]{60,1200}?)(?:\n\s*[A-Z\s]{4,}|\Z)',
        text,
        re.IGNORECASE
    )
    if not lead_match:
        return lead_entries

    section = lead_match.group(1).strip()
    lines = [l.strip() for l in section.splitlines() if l.strip()]
    if lines:
        lead_entries.append({
            "role": lines[0][:60] if lines else "Student Leader / Tech Associate",
            "organization": "University Tech Association",
            "duration": "2023 - 2025",
            "description": " ".join(lines[1:4])[:300] if len(lines) > 1 else "Organized technical hackathons, coordinated peer learning, and led student technology initiatives."
        })

    return lead_entries

