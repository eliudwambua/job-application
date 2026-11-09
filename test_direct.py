import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db, get_profile_data
from app.services.ai_tailor import calculate_match_score

print("1. Running init_db()...")
try:
    init_db()
    print("   ✓ init_db OK")
except Exception as e:
    print("   ✗ init_db failed:")
    traceback.print_exc()

print("2. Fetching profile data...")
try:
    profile = get_profile_data()
    print("   ✓ Profile fetched:", profile.get("full_name"), profile.get("email"))
except Exception as e:
    print("   ✗ get_profile_data failed:")
    traceback.print_exc()

print("3. Querying SQLite opportunities...")
try:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opportunities ORDER BY id DESC LIMIT 6")
    opps = [dict(r) for r in cursor.fetchall()]
    print(f"   ✓ Fetched {len(opps)} opportunities")
    for o in opps:
        m = calculate_match_score(profile, o)
        print(f"     Match: {o['title'][:30]}... -> {m['score']}%")
    conn.close()
except Exception as e:
    print("   ✗ Opportunities query / match score failed:")
    traceback.print_exc()

print("4. Testing Template Rendering...")
try:
    from app.main import templates
    from starlette.requests import Request
    req = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    resp = templates.TemplateResponse("dashboard.html", {
        "request": req,
        "profile": profile,
        "total_opps": len(opps),
        "total_apps": 0,
        "total_docs": 0,
        "total_submitted": 0,
        "opportunities": opps,
        "recent_applications": [],
        "supabase_connected": False,
        "supabase_url": "",
        "active_tab": "dashboard"
    })
    print("   ✓ Template dashboard.html rendered successfully! Length:", len(resp.body))
except Exception as e:
    print("   ✗ Template rendering failed:")
    traceback.print_exc()

print("ALL DIRECT CHECKS FINISHED.")

