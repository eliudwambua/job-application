import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db
from app.services.ai_tailor import calculate_match_score, generate_sop, generate_tailored_resume, generate_essay_answers
from app.services.playwright_copilot import generate_bookmarklet_code
from app.main import app
from fastapi.testclient import TestClient

print("[1/5] Testing Database Initialization...")
init_db()

conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM opportunities")
count = cursor.fetchone()[0]
cursor.execute("SELECT * FROM profile WHERE id = 1")
profile = dict(cursor.fetchone())
conn.close()
print(f"  ✓ Database initialized! Seeded {count} opportunities.")
print(f"  ✓ Profile loaded for: {profile['full_name']}")

print("\n[2/5] Testing AI Tailoring & Document Synthesis...")
opp_sample = {
    "title": "Erasmus Mundus EMAI Master",
    "organization": "European Consortium",
    "type": "scholarship",
    "country": "Netherlands",
    "funding_type": "fully_funded",
    "requirements": ["B.Sc. in CS", "GPA 3.5+", "IELTS 7.0+"],
    "description": "Prestigious fully funded AI master"
}
match = calculate_match_score(profile, opp_sample)
print(f"  ✓ Calculated Match Score: {match['score']}%")
print(f"  ✓ Match reasons: {len(match['reasons'])} identified")

sop = generate_sop(profile, opp_sample)
assert len(sop) > 500
print(f"  ✓ Generated Statement of Purpose: {len(sop)} characters")

cv = generate_tailored_resume(profile, opp_sample)
assert len(cv) > 300
print(f"  ✓ Generated Tailored Academic CV: {len(cv)} characters")

essays = generate_essay_answers(profile, opp_sample)
assert len(essays) == 3
print(f"  ✓ Generated {len(essays)} scholarship essay responses")

print("\n[3/5] Testing Universal Bookmarklet Generator...")
bookmarklet = generate_bookmarklet_code(profile, sop)
assert bookmarklet.startswith("javascript:")
print(f"  ✓ Bookmarklet JS generated successfully: {len(bookmarklet)} bytes")

print("\n[4/5] Testing FastAPI Web Routes via TestClient...")
# Test routes
from starlette.testclient import TestClient
client = TestClient(app)

r_dash = client.get("/")
assert r_dash.status_code == 200
print("  ✓ GET / (Dashboard) -> 200 OK")

r_opps = client.get("/opportunities")
assert r_opps.status_code == 200
print("  ✓ GET /opportunities -> 200 OK")

r_copilot = client.get("/copilot/1")
assert r_copilot.status_code == 200
print("  ✓ GET /copilot/1 (Copilot Studio) -> 200 OK")

r_apps = client.get("/applications")
assert r_apps.status_code == 200
print("  ✓ GET /applications (Kanban Tracker) -> 200 OK")

r_prof = client.get("/profile")
assert r_prof.status_code == 200
print("  ✓ GET /profile (Profile Vault) -> 200 OK")

print("\n[5/5] ALL TESTS PASSED SUCCESSFULLY! 🚀")

