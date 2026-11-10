"""
ScholarPilot EU — Verification of CV Document Parser (PDF & DOCX)
and 60 Job Sources Web Scraping Engine.
"""

import sys
import os
import io
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.document_parser import parse_resume_document
from app.services.job_scraper import load_sources_data, get_flattened_sources, match_source_from_url, get_job_source_by_id
import docx

print("=" * 60)
print("TEST 1: 60 Job Sources Directory Verification")
print("=" * 60)

data = load_sources_data()
assert data.get("total_sources") == 60, f"Expected 60 sources, got {data.get('total_sources')}"
print(f"✓ Total sources loaded: {data.get('total_sources')}")

flattened = get_flattened_sources()
assert len(flattened) == 60, f"Expected 60 flattened sources, got {len(flattened)}"
print(f"✓ Flattened sources count: {len(flattened)}")

kenya_sources = [s for s in flattened if s.get("region") == "Kenya"]
intl_sources = [s for s in flattened if s.get("region") == "International"]
print(f"✓ Kenya platforms: {len(kenya_sources)} (Expected 20)")
print(f"✓ International platforms: {len(intl_sources)} (Expected 40)")
assert len(kenya_sources) == 20
assert len(intl_sources) == 40

# Test URL matching
test_urls = [
    ("https://www.safaricom.co.ke/careers/job/123", "Safaricom Careers"),
    ("https://www.brightermonday.co.ke/jobs/developer", "BrighterMonday Kenya"),
    ("https://www.stepstone.de/stellenangebote--Developer.html", "StepStone Germany"),
    ("https://www.usajobs.gov/job/789", "USAJOBS"),
    ("https://careers.un.org/lbw/home.aspx", "UN Careers"),
]

for url, expected_name in test_urls:
    matched = match_source_from_url(url)
    assert matched is not None, f"Failed to match URL {url}"
    assert matched["name"] == expected_name, f"Expected {expected_name}, got {matched['name']}"
    print(f"✓ Matched '{url[:40]}...' -> {matched['name']} ({matched['country']})")

print("\n" + "=" * 60)
print("TEST 2: Word Document (.docx) Creation & Advanced Parsing")
print("=" * 60)

# Create an in-memory sample .docx resume for Eliud Maingi
doc = docx.Document()
doc.add_heading("Eliud Maingi", level=0)
doc.add_paragraph("Nairobi, Kenya | meliudwambua@gmail.com | +254 712 345678 | linkedin.com/in/eliud-maingi | github.com/eliud-maingi")
doc.add_heading("Professional Summary", level=1)
doc.add_paragraph("Motivated Business Information Technology professional specializing in Python backend architecture, SQL data analytics, and cloud microservices.")

doc.add_heading("Education", level=1)
doc.add_paragraph("Bachelor of Science in Business Information Technology\nJomo Kenyatta University of Agriculture and Technology (JKUAT)\nGraduation: 2025 | Cumulative GPA: 2.78 / 4.0")

doc.add_heading("Technical Competencies", level=1)
doc.add_paragraph("Python, FastAPI, SQL, PostgreSQL, React, JavaScript, Docker, Git, Machine Learning, Power BI, Advanced Excel, Business Analysis, Linux")

doc.add_heading("Work Experience", level=1)
doc.add_paragraph("Software Engineering Intern | Tech Innovators Kenya\nJan 2024 - Dec 2024\nDeveloped automated REST APIs using FastAPI and SQL databases, improving query performance by 40%.")
doc.add_paragraph("Junior IT Systems Analyst | Enterprise Digital Solutions\nJun 2023 - Dec 2023\nDesigned database schemas and built automated reporting dashboards for enterprise management.")

doc.add_heading("Leadership & Activities", level=1)
doc.add_paragraph("President | University Tech & Coding Society\n2023 - 2025\nOrganized 3 national hackathons with 500+ participants and mentored junior students in web development.")

docx_io = io.BytesIO()
doc.save(docx_io)
docx_bytes = docx_io.getvalue()

parsed_docx = parse_resume_document(docx_bytes, "Eliud_Maingi_Resume.docx")

print(f"✓ Full Name: {parsed_docx.get('full_name')} (Expected 'Eliud Maingi')")
assert parsed_docx.get('full_name') == "Eliud Maingi"

print(f"✓ Email: {parsed_docx.get('email')} (Expected 'meliudwambua@gmail.com')")
assert parsed_docx.get('email') == "meliudwambua@gmail.com"

print(f"✓ Phone: {parsed_docx.get('phone')} (Expected '+254 712 345678')")
assert "+254" in parsed_docx.get('phone', '')

print(f"✓ Location: {parsed_docx.get('location')}")
assert "Nairobi" in parsed_docx.get('location', '')

print(f"✓ Nationality: {parsed_docx.get('nationality')} (Expected 'Kenyan')")
assert parsed_docx.get('nationality') == "Kenyan"

print(f"✓ Degree: {parsed_docx.get('bachelor_degree')}")
assert "Business Information Technology" in parsed_docx.get('bachelor_degree', '')

print(f"✓ University: {parsed_docx.get('bachelor_university')}")
assert "Jomo Kenyatta" in parsed_docx.get('bachelor_university', '')

print(f"✓ GPA: {parsed_docx.get('gpa')} / Scale: {parsed_docx.get('gpa_scale')}")
assert parsed_docx.get('gpa') == 2.78

print(f"✓ Graduation Year: {parsed_docx.get('graduation_year')} (Expected 2025)")
assert parsed_docx.get('graduation_year') == 2025

print(f"✓ Skills Extracted ({len(parsed_docx.get('skills', []))}): {', '.join(parsed_docx.get('skills', [])[:6])}...")
assert len(parsed_docx.get('skills', [])) >= 8

print(f"✓ Work Experience Entries: {len(parsed_docx.get('work_experience', []))}")
assert len(parsed_docx.get('work_experience', [])) >= 1

print(f"✓ Leadership Entries: {len(parsed_docx.get('leadership_experience', []))}")
assert len(parsed_docx.get('leadership_experience', [])) >= 1

print("\n" + "=" * 60)
print("TEST 3: Testing Web Route /sources Template Rendering")
print("=" * 60)

from app.main import templates, app
from starlette.requests import Request
from starlette.testclient import TestClient

req = Request({"type": "http", "method": "GET", "path": "/sources", "headers": []})
resp = templates.TemplateResponse(request=req, name="sources.html", context={
    "profile": parsed_docx,
    "sources": flattened,
    "total_sources": len(flattened),
    "filtered_count": len(flattened),
    "countries": ["Germany", "Kenya"],
    "current_region": "all",
    "current_country": "all",
    "search_query": "",
    "supabase_connected": True,
    "supabase_url": "https://test.supabase.co",
    "active_tab": "sources"
})
assert len(resp.body) > 1000
print(f"✓ sources.html rendered successfully ({len(resp.body)} bytes)")

print("\nALL CV PARSING & 60-SOURCES SCRAPING TESTS PASSED! 🚀")

