"""
ScholarPilot EU — Supabase Migration Script
============================================
Migrates all local SQLite data → Supabase cloud database.

Usage:
    python migrate_to_supabase.py

Requirements:
    - .env file with SUPABASE_URL and SUPABASE_KEY set
    - Run from the project root directory
    - Supabase tables must exist (run supabase_schema.sql first)

IMPORTANT: Disable Row Level Security (RLS) in Supabase Dashboard
    → Table Editor → Each table → RLS → Disable RLS
    OR add INSERT/UPDATE policies for the anon role.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
DB_PATH = Path(__file__).parent / "app" / "data" / "scholarpilot.db"


def check_prereqs():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌  SUPABASE_URL or SUPABASE_KEY missing in .env — aborting.")
        sys.exit(1)
    if not DB_PATH.exists():
        print(f"❌  SQLite database not found at {DB_PATH} — aborting.")
        sys.exit(1)
    print(f"✅  Supabase: {SUPABASE_URL}")
    print(f"✅  Database: {DB_PATH}")


def get_sqlite():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_supabase():
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError:
        print("❌  supabase-py not installed. Run:  pip install supabase")
        sys.exit(1)
    except Exception as e:
        print(f"❌  Supabase client error: {e}")
        sys.exit(1)


def migrate_profile(sb, conn):
    print("\n📋  Migrating profile...")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profile WHERE id = 1")
    row = cursor.fetchone()
    if not row:
        print("   ⚠️  No profile row in SQLite — skipping.")
        return 0

    p = dict(row)

    # Parse JSON fields
    for field in ["target_countries", "skills", "work_experience", "leadership_experience"]:
        val = p.get(field, "[]")
        if isinstance(val, str):
            try:
                p[field] = json.loads(val)
            except Exception:
                p[field] = []

    payload = {
        "id": 1,
        "full_name": p.get("full_name", ""),
        "email": p.get("email", ""),
        "phone": p.get("phone", ""),
        "location": p.get("location", ""),
        "nationality": p.get("nationality", ""),
        "linkedin_url": p.get("linkedin_url", ""),
        "github_url": p.get("github_url", ""),
        "portfolio_url": p.get("portfolio_url", ""),
        "target_degree": p.get("target_degree", "Master of Science"),
        "target_field": p.get("target_field", ""),
        "target_countries": p.get("target_countries", []),
        "gpa": float(p.get("gpa") or 3.5),
        "gpa_scale": float(p.get("gpa_scale") or 4.0),
        "bachelor_degree": p.get("bachelor_degree", ""),
        "bachelor_university": p.get("bachelor_university", ""),
        "graduation_year": int(p.get("graduation_year") or 2025),
        "ielts_score": float(p.get("ielts_score") or 7.0),
        "toefl_score": int(p.get("toefl_score") or 100),
        "gre_score": int(p.get("gre_score") or 320),
        "skills": p.get("skills", []),
        "research_interests": p.get("research_interests", ""),
        "work_experience": p.get("work_experience", []),
        "leadership_experience": p.get("leadership_experience", []),
    }

    try:
        result = sb.table("profiles").upsert(payload).execute()
        print(f"   ✅  Profile upserted: {p.get('full_name')} ({p.get('email')})")
        return 1
    except Exception as e:
        print(f"   ❌  Profile upsert failed: {e}")
        return 0


def migrate_opportunities(sb, conn):
    print("\n🌍  Migrating opportunities...")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opportunities ORDER BY id")
    rows = [dict(r) for r in cursor.fetchall()]

    if not rows:
        print("   ⚠️  No opportunities in SQLite — skipping.")
        return 0

    success = 0
    fail = 0
    for opp in rows:
        # Parse requirements JSON
        try:
            reqs = json.loads(opp.get("requirements", "[]"))
        except Exception:
            reqs = []

        payload = {
            "id": opp["id"],
            "title": opp.get("title", ""),
            "organization": opp.get("organization", ""),
            "type": opp.get("type", "scholarship"),
            "country": opp.get("country", ""),
            "city": opp.get("city", ""),
            "deadline": opp.get("deadline", "") or None,
            "funding_type": opp.get("funding_type", "fully_funded"),
            "stipend_amount": opp.get("stipend_amount", ""),
            "degree_level": opp.get("degree_level", "Master"),
            "requirements": reqs,
            "description": opp.get("description", ""),
            "url": opp.get("url", ""),
            "source": opp.get("source", "Curated"),
            "is_bookmarked": bool(opp.get("is_bookmarked", 0)),
        }

        try:
            sb.table("opportunities").upsert(payload).execute()
            print(f"   ✅  [{opp['type'].upper()}] {opp['title'][:60]}...")
            success += 1
        except Exception as e:
            print(f"   ❌  Failed [{opp['id']}] {opp['title'][:40]}: {e}")
            fail += 1

    print(f"\n   📊  Opportunities: {success} migrated, {fail} failed")
    return success


def migrate_applications(sb, conn):
    print("\n📁  Migrating applications...")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications ORDER BY id")
    rows = [dict(r) for r in cursor.fetchall()]

    if not rows:
        print("   ℹ️  No applications to migrate.")
        return 0

    success = 0
    fail = 0
    for a in rows:
        payload = {
            "id": a["id"],
            "opportunity_id": a["opportunity_id"],
            "status": a.get("status", "bookmarked"),
            "match_score": int(a.get("match_score") or 0),
            "notes": a.get("notes", ""),
            "submission_date": a.get("submission_date", "") or None,
        }
        try:
            sb.table("applications").upsert(payload).execute()
            print(f"   ✅  Application #{a['id']} (opp_id={a['opportunity_id']}) → {a['status']}")
            success += 1
        except Exception as e:
            print(f"   ❌  Application #{a['id']} failed: {e}")
            fail += 1

    print(f"\n   📊  Applications: {success} migrated, {fail} failed")
    return success


def migrate_tailored_docs(sb, conn):
    print("\n📄  Migrating tailored documents...")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tailored_docs ORDER BY id")
    rows = [dict(r) for r in cursor.fetchall()]

    if not rows:
        print("   ℹ️  No tailored docs to migrate.")
        return 0

    success = 0
    fail = 0
    for doc in rows:
        try:
            kw = json.loads(doc.get("target_keywords", "[]"))
        except Exception:
            kw = []

        payload = {
            "id": doc["id"],
            "application_id": doc["application_id"],
            "doc_type": doc.get("doc_type", "sop"),
            "title": doc.get("title", ""),
            "content": doc.get("content", ""),
            "target_keywords": kw,
        }
        try:
            sb.table("tailored_docs").upsert(payload).execute()
            print(f"   ✅  Doc #{doc['id']} [{doc['doc_type']}] app_id={doc['application_id']}")
            success += 1
        except Exception as e:
            print(f"   ❌  Doc #{doc['id']} failed: {e}")
            fail += 1

    print(f"\n   📊  Tailored Docs: {success} migrated, {fail} failed")
    return success


def verify_counts(sb):
    print("\n🔍  Verifying Supabase counts...")
    for table in ["profiles", "opportunities", "applications", "tailored_docs"]:
        try:
            result = sb.table(table).select("id", count="exact").execute()
            count = result.count if hasattr(result, "count") else len(result.data)
            print(f"   📊  {table}: {count} rows in Supabase")
        except Exception as e:
            print(f"   ❌  Could not count {table}: {e}")


def main():
    print("=" * 60)
    print("  ScholarPilot EU — Supabase Migration")
    print("=" * 60)

    check_prereqs()
    sb = get_supabase()
    conn = get_sqlite()

    try:
        p = migrate_profile(sb, conn)
        o = migrate_opportunities(sb, conn)
        a = migrate_applications(sb, conn)
        d = migrate_tailored_docs(sb, conn)
    finally:
        conn.close()

    verify_counts(sb)

    print("\n" + "=" * 60)
    print(f"  ✅  Migration complete!")
    print(f"     Profile: {p} row | Opportunities: {o} | Applications: {a} | Docs: {d}")
    print("=" * 60)
    print("\nIf you see ❌ errors above, check:")
    print("  1. Supabase Dashboard → Table Editor → Disable RLS on each table")
    print("  2. supabase_schema.sql has been run in the Supabase SQL Editor")
    print("  3. Your SUPABASE_KEY has write permission (anon key needs RLS disabled)")


if __name__ == "__main__":
    main()

