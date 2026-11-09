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
from app.services.ai_tailor import calculate_match_score, generate_sop, generate_tailored_resume, generate_essay_answers
from app.services.playwright_copilot import launch_assisted_apply_session, generate_bookmarklet_code
from app.services.scholarship_scraper import extract_opportunity_from_url

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
async def upload_cv_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    extracted = parse_pdf_resume(contents)

    profile = get_profile_data()
    if extracted.get("email"):
        profile["email"] = extracted["email"]
    if extracted.get("phone"):
        profile["phone"] = extracted["phone"]
    if extracted.get("linkedin_url"):
        profile["linkedin_url"] = extracted["linkedin_url"]
    if extracted.get("github_url"):
        profile["github_url"] = extracted["github_url"]
    if extracted.get("gpa"):
        profile["gpa"] = extracted["gpa"]
    if extracted.get("graduation_year"):
        profile["graduation_year"] = extracted["graduation_year"]
    if extracted.get("skills"):
        existing_skills = profile.get("skills", [])
        if isinstance(existing_skills, list):
            combined = list(set(existing_skills + extracted["skills"]))
            profile["skills"] = combined

    update_profile_data(profile)

    return JSONResponse({
        "status": "success",
        "message": "Resume uploaded and parsed successfully!",
        "extracted": extracted
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

    runner_script = os.path.join(os.path.dirname(__file__), "services", "browser_runner.py")
    profile_json = json.dumps(profile)

    try:
        # Spawn detached process that pops up on Windows desktop
        subprocess.Popen(
            [sys.executable, runner_script, target_url, profile_json, tailored_doc],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
    except Exception as e:
        # Reliable fallback: open portal in default browser
        webbrowser.open(target_url)

    return JSONResponse({
        "status": "launched",
        "message": "Browser Copilot launched! Check your Windows taskbar for the window."
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
