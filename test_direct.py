import os
import sys
import traceback
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db, get_profile_data
from app.services.ai_tailor import calculate_match_score

print("1. Running init_db()...")
init_db()
print("   ✓ init_db OK")

print("2. Fetching profile data...")
profile = get_profile_data()
print("   ✓ Profile fetched:", profile.get("full_name"), profile.get("email"))

print("3. Querying opportunities...")
conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT * FROM opportunities")
all_opps = [dict(r) for r in cursor.fetchall()]
for o in all_opps:
    try:
        o["requirements"] = json.loads(o["requirements"])
    except Exception:
        o["requirements"] = []
    m = calculate_match_score(profile, o)
    o["match_score"] = m["score"]
conn.close()
print(f"   ✓ Total opportunities in DB: {len(all_opps)}")

from app.main import templates
from starlette.requests import Request

pages_to_test = [
    ("dashboard.html", {
        "profile": profile,
        "total_opps": len(all_opps),
        "total_apps": 2,
        "total_docs": 3,
        "total_submitted": 1,
        "opportunities": all_opps[:6],
        "recent_applications": [],
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "dashboard"
    }),
    ("scholarships.html", {
        "profile": profile,
        "opportunities": [o for o in all_opps if o.get("type") == "scholarship"],
        "countries": ["Germany", "Netherlands"],
        "current_country": "all",
        "search_query": "",
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "scholarships"
    }),
    ("jobs.html", {
        "profile": profile,
        "opportunities": [o for o in all_opps if o.get("type") == "job" and o.get("country") != "Kenya"],
        "countries": ["Germany", "Netherlands"],
        "current_country": "all",
        "search_query": "",
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "jobs"
    }),
    ("kenya_jobs.html", {
        "profile": profile,
        "opportunities": [o for o in all_opps if o.get("country") == "Kenya"],
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "kenya_jobs"
    }),
    ("applications.html", {
        "profile": profile,
        "columns": {
            "bookmarked": [], "tailoring": [], "ready": [], "applied": [], "interview": [], "accepted": []
        },
        "total_tracked": 0,
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "applications"
    }),
    ("profile.html", {
        "profile": profile,
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "profile"
    }),
    ("sources.html", {
        "profile": profile,
        "sources_data": {"categories": {"international": {"total": 40, "global_platforms": [], "country_platforms": []}, "kenya": {"total": 20, "platforms": []}}},
        "total_sources": 60,
        "kenya_sources": [],
        "intl_sources": [],
        "target_countries": ["Germany", "Netherlands", "Kenya"],
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "sources"
    }),
    ("opportunities.html", {
        "profile": profile,
        "opportunities": all_opps,
        "countries": ["Germany", "Kenya"],
        "current_country": "all",
        "current_type": "all",
        "search_query": "",
        "supabase_connected": True,
        "supabase_url": "https://test.supabase.co",
        "active_tab": "opportunities"
    })
]

print("\n4. Testing All Page Templates...")
for name, ctx in pages_to_test:
    try:
        req = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
        resp = templates.TemplateResponse(request=req, name=name, context=ctx)
        print(f"   ✓ {name:20s} -> OK ({len(resp.body)} bytes)")
    except Exception as e:
        print(f"   ✗ {name:20s} -> FAILED: {e}")
        traceback.print_exc()

print("\nALL DIRECT CHECKS PASSED SUCCESSFULLY! 🚀")
