-- ==============================================================
-- ScholarPilot EU - Supabase PostgreSQL Database Schema v2
-- Run this in your Supabase Dashboard -> SQL Editor -> Run
-- ==============================================================

-- Drop existing tables (safe re-run)
DROP TABLE IF EXISTS tailored_docs CASCADE;
DROP TABLE IF EXISTS applications CASCADE;
DROP TABLE IF EXISTS opportunities CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;

-- 1. Profiles Table
CREATE TABLE profiles (
    id BIGINT PRIMARY KEY DEFAULT 1,
    full_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    location TEXT DEFAULT '',
    nationality TEXT DEFAULT '',
    linkedin_url TEXT DEFAULT '',
    github_url TEXT DEFAULT '',
    portfolio_url TEXT DEFAULT '',
    target_degree TEXT DEFAULT 'Master of Science',
    target_field TEXT DEFAULT 'Computer Science / AI / Data Science',
    target_countries JSONB DEFAULT '[]'::jsonb,
    gpa NUMERIC(4,2) DEFAULT 3.5,
    gpa_scale NUMERIC(4,2) DEFAULT 4.0,
    bachelor_degree TEXT DEFAULT '',
    bachelor_university TEXT DEFAULT '',
    graduation_year INT DEFAULT 2025,
    ielts_score NUMERIC(3,1) DEFAULT 7.0,
    toefl_score INT DEFAULT 100,
    gre_score INT DEFAULT 320,
    skills JSONB DEFAULT '[]'::jsonb,
    research_interests TEXT DEFAULT '',
    work_experience JSONB DEFAULT '[]'::jsonb,
    leadership_experience JSONB DEFAULT '[]'::jsonb,
    raw_cv_text TEXT DEFAULT '',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Opportunities Table
CREATE TABLE opportunities (
    id BIGINT PRIMARY KEY,
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'scholarship',
    country TEXT NOT NULL,
    city TEXT DEFAULT '',
    deadline TEXT DEFAULT '',
    funding_type TEXT DEFAULT 'fully_funded',
    stipend_amount TEXT DEFAULT '',
    degree_level TEXT DEFAULT 'Master',
    requirements JSONB DEFAULT '[]'::jsonb,
    description TEXT DEFAULT '',
    url TEXT DEFAULT '',
    source TEXT DEFAULT 'Curated',
    is_bookmarked BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-increment sequence for new opportunities added from UI
CREATE SEQUENCE IF NOT EXISTS opportunities_id_seq START 100;
ALTER TABLE opportunities ALTER COLUMN id SET DEFAULT nextval('opportunities_id_seq');

-- 3. Applications Table
CREATE TABLE applications (
    id BIGINT PRIMARY KEY,
    opportunity_id BIGINT REFERENCES opportunities(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'bookmarked',
    match_score INT DEFAULT 0,
    notes TEXT DEFAULT '',
    submission_date TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE SEQUENCE IF NOT EXISTS applications_id_seq START 100;
ALTER TABLE applications ALTER COLUMN id SET DEFAULT nextval('applications_id_seq');

-- 4. Tailored Documents Table
CREATE TABLE tailored_docs (
    id BIGINT PRIMARY KEY,
    application_id BIGINT REFERENCES applications(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    target_keywords JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE SEQUENCE IF NOT EXISTS tailored_docs_id_seq START 100;
ALTER TABLE tailored_docs ALTER COLUMN id SET DEFAULT nextval('tailored_docs_id_seq');

-- ==============================================================
-- IMPORTANT: Disable Row Level Security on all tables
-- (required for the anon/publishable API key to read & write)
-- ==============================================================
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities DISABLE ROW LEVEL SECURITY;
ALTER TABLE applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE tailored_docs DISABLE ROW LEVEL SECURITY;
