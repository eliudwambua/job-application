import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.supabase_client import get_supabase, is_supabase_configured, get_supabase_url

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "scholarpilot.db")

def get_sqlite():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_sqlite()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY,
        full_name TEXT DEFAULT '',
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        location TEXT DEFAULT '',
        nationality TEXT DEFAULT '',
        linkedin_url TEXT DEFAULT '',
        github_url TEXT DEFAULT '',
        portfolio_url TEXT DEFAULT '',
        target_degree TEXT DEFAULT 'Master of Science',
        target_field TEXT DEFAULT 'Computer Science / AI / Data Science',
        target_countries TEXT DEFAULT '["Germany", "Netherlands", "Sweden", "United Kingdom"]',
        gpa REAL DEFAULT 3.85,
        gpa_scale REAL DEFAULT 4.0,
        bachelor_degree TEXT DEFAULT 'B.Sc. in Computer Science',
        bachelor_university TEXT DEFAULT 'State University of Technology',
        graduation_year INTEGER DEFAULT 2025,
        ielts_score REAL DEFAULT 7.5,
        toefl_score INTEGER DEFAULT 105,
        gre_score INTEGER DEFAULT 320,
        skills TEXT DEFAULT '["Python", "Machine Learning", "FastAPI", "JavaScript", "Docker", "Algorithms"]',
        research_interests TEXT DEFAULT 'Applied Machine Learning, Distributed Systems, Responsible AI',
        work_experience TEXT DEFAULT '[]',
        leadership_experience TEXT DEFAULT '[]',
        raw_cv_text TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        organization TEXT NOT NULL,
        type TEXT NOT NULL,
        country TEXT NOT NULL,
        city TEXT DEFAULT '',
        deadline TEXT DEFAULT '',
        funding_type TEXT DEFAULT 'fully_funded',
        stipend_amount TEXT DEFAULT '',
        degree_level TEXT DEFAULT 'Master',
        requirements TEXT DEFAULT '[]',
        description TEXT DEFAULT '',
        url TEXT DEFAULT '',
        source TEXT DEFAULT 'Curated',
        is_bookmarked INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER NOT NULL,
        status TEXT DEFAULT 'bookmarked',
        match_score INTEGER DEFAULT 85,
        notes TEXT DEFAULT '',
        submission_date TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tailored_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        doc_type TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        target_keywords TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("SELECT id FROM profile WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO profile (
            id, full_name, email, phone, location, nationality, 
            target_degree, target_field, target_countries, gpa, gpa_scale,
            bachelor_degree, bachelor_university, graduation_year, ielts_score,
            skills, research_interests, work_experience, leadership_experience
        ) VALUES (
            1, 'Applicant', 'applicant@example.com', '', '', '',
            'Master of Science (M.Sc.)', 'Computer Science & Artificial Intelligence',
            '["Germany", "Netherlands", "Sweden", "United Kingdom", "Switzerland"]',
            3.5, 4.0, 'Bachelor Degree', 'University', 2025, 7.0,
            '["Python", "Machine Learning", "FastAPI", "SQL"]',
            'Applied Machine Learning, Distributed Systems, Software Engineering',
            '[]', '[]'
        )
        """)

    cursor.execute("SELECT COUNT(*) FROM opportunities")
    if cursor.fetchone()[0] == 0:
        seed_opportunities(cursor)

    conn.commit()
    conn.close()

def seed_opportunities(cursor):
    curated = [
        {
            "title": "Erasmus Mundus Joint Master Degree (EMJMD) - European Master in Artificial Intelligence (EMAI)",
            "organization": "European Commission & Consortium (UPF Barcelona, Radboud, Sapienza, Ljubljana)",
            "type": "scholarship",
            "country": "Netherlands / Spain / Italy",
            "city": "Nijmegen / Barcelona / Rome",
            "deadline": "2026-01-15",
            "funding_type": "fully_funded",
            "stipend_amount": "€1,400/month + Full 100% Tuition Waiver + Health Insurance (€36,000 total value)",
            "degree_level": "Master of Science",
            "requirements": json.dumps(["B.Sc. in Computer Science, Math, or Engineering", "Min. GPA 3.5/4.0", "IELTS 7.0+ or TOEFL 95+", "2 Reference Letters"]),
            "description": "Prestigious European Union flagship scholarship. Full tuition coverage and €1,400 monthly living allowance across 24 months studying in at least two European countries.",
            "url": "https://www.erasmus-mundus.eu/",
            "source": "Erasmus+ EU Official"
        },
        {
            "title": "DAAD Helmut-Schmidt-Programme (Master's in Public Policy & Good Governance)",
            "organization": "German Academic Exchange Service (DAAD)",
            "type": "scholarship",
            "country": "Germany",
            "city": "Berlin / Munich / Erfurt",
            "deadline": "2026-07-31",
            "funding_type": "fully_funded",
            "stipend_amount": "€934/month + Travel Subsidy + Health Insurance + Free German Language Course",
            "degree_level": "Master",
            "requirements": json.dumps(["Bachelor's degree in Social/Political Sciences, Economics, or Law", "First academic degree above average", "English proficiency proof"]),
            "description": "Full scholarship for future leaders from developing countries at top German universities. Zero tuition fees + monthly stipend.",
            "url": "https://www2.daad.de/deutschland/stipendien/datenbank/en/21148-scholarship-database/",
            "source": "DAAD Germany"
        },
        {
            "title": "DAAD Development-Related Postgraduate Courses (EPOS) - Tech & Engineering",
            "organization": "DAAD & German Universities (TU Munich, RWTH Aachen, TU Berlin)",
            "type": "scholarship",
            "country": "Germany",
            "city": "Munich / Aachen / Berlin",
            "deadline": "2026-09-30",
            "funding_type": "fully_funded",
            "stipend_amount": "€934/month + Full Tuition Exemption + Travel Allowance",
            "degree_level": "Master of Science",
            "requirements": json.dumps(["Relevant Bachelor's degree (top 30%)", "At least 2 years work experience", "IELTS 6.5+ or TOEFL 85+"]),
            "description": "Supports graduates from emerging nations in Sustainable Engineering, Renewable Energy, Computer Science, and Data. Tuition free in Germany + full living stipend.",
            "url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/daad-scholarships/",
            "source": "DAAD Germany"
        },
        {
            "title": "Chevening Scholarship for Master's in the United Kingdom",
            "organization": "UK Foreign, Commonwealth & Development Office (FCDO)",
            "type": "scholarship",
            "country": "United Kingdom",
            "city": "London / Oxford / Cambridge / Edinburgh",
            "deadline": "2026-11-05",
            "funding_type": "fully_funded",
            "stipend_amount": "100% Full UK Tuition + Monthly Stipend (£1,400+) + Return Flights + Visa Fees",
            "degree_level": "One-Year Master's",
            "requirements": json.dumps(["Undergraduate degree equivalent to UK upper second-class 2:1", "Minimum 2 years work experience", "4 detailed leadership & networking essays"]),
            "description": "The UK government's global scholarship program. Covers complete tuition at any UK university, flights, and monthly living allowance. Zero debt.",
            "url": "https://www.chevening.org/scholarships/",
            "source": "Chevening UK"
        },
        {
            "title": "NL Scholarship (formerly Holland Scholarship) + University Grants",
            "organization": "Dutch Ministry of Education & Research Universities (TU Delft, UvA)",
            "type": "scholarship",
            "country": "Netherlands",
            "city": "Amsterdam / Delft / Utrecht",
            "deadline": "2026-02-01",
            "funding_type": "partial",
            "stipend_amount": "€5,000 - €15,000 grant towards tuition fees and initial setup",
            "degree_level": "Master",
            "requirements": json.dumps(["Non-EEA nationality", "Applying for full-time Master's in Netherlands", "Academic excellence (GPA > 3.6/4.0)"]),
            "description": "Financed by the Dutch Ministry of Education and leading Dutch research universities for international master students.",
            "url": "https://www.studyinnl.org/finances/nl-scholarship",
            "source": "Study in NL"
        },
        {
            "title": "Swedish Institute Scholarship for Global Professionals (SISGP)",
            "organization": "Swedish Institute (Government of Sweden)",
            "type": "scholarship",
            "country": "Sweden",
            "city": "Stockholm / Gothenburg / Lund",
            "deadline": "2026-02-28",
            "funding_type": "fully_funded",
            "stipend_amount": "SEK 12,000/month (~€1,100) + 100% Tuition Fees Paid Directly + Travel Grant",
            "degree_level": "Master",
            "requirements": json.dumps(["Citizenship from eligible SI countries", "Min. 3,000 hours work experience", "Proof of leadership"]),
            "description": "Covers 100% tuition fees at top Swedish universities (KTH, Chalmers, Lund, Uppsala) with a generous monthly stipend of 12,000 SEK.",
            "url": "https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/",
            "source": "Swedish Institute"
        },
        {
            "title": "Working Student (Werkstudent) - Software Engineering & AI",
            "organization": "Siemens AG",
            "type": "job",
            "country": "Germany",
            "city": "Munich / Remote in Germany",
            "deadline": "2026-03-31",
            "funding_type": "paid",
            "stipend_amount": "€16 - €22 / hour (up to 20 hrs/week = ~€1,400 - €1,800/month)",
            "degree_level": "Enrolled Master's Student",
            "requirements": json.dumps(["Enrolled in European Master in Computer Science or related", "Python or Java knowledge", "English proficiency"]),
            "description": "Official German 'Werkstudent' contract allowing up to 20 hours/week during semester. Build strong German industry experience.",
            "url": "https://jobs.siemens.com/",
            "source": "Siemens Careers"
        },
        {
            "title": "AI Research & Data Science Working Student",
            "organization": "SAP Labs",
            "type": "job",
            "country": "Germany",
            "city": "Walldorf / Berlin",
            "deadline": "2026-04-15",
            "funding_type": "paid",
            "stipend_amount": "€18 - €24 / hour (up to 20 hrs/week = ~€1,500 - €2,000/month)",
            "degree_level": "Master Student",
            "requirements": json.dumps(["Enrolled Master's student", "Experience with PyTorch, LLMs, or ML pipelines", "Fluent English"]),
            "description": "Work directly on enterprise AI and scalable machine learning workflows while completing your Master's degree in Germany.",
            "url": "https://jobs.sap.com/",
            "source": "SAP Careers"
        },
        {
            "title": "Software Engineer / Full Stack Developer",
            "organization": "Safaricom PLC",
            "type": "job",
            "country": "Kenya",
            "city": "Nairobi",
            "deadline": "2026-05-30",
            "funding_type": "paid",
            "stipend_amount": "KES 180,000 - 280,000 / month + Medical Cover + Bonuses",
            "degree_level": "Bachelor / Master in Business IT, Computer Science",
            "requirements": json.dumps(["Degree in Business Information Technology or Computer Science", "Proficiency in Python, JavaScript/React, and SQL", "Experience building and consuming RESTful APIs", "Team collaboration"]),
            "description": "Join Kenya's leading telecommunications and fintech powerhouse. Build customer-facing platforms, enterprise microservices, and digital financial products powering millions of users daily.",
            "url": "https://www.safaricom.co.ke/careers",
            "source": "Safaricom Careers"
        },
        {
            "title": "Graduate Tech Associate / Software Engineer",
            "organization": "Microsoft Africa Development Centre (ADC)",
            "type": "job",
            "country": "Kenya",
            "city": "Nairobi (Dunhill Towers / Westlands)",
            "deadline": "2026-06-15",
            "funding_type": "paid",
            "stipend_amount": "KES 250,000 - 350,000 / month + Stock Grants + Healthcare",
            "degree_level": "Graduate in BIT / Computer Science",
            "requirements": json.dumps(["Recent graduate in Business Information Technology, Software Engineering, or CS", "Strong analytical problem-solving skills", "Proficiency in modern programming (Python, C#, TypeScript)", "Passion for cloud computing"]),
            "description": "Work at Microsoft's premier engineering hub in Nairobi developing global cloud, AI, and developer tools alongside world-class Microsoft software engineers.",
            "url": "https://careers.microsoft.com/",
            "source": "Microsoft ADC"
        },
        {
            "title": "Data Analyst & Business Intelligence Specialist",
            "organization": "Equity Bank Group",
            "type": "job",
            "country": "Kenya",
            "city": "Nairobi (Equity Centre)",
            "deadline": "2026-04-30",
            "funding_type": "paid",
            "stipend_amount": "KES 150,000 - 220,000 / month + Benefits",
            "degree_level": "B.Sc. in Business Information Technology / Data Science",
            "requirements": json.dumps(["Degree in Business IT, Data Analytics, or Computer Science", "Strong SQL querying & database management skills", "Python for data analysis (Pandas, NumPy)", "Experience creating dashboards and executive business reports"]),
            "description": "Drive financial inclusion across East and Central Africa through data intelligence. Deliver predictive analytics, business dashboards, and data-driven insights across bank divisions.",
            "url": "https://equitygroupholdings.com/careers",
            "source": "Equity Bank Careers"
        },
        {
            "title": "Junior AI & Machine Learning Engineer",
            "organization": "KCB Bank Kenya",
            "type": "job",
            "country": "Kenya",
            "city": "Nairobi (Upper Hill)",
            "deadline": "2026-05-15",
            "funding_type": "paid",
            "stipend_amount": "KES 160,000 - 240,000 / month",
            "degree_level": "Degree in BIT / Computer Science / AI",
            "requirements": json.dumps(["Degree in Business Information Technology or CS", "Understanding of ML algorithms & data pipelines in Python", "Experience with FastAPI/Flask and Git", "Strong problem-solving mindset"]),
            "description": "Deploy machine learning models for credit scoring, fraud prevention, and intelligent conversational banking for KCB digital channels.",
            "url": "https://kcbgroup.com/careers",
            "source": "KCB Careers"
        },
        {
            "title": "IT Systems & Business Analyst",
            "organization": "United Nations Environment Programme (UNEP)",
            "type": "job",
            "country": "Kenya",
            "city": "Nairobi (Gigiri)",
            "deadline": "2026-06-30",
            "funding_type": "paid",
            "stipend_amount": "USD $2,000 - $2,800 / month (tax exempt) + UN benefits",
            "degree_level": "Bachelor in Business Information Technology / MIS / CS",
            "requirements": json.dumps(["Degree in Business Information Technology or related field", "Knowledge of relational databases, cloud infrastructure, and systems documentation", "Fluency in English", "Cross-cultural communication skills"]),
            "description": "Support digital systems, project databases, and information architecture for global environmental initiatives based at the United Nations Headquarters in Gigiri, Nairobi.",
            "url": "https://careers.un.org/",
            "source": "UN Careers Nairobi"
        }
    ]

    for item in curated:
        cursor.execute("""
        INSERT INTO opportunities (
            title, organization, type, country, city, deadline,
            funding_type, stipend_amount, degree_level, requirements,
            description, url, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["title"], item["organization"], item["type"], item["country"], item.get("city", ""),
            item["deadline"], item["funding_type"], item["stipend_amount"], item["degree_level"],
            item["requirements"], item["description"], item["url"], item["source"]
        ))

def get_db():
    return get_sqlite()

def normalize_profile(p: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures profile fields have proper types (float, list, int)."""
    if not p:
        return {}
    
    try:
        p["gpa"] = float(p.get("gpa") if p.get("gpa") is not None else 3.5)
    except Exception:
        p["gpa"] = 3.5

    try:
        p["gpa_scale"] = float(p.get("gpa_scale") if p.get("gpa_scale") is not None else 4.0)
    except Exception:
        p["gpa_scale"] = 4.0

    try:
        p["graduation_year"] = int(p.get("graduation_year") if p.get("graduation_year") is not None else 2025)
    except Exception:
        p["graduation_year"] = 2025

    try:
        p["ielts_score"] = float(p.get("ielts_score") if p.get("ielts_score") is not None else 7.0)
    except Exception:
        p["ielts_score"] = 7.0

    try:
        p["toefl_score"] = int(p.get("toefl_score") if p.get("toefl_score") is not None else 100)
    except Exception:
        p["toefl_score"] = 100

    try:
        p["gre_score"] = int(p.get("gre_score") if p.get("gre_score") is not None else 320)
    except Exception:
        p["gre_score"] = 320

    for field in ["target_countries", "skills", "work_experience", "leadership_experience"]:
        val = p.get(field)
        if isinstance(val, str):
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                try:
                    p[field] = json.loads(val)
                except Exception:
                    p[field] = [x.strip() for x in val.split(",") if x.strip()]
            else:
                p[field] = [x.strip() for x in val.split(",") if x.strip()]
        elif not isinstance(val, list):
            p[field] = []

    return p

def get_profile_data() -> Dict[str, Any]:
    """Fetches the saved profile with instant local retrieval and cloud sync."""
    conn = get_sqlite()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profile WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return normalize_profile(dict(row))
    return {}

def update_profile_data(data: Dict[str, Any]):
    """Saves profile to local database and syncs with Supabase."""
    conn = get_sqlite()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE profile SET
        full_name = ?, email = ?, phone = ?, location = ?, nationality = ?,
        linkedin_url = ?, github_url = ?, portfolio_url = ?,
        target_degree = ?, target_field = ?, target_countries = ?,
        gpa = ?, gpa_scale = ?, bachelor_degree = ?, bachelor_university = ?,
        graduation_year = ?, ielts_score = ?, toefl_score = ?, gre_score = ?,
        skills = ?, research_interests = ?, work_experience = ?, leadership_experience = ?,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
    """, (
        data.get("full_name", ""), data.get("email", ""), data.get("phone", ""), data.get("location", ""), data.get("nationality", ""),
        data.get("linkedin_url", ""), data.get("github_url", ""), data.get("portfolio_url", ""),
        data.get("target_degree", "Master of Science"), data.get("target_field", ""), json.dumps(data.get("target_countries", [])),
        data.get("gpa", 3.85), data.get("gpa_scale", 4.0), data.get("bachelor_degree", ""), data.get("bachelor_university", ""),
        data.get("graduation_year", 2025), data.get("ielts_score", 7.5), data.get("toefl_score", 105), data.get("gre_score", 320),
        json.dumps(data.get("skills", [])), data.get("research_interests", ""), json.dumps(data.get("work_experience", [])), json.dumps(data.get("leadership_experience", []))
    ))
    conn.commit()
    conn.close()

    # Sync with Supabase asynchronously / safely
    sb = get_supabase()
    if sb:
        try:
            sb.table("profiles").upsert({
                "id": 1,
                "full_name": data.get("full_name", ""),
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "location": data.get("location", ""),
                "nationality": data.get("nationality", ""),
                "linkedin_url": data.get("linkedin_url", ""),
                "github_url": data.get("github_url", ""),
                "portfolio_url": data.get("portfolio_url", ""),
                "target_degree": data.get("target_degree", "Master of Science"),
                "target_field": data.get("target_field", ""),
                "gpa": float(data.get("gpa", 3.85)),
                "gpa_scale": float(data.get("gpa_scale", 4.0)),
                "bachelor_degree": data.get("bachelor_degree", ""),
                "bachelor_university": data.get("bachelor_university", ""),
                "graduation_year": int(data.get("graduation_year", 2025)),
                "ielts_score": float(data.get("ielts_score", 7.5)),
                "research_interests": data.get("research_interests", "")
            }).execute()
        except Exception as e:
            print(f"[Supabase Sync Notice]: {e}")

def save_supabase_env_credentials(url: str, key: str):
    """Saves Supabase credentials into .env file."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    new_lines = []
    url_set = False
    key_set = False

    for line in lines:
        if line.startswith("SUPABASE_URL="):
            new_lines.append(f"SUPABASE_URL={url.strip()}\n")
            url_set = True
        elif line.startswith("SUPABASE_KEY="):
            new_lines.append(f"SUPABASE_KEY={key.strip()}\n")
            key_set = True
        else:
            new_lines.append(line)

    if not url_set:
        new_lines.append(f"SUPABASE_URL={url.strip()}\n")
    if not key_set:
        new_lines.append(f"SUPABASE_KEY={key.strip()}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    os.environ["SUPABASE_URL"] = url.strip()
    os.environ["SUPABASE_KEY"] = key.strip()

    import app.supabase_client as sbc
    sbc._supabase_client = None
