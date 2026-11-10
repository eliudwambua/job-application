import os
import json
import asyncio
from typing import Optional, List
from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db, get_db, get_profile_data, update_profile_data, save_supabase_env_credentials
from app.supabase_client import is_supabase_configured, get_supabase_url
from app.services.pdf_parser import parse_pdf_resume
from app.services.document_parser import parse_resume_document
from app.services.ai_tailor import calculate_match_score, generate_sop, generate_tailored_resume, generate_essay_answers
from app.services.playwright_copilot import launch_assisted_apply_session, generate_bookmarklet_code
from app.services.scholarship_scraper import extract_opportunity_from_url
from app.services.job_scraper import get_flattened_sources, scrape_job_posting, get_job_source_by_id, load_sources_data

app = FastAPI(title="ScholarPilot EU - Master's & Job Application Copilot", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def startup_event():
    init_db()

# ----------------- UI Pages -----------------

@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM opportunities")
    total_opps = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_apps = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tailored_docs")
    total_docs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'applied'")
    total_submitted = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM opportunities ORDER BY id DESC LIMIT 6")
    opps = [dict(r) for r in cursor.fetchall()]
    for o in opps:
        try:
            o["requirements"] = json.loads(o["requirements"])
        except Exception:
            o["requirements"] = []
        match = calculate_match_score(profile, o)
        o["match_score"] = match["score"]

    cursor.execute("""
    SELECT a.*, o.title as opp_title, o.organization as opp_org, o.country as opp_country, o.deadline as opp_deadline, o.type as opp_type
    FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    ORDER BY a.updated_at DESC LIMIT 5
    """)
    recent_apps = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "profile": profile,
            "total_opps": total_opps,
            "total_apps": total_apps,
            "total_docs": total_docs,
            "total_submitted": total_submitted,
            "opportunities": opps,
            "recent_applications": recent_apps,
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "dashboard"
        }
    )

@app.get("/scholarships", response_class=HTMLResponse)
async def scholarships_page(request: Request, country: Optional[str] = None, q: Optional[str] = None):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM opportunities WHERE type = 'scholarship'"
    params = []
    if country and country != "all":
        query += " AND country LIKE ?"
        params.append(f"%{country}%")
    if q:
        query += " AND (title LIKE ? OR organization LIKE ? OR description LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    opps = [dict(r) for r in cursor.fetchall()]

    for o in opps:
        try:
            o["requirements"] = json.loads(o["requirements"])
        except Exception:
            o["requirements"] = []
        match = calculate_match_score(profile, o)
        o["match_score"] = match["score"]
        o["match_reasons"] = match["reasons"]

    cursor.execute("SELECT DISTINCT country FROM opportunities WHERE type = 'scholarship'")
    countries = [r[0] for r in cursor.fetchall() if r[0]]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="scholarships.html",
        context={
            "profile": profile,
            "opportunities": opps,
            "countries": countries,
            "current_country": country or "all",
            "search_query": q or "",
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "scholarships"
        }
    )

@app.get("/kenya-jobs", response_class=HTMLResponse)
async def kenya_jobs_page(request: Request, q: Optional[str] = None):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM opportunities WHERE country = 'Kenya'"
    params = []
    if q:
        query += " AND (title LIKE ? OR organization LIKE ? OR description LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    opps = [dict(r) for r in cursor.fetchall()]

    for o in opps:
        try:
            o["requirements"] = json.loads(o["requirements"])
        except Exception:
            o["requirements"] = []
        match = calculate_match_score(profile, o)
        o["match_score"] = match["score"]
        o["match_reasons"] = match["reasons"]

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="kenya_jobs.html",
        context={
            "profile": profile,
            "opportunities": opps,
            "search_query": q or "",
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "kenya_jobs"
        }
    )

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request, country: Optional[str] = None, q: Optional[str] = None):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM opportunities WHERE type IN ('job', 'internship')"
    params = []
    if country and country != "all":
        query += " AND country LIKE ?"
        params.append(f"%{country}%")
    if q:
        query += " AND (title LIKE ? OR organization LIKE ? OR description LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    opps = [dict(r) for r in cursor.fetchall()]

    for o in opps:
        try:
            o["requirements"] = json.loads(o["requirements"])
        except Exception:
            o["requirements"] = []
        match = calculate_match_score(profile, o)
        o["match_score"] = match["score"]
        o["match_reasons"] = match["reasons"]

    cursor.execute("SELECT DISTINCT country FROM opportunities WHERE type IN ('job', 'internship')")
    countries = [r[0] for r in cursor.fetchall() if r[0]]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="jobs.html",
        context={
            "profile": profile,
            "opportunities": opps,
            "countries": countries,
            "current_country": country or "all",
            "search_query": q or "",
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "jobs"
        }
    )

@app.get("/sources", response_class=HTMLResponse)
async def sources_page(
    request: Request,
    region: Optional[str] = None,
    country: Optional[str] = None,
    q: Optional[str] = None
):
    profile = get_profile_data()
    all_sources = get_flattened_sources()
    
    # Filter by region
    filtered = all_sources
    if region and region != "all":
        filtered = [s for s in filtered if s.get("region", "").lower() == region.lower()]

    # Filter by country
    if country and country != "all":
        filtered = [s for s in filtered if s.get("country", "").lower() == country.lower()]

    # Filter by search
    if q:
        query_l = q.lower()
        filtered = [
            s for s in filtered 
            if query_l in s.get("name", "").lower() 
            or query_l in s.get("country", "").lower()
            or query_l in s.get("source_type", "").lower()
        ]

    # Collect distinct countries for dropdown
    countries = sorted(list(set(s.get("country") for s in all_sources if s.get("country") and s.get("country") not in ["Global", "Europe"])))

    return templates.TemplateResponse(
        request=request,
        name="sources.html",
        context={
            "profile": profile,
            "sources": filtered,
            "total_sources": len(all_sources),
            "filtered_count": len(filtered),
            "countries": countries,
            "current_region": region or "all",
            "current_country": country or "all",
            "search_query": q or "",
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "sources"
        }
    )

@app.get("/opportunities", response_class=HTMLResponse)
async def opportunities_page(request: Request, type: Optional[str] = None, country: Optional[str] = None, q: Optional[str] = None):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM opportunities WHERE 1=1"
    params = []

    if type and type != "all":
        query += " AND type = ?"
        params.append(type)
    if country and country != "all":
        query += " AND country LIKE ?"
        params.append(f"%{country}%")
    if q:
        query += " AND (title LIKE ? OR organization LIKE ? OR description LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    opps = [dict(r) for r in cursor.fetchall()]

    for o in opps:
        try:
            o["requirements"] = json.loads(o["requirements"])
        except Exception:
            o["requirements"] = []
        match = calculate_match_score(profile, o)
        o["match_score"] = match["score"]
        o["match_reasons"] = match["reasons"]

    cursor.execute("SELECT DISTINCT country FROM opportunities")
    countries = [r[0] for r in cursor.fetchall() if r[0]]
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="opportunities.html",
        context={
            "profile": profile,
            "opportunities": opps,
            "countries": countries,
            "current_type": type or "all",
            "current_country": country or "all",
            "search_query": q or "",
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "opportunities"
        }
    )

@app.get("/copilot/{opp_id}", response_class=HTMLResponse)
async def copilot_studio_page(request: Request, opp_id: int):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Opportunity not found")
    opp = dict(row)
    try:
        opp["requirements"] = json.loads(opp["requirements"])
    except Exception:
        opp["requirements"] = []

    cursor.execute("SELECT * FROM applications WHERE opportunity_id = ?", (opp_id,))
    app_record = cursor.fetchone()
    if not app_record:
        cursor.execute("INSERT INTO applications (opportunity_id, status, match_score) VALUES (?, 'tailoring', 85)", (opp_id,))
        conn.commit()
        cursor.execute("SELECT * FROM applications WHERE opportunity_id = ?", (opp_id,))
        app_record = cursor.fetchone()
    
    app_data = dict(app_record)

    cursor.execute("SELECT * FROM tailored_docs WHERE application_id = ?", (app_data["id"],))
    docs_rows = cursor.fetchall()
    docs = {d["doc_type"]: dict(d) for d in docs_rows}

    user_name = profile.get("full_name", "")
    force_regen = request.query_params.get("regenerate") == "true"

    sop_content = docs.get("sop", {}).get("content")
    if not sop_content or force_regen or (user_name and user_name != "Alex Morgan" and "Alex Morgan" in (sop_content or "")):
        sop_content = generate_sop(profile, opp)
        if "sop" in docs:
            cursor.execute("UPDATE tailored_docs SET content = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?", (sop_content, docs["sop"]["id"]))
        else:
            cursor.execute("INSERT INTO tailored_docs (application_id, doc_type, title, content) VALUES (?, 'sop', 'Statement of Purpose / Motivation Letter', ?)", (app_data["id"], sop_content))
        conn.commit()

    resume_content = docs.get("resume", {}).get("content")
    if not resume_content or force_regen or (user_name and user_name != "Alex Morgan" and "Alex Morgan" in (resume_content or "")):
        resume_content = generate_tailored_resume(profile, opp)
        if "resume" in docs:
            cursor.execute("UPDATE tailored_docs SET content = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?", (resume_content, docs["resume"]["id"]))
        else:
            cursor.execute("INSERT INTO tailored_docs (application_id, doc_type, title, content) VALUES (?, 'resume', 'ATS-Optimized Academic CV', ?)", (app_data["id"], resume_content))
        conn.commit()

    match_analysis = calculate_match_score(profile, opp)
    essay_answers = generate_essay_answers(profile, opp)
    bookmarklet = generate_bookmarklet_code(profile, sop_content)
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="copilot_studio.html",
        context={
            "profile": profile,
            "opp": opp,
            "application": app_data,
            "sop_content": sop_content,
            "resume_content": resume_content,
            "match_analysis": match_analysis,
            "essay_answers": essay_answers,
            "bookmarklet": bookmarklet,
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "opportunities"
        }
    )

@app.get("/copilot/{opp_id}/print-doc", response_class=HTMLResponse)
async def print_doc_page(request: Request, opp_id: int, type: str = "sop"):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM applications WHERE opportunity_id = ?", (opp_id,))
    app_row = cursor.fetchone()
    content = ""
    title = "Document"

    if app_row:
        app_id = app_row["id"]
        cursor.execute("SELECT title, content FROM tailored_docs WHERE application_id = ? AND doc_type = ?", (app_id, type))
        doc_row = cursor.fetchone()
        if doc_row:
            title = doc_row["title"]
            content = doc_row["content"]

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="print_doc.html",
        context={
            "profile": profile,
            "title": title,
            "content": content
        }
    )

@app.get("/applications", response_class=HTMLResponse)
async def applications_tracker_page(request: Request):
    profile = get_profile_data()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT a.*, o.title as opp_title, o.organization as opp_org, o.country as opp_country, 
           o.deadline as opp_deadline, o.type as opp_type, o.funding_type, o.stipend_amount, o.url as opp_url
    FROM applications a
    JOIN opportunities o ON a.opportunity_id = o.id
    ORDER BY a.updated_at DESC
    """)
    apps = [dict(r) for r in cursor.fetchall()]

    columns = {
        "bookmarked": [],
        "tailoring": [],
        "ready": [],
        "applied": [],
        "interview": [],
        "accepted": []
    }
    for a in apps:
        status = a.get("status", "bookmarked")
        if status in columns:
            columns[status].append(a)
        else:
            columns["bookmarked"].append(a)

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="applications.html",
        context={
            "profile": profile,
            "columns": columns,
            "total_tracked": len(apps),
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "applications"
        }
    )

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    profile = get_profile_data()
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "profile": profile,
            "supabase_connected": is_supabase_configured(),
            "supabase_url": get_supabase_url(),
            "active_tab": "profile"
        }
    )

# ----------------- API Endpoints -----------------

@app.post("/api/profile")
async def save_profile(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    location: str = Form(""),
    nationality: str = Form(""),
    linkedin_url: str = Form(""),
    github_url: str = Form(""),
    portfolio_url: str = Form(""),
    target_degree: str = Form("Master of Science"),
    target_field: str = Form(""),
    target_countries: str = Form("[]"),
    gpa: float = Form(3.85),
    gpa_scale: float = Form(4.0),
    bachelor_degree: str = Form(""),
    bachelor_university: str = Form(""),
    graduation_year: int = Form(2025),
    ielts_score: float = Form(7.5),
    toefl_score: int = Form(105),
    gre_score: int = Form(320),
    skills: str = Form("[]"),
    research_interests: str = Form(""),
    work_experience: str = Form("[]"),
    leadership_experience: str = Form("[]")
):
    try:
        t_countries = json.loads(target_countries) if target_countries.startswith("[") else [c.strip() for c in target_countries.split(",") if c.strip()]
    except Exception:
        t_countries = ["Germany", "Netherlands", "Sweden"]

    try:
        s_list = json.loads(skills) if skills.startswith("[") else [s.strip() for s in skills.split(",") if s.strip()]
    except Exception:
        s_list = []

    try:
        w_exp = json.loads(work_experience) if work_experience.strip() else []
    except Exception:
        w_exp = []

    try:
        l_exp = json.loads(leadership_experience) if leadership_experience.strip() else []
    except Exception:
        l_exp = []

    data = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "location": location,
        "nationality": nationality,
        "linkedin_url": linkedin_url,
        "github_url": github_url,
        "portfolio_url": portfolio_url,
        "target_degree": target_degree,
        "target_field": target_field,
        "target_countries": t_countries,
        "gpa": gpa,
        "gpa_scale": gpa_scale,
        "bachelor_degree": bachelor_degree,
        "bachelor_university": bachelor_university,
        "graduation_year": graduation_year,
        "ielts_score": ielts_score,
        "toefl_score": toefl_score,
        "gre_score": gre_score,
        "skills": s_list,
        "research_interests": research_interests,
        "work_experience": w_exp,
        "leadership_experience": l_exp
    }

    update_profile_data(data)
    return RedirectResponse(url="/profile?saved=true", status_code=303)

@app.post("/api/profile/upload-cv")
async def upload_cv_document(file: UploadFile = File(...)):
    """
    Parses uploaded PDF and Word documents (.docx, .doc),
    extracting full contact info, academic history, GPA, skills,
    work experience, and leadership.
    """
    filename = file.filename or ""
    contents = await file.read()
    
    extracted = parse_resume_document(contents, filename)
    if not extracted or not extracted.get("raw_text"):
        return JSONResponse({
            "status": "error",
            "message": "Could not extract text from document. Ensure it is a valid PDF or Word (.docx/.doc) file."
        }, status_code=400)

    profile = get_profile_data()

    # Full Name
    if extracted.get("full_name"):
        profile["full_name"] = extracted["full_name"]

    # Contact & Links
    if extracted.get("email"):
        profile["email"] = extracted["email"]
    if extracted.get("phone"):
        profile["phone"] = extracted["phone"]
    if extracted.get("location"):
        profile["location"] = extracted["location"]
    if extracted.get("nationality"):
        profile["nationality"] = extracted["nationality"]
    if extracted.get("linkedin_url"):
        profile["linkedin_url"] = extracted["linkedin_url"]
    if extracted.get("github_url"):
        profile["github_url"] = extracted["github_url"]
    if extracted.get("portfolio_url"):
        profile["portfolio_url"] = extracted["portfolio_url"]

    # Academic & Credentials
    if extracted.get("bachelor_degree"):
        profile["bachelor_degree"] = extracted["bachelor_degree"]
    if extracted.get("bachelor_university"):
        profile["bachelor_university"] = extracted["bachelor_university"]
    if extracted.get("gpa") is not None:
        profile["gpa"] = extracted["gpa"]
    if extracted.get("gpa_scale") is not None:
        profile["gpa_scale"] = extracted["gpa_scale"]
    if extracted.get("graduation_year"):
        profile["graduation_year"] = extracted["graduation_year"]
    if extracted.get("ielts_score"):
        profile["ielts_score"] = extracted["ielts_score"]
    if extracted.get("toefl_score"):
        profile["toefl_score"] = extracted["toefl_score"]
    if extracted.get("gre_score"):
        profile["gre_score"] = extracted["gre_score"]

    # Target field & research focus
    if extracted.get("target_field"):
        profile["target_field"] = extracted["target_field"]
    if extracted.get("research_interests"):
        profile["research_interests"] = extracted["research_interests"]

    # Skills merge (unique preservation)
    if extracted.get("skills"):
        existing_skills = profile.get("skills", [])
        if not isinstance(existing_skills, list):
            existing_skills = []
        combined_skills = list(dict.fromkeys(existing_skills + extracted["skills"]))
        profile["skills"] = combined_skills

    # Work & Leadership Experience
    if extracted.get("work_experience") and len(extracted["work_experience"]) > 0:
        profile["work_experience"] = extracted["work_experience"]
    if extracted.get("leadership_experience") and len(extracted["leadership_experience"]) > 0:
        profile["leadership_experience"] = extracted["leadership_experience"]

    # Save to SQLite and Supabase
    update_profile_data(profile)

    captured_summary = {
        "full_name": profile.get("full_name"),
        "email": profile.get("email"),
        "phone": profile.get("phone"),
        "location": profile.get("location"),
        "bachelor_degree": profile.get("bachelor_degree"),
        "bachelor_university": profile.get("bachelor_university"),
        "gpa": profile.get("gpa"),
        "skills_count": len(profile.get("skills", [])),
        "experience_count": len(profile.get("work_experience", [])),
    }

    return JSONResponse({
        "status": "success",
        "message": f"Successfully parsed {filename}! Extracted {captured_summary['skills_count']} skills, GPA {captured_summary['gpa']}, and education details.",
        "extracted": extracted,
        "summary": captured_summary
    })


@app.get("/api/scraper/sources")
async def get_sources_endpoint():
    """Returns the complete 60 sources directory as JSON."""
    return JSONResponse(load_sources_data())


@app.post("/api/scraper/scrape-url")
async def scrape_url_endpoint(payload: dict):
    """
    Scrapes a job posting from any URL (including our 60 directory platforms)
    and returns parsed structured opportunity fields.
    """
    url = (payload.get("url") or "").strip()
    source_id = payload.get("source_id")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required for web scraping.")

    scraped = await scrape_job_posting(url, custom_source_id=source_id)
    return JSONResponse(scraped)


@app.post("/api/scraper/import-job")
async def import_scraped_job(payload: dict):
    """
    Imports a scraped job opportunity directly into the ScholarPilot catalog.
    """
    title = (payload.get("title") or "Imported Opportunity").strip()
    organization = (payload.get("organization") or "Host Organization").strip()
    opp_type = payload.get("type", "job")
    country = payload.get("country", "Europe")
    city = payload.get("city", "")
    deadline = payload.get("deadline", "")
    funding_type = payload.get("funding_type", "paid")
    stipend_amount = payload.get("stipend_amount", "")
    degree_level = payload.get("degree_level", "Bachelor / Master")
    requirements = payload.get("requirements", [])
    if isinstance(requirements, list):
        req_json = json.dumps(requirements)
    else:
        req_json = str(requirements)
    description = payload.get("description", "")
    url = payload.get("url", "")
    source = payload.get("source", "Web Scraper")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO opportunities (
        title, organization, type, country, city, deadline,
        funding_type, stipend_amount, degree_level, requirements,
        description, url, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title, organization, opp_type, country, city, deadline,
        funding_type, stipend_amount, degree_level, req_json,
        description, url, source
    ))
    conn.commit()
    opp_id = cursor.lastrowid
    conn.close()

    # Also sync with Supabase if active
    from app.supabase_client import get_supabase
    sb = get_supabase()
    if sb:
        try:
            sb.table("opportunities").upsert({
                "id": opp_id,
                "title": title,
                "organization": organization,
                "type": opp_type,
                "country": country,
                "city": city,
                "deadline": deadline,
                "funding_type": funding_type,
                "stipend_amount": stipend_amount,
                "degree_level": degree_level,
                "requirements": requirements if isinstance(requirements, list) else [],
                "description": description,
                "url": url,
                "source": source
            }).execute()
        except Exception as e:
            print(f"[Supabase Sync Import Notice]: {e}")

    return JSONResponse({
        "status": "success",
        "opp_id": opp_id,
        "message": f"Successfully scraped and imported '{title}' into catalog!",
        "copilot_url": f"/copilot/{opp_id}"
    })

@app.post("/api/settings/supabase")
async def save_supabase_settings(payload: dict):
    url = payload.get("url", "").strip()
    key = payload.get("key", "").strip()

    if not url or not key:
        raise HTTPException(status_code=400, detail="Supabase URL and API Key are required.")

    save_supabase_env_credentials(url, key)
    return JSONResponse({"status": "success", "message": "Supabase credentials saved successfully!"})

@app.post("/api/opportunities/extract-url")
async def extract_url_endpoint(payload: dict):
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    data = await extract_opportunity_from_url(url)
    return JSONResponse(data)

@app.post("/api/opportunities")
async def create_opportunity(
    title: str = Form(...),
    organization: str = Form(...),
    type: str = Form(...),
    country: str = Form(...),
    city: str = Form(""),
    deadline: str = Form(""),
    funding_type: str = Form("fully_funded"),
    stipend_amount: str = Form(""),
    degree_level: str = Form("Master"),
    requirements: str = Form("[]"),
    description: str = Form(""),
    url: str = Form(""),
    source: str = Form("Manual Entry")
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO opportunities (
        title, organization, type, country, city, deadline,
        funding_type, stipend_amount, degree_level, requirements,
        description, url, source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title, organization, type, country, city, deadline,
        funding_type, stipend_amount, degree_level, requirements,
        description, url, source
    ))
    conn.commit()
    opp_id = cursor.lastrowid
    conn.close()

    return RedirectResponse(url=f"/copilot/{opp_id}", status_code=303)

@app.post("/api/copilot/launch-browser")
async def launch_browser_copilot(payload: dict):
    import subprocess
    import sys
    import webbrowser

    target_url = (payload.get("target_url") or "").strip()
    tailored_doc = payload.get("tailored_doc", "")

    profile = get_profile_data()
    if not target_url or not target_url.startswith("http"):
        target_url = "https://www.google.com"

    # Always use system default browser — most reliable on Windows
    try:
        webbrowser.open(target_url)
    except Exception:
        pass

    return JSONResponse({
        "status": "launched",
        "message": f"Opening {target_url} in your default browser..."
    })


@app.post("/api/copilot/auto-apply")
async def auto_apply_job(payload: dict):
    """
    Auto-apply endpoint: generates docs + opens the application URL.
    The user clicks 'Confirm & Auto-Apply' — we prepare everything and
    open the job portal. User does the final submit (no CAPTCHA bypassing).
    """
    import subprocess
    import sys
    import webbrowser

    opp_id = payload.get("opp_id")
    if not opp_id:
        raise HTTPException(status_code=400, detail="opp_id is required")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp = dict(row)
    try:
        opp["requirements"] = json.loads(opp["requirements"])
    except Exception:
        opp["requirements"] = []

    profile = get_profile_data()

    # Create / find application record
    cursor.execute("SELECT id FROM applications WHERE opportunity_id = ?", (opp_id,))
    existing_app = cursor.fetchone()

    if existing_app:
        app_id = existing_app[0]
        cursor.execute(
            "UPDATE applications SET status = 'tailoring', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (app_id,)
        )
    else:
        match = calculate_match_score(profile, opp)
        cursor.execute(
            "INSERT INTO applications (opportunity_id, status, match_score) VALUES (?, 'tailoring', ?)",
            (opp_id, match["score"])
        )
        app_id = cursor.lastrowid

    conn.commit()

    # Generate SOP if not already cached
    cursor.execute(
        "SELECT id, content FROM tailored_docs WHERE application_id = ? AND doc_type = 'sop'",
        (app_id,)
    )
    sop_row = cursor.fetchone()

    if not sop_row:
        sop_content = generate_sop(profile, opp)
        cursor.execute(
            "INSERT INTO tailored_docs (application_id, doc_type, title, content) VALUES (?, 'sop', ?, ?)",
            (app_id, f"SOP - {opp['title']}", sop_content)
        )
        conn.commit()

    # Mark as applied
    cursor.execute(
        "UPDATE applications SET status = 'applied', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (app_id,)
    )
    conn.commit()
    conn.close()

    # Open the job portal in the user's default browser
    target_url = opp.get("url", "").strip()
    if target_url and target_url.startswith("http"):
        try:
            webbrowser.open(target_url)
        except Exception:
            pass

    return JSONResponse({
        "status": "success",
        "app_id": app_id,
        "message": f"✅ Application prepared! Opening {opp['organization']} portal in your browser. Your SOP and CV are ready in Copilot Studio.",
        "copilot_url": f"/copilot/{opp_id}",
        "target_url": target_url
    })

@app.post("/api/applications/update-status")
async def update_application_status(payload: dict):
    app_id = payload.get("app_id")
    status = payload.get("status")
    notes = payload.get("notes")

    conn = get_db()
    cursor = conn.cursor()

    if notes is not None:
        cursor.execute("UPDATE applications SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, notes, app_id))
    else:
        cursor.execute("UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, app_id))
    
    conn.commit()
    conn.close()

    return JSONResponse({"status": "success", "app_id": app_id, "new_status": status})

@app.post("/api/tailor/save-doc")
async def save_tailored_doc(payload: dict):
    app_id = payload.get("app_id")
    doc_type = payload.get("doc_type")
    content = payload.get("content")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE tailored_docs SET content = ?, created_at = CURRENT_TIMESTAMP
    WHERE application_id = ? AND doc_type = ?
    """, (content, app_id, doc_type))
    conn.commit()
    conn.close()

    return JSONResponse({"status": "saved"})
