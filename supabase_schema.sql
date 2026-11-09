-- ==============================================================
-- ScholarPilot EU - Supabase PostgreSQL Database Schema
-- Run this in your Supabase Dashboard -> SQL Editor -> Run
-- ==============================================================

-- 1. Profiles Table
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    phone TEXT DEFAULT '',
    location TEXT DEFAULT '',
    nationality TEXT DEFAULT '',
    linkedin_url TEXT DEFAULT '',
    github_url TEXT DEFAULT '',
    portfolio_url TEXT DEFAULT '',
    target_degree TEXT DEFAULT 'Master of Science (M.Sc.)',
    target_field TEXT DEFAULT 'Computer Science / AI / Data Science',
    target_countries JSONB DEFAULT '["Germany", "Netherlands", "Sweden", "United Kingdom", "Switzerland"]'::jsonb,
    gpa NUMERIC(4,2) DEFAULT 3.85,
    gpa_scale NUMERIC(4,2) DEFAULT 4.0,
    bachelor_degree TEXT DEFAULT 'B.Sc. in Computer Science',
    bachelor_university TEXT DEFAULT 'State University of Technology',
    graduation_year INT DEFAULT 2025,
    ielts_score NUMERIC(3,1) DEFAULT 7.5,
    toefl_score INT DEFAULT 105,
    gre_score INT DEFAULT 320,
    skills JSONB DEFAULT '["Python", "Machine Learning", "FastAPI", "TypeScript", "React", "Docker", "Algorithms"]'::jsonb,
    research_interests TEXT DEFAULT 'Deep Learning architectures, autonomous agents, and scalable distributed systems',
    work_experience JSONB DEFAULT '[{"role": "Software Engineering Intern", "company": "Tech Innovators Lab", "duration": "2024 - 2025", "description": "Built REST APIs with Python and integrated microservices, improving throughput by 35%."}]'::jsonb,
    leadership_experience JSONB DEFAULT '[{"role": "President", "organization": "University AI & Coding Society", "duration": "2023 - 2025", "description": "Organized 3 national hackathons with 600+ participants."}]'::jsonb,
    raw_cv_text TEXT DEFAULT '',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Opportunities Table
CREATE TABLE IF NOT EXISTS opportunities (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    organization TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'scholarship', -- 'scholarship', 'job', 'internship'
    country TEXT NOT NULL,
    city TEXT DEFAULT '',
    deadline TEXT DEFAULT '',
    funding_type TEXT DEFAULT 'fully_funded', -- 'fully_funded', 'partial', 'paid'
    stipend_amount TEXT DEFAULT '',
    degree_level TEXT DEFAULT 'Master',
    requirements JSONB DEFAULT '[]'::jsonb,
    description TEXT DEFAULT '',
    url TEXT DEFAULT '',
    source TEXT DEFAULT 'Curated',
    is_bookmarked BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Applications Pipeline Table
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    opportunity_id INT REFERENCES opportunities(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'bookmarked', -- 'bookmarked', 'tailoring', 'ready', 'applied', 'interview', 'accepted'
    match_score INT DEFAULT 85,
    notes TEXT DEFAULT '',
    submission_date TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tailored Documents Table
CREATE TABLE IF NOT EXISTS tailored_docs (
    id SERIAL PRIMARY KEY,
    application_id INT REFERENCES applications(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL, -- 'sop', 'resume', 'cover_letter', 'essay'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    target_keywords JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed initial default profile if not exists
INSERT INTO profiles (
    id, full_name, email, phone, location, nationality,
    target_degree, target_field, target_countries, gpa, gpa_scale,
    bachelor_degree, bachelor_university, graduation_year, ielts_score,
    skills, research_interests
) VALUES (
    1, 'Alex Morgan', 'alex.morgan.applicant@gmail.com', '+1 (555) 392-8192', 'Global Applicant', 'International',
    'Master of Science (M.Sc.)', 'Computer Science & Artificial Intelligence',
    '["Germany", "Netherlands", "Sweden", "United Kingdom", "Switzerland"]'::jsonb,
    3.85, 4.0, 'B.S. in Computer Science', 'International Tech Institute', 2025, 7.5,
    '["Python", "PyTorch", "FastAPI", "TypeScript", "React", "Docker", "Machine Learning"]'::jsonb,
    'Deep Learning architectures, autonomous agents, and scalable distributed systems'
) ON CONFLICT (id) DO NOTHING;

-- Seed top European opportunities
INSERT INTO opportunities (title, organization, type, country, city, deadline, funding_type, stipend_amount, degree_level, requirements, description, url, source)
VALUES 
(
    'Erasmus Mundus Joint Master Degree (EMJMD) - European Master in Artificial Intelligence (EMAI)',
    'European Commission & Consortium (UPF Barcelona, Radboud, Sapienza)',
    'scholarship',
    'Netherlands / Spain / Italy',
    'Nijmegen / Barcelona',
    '2026-01-15',
    'fully_funded',
    '€1,400/month + 100% Tuition Waiver + Health Insurance (€36,000 total)',
    'Master of Science',
    '["B.Sc. in Computer Science, Math, or Engineering", "Min. GPA 3.5/4.0", "IELTS 7.0+ or TOEFL 95+", "2 Letters of Recommendation"]'::jsonb,
    'Prestigious EU flagship scholarship. Full tuition coverage and €1,400 monthly living allowance across 24 months studying in at least two European countries.',
    'https://www.erasmus-mundus.eu/',
    'Erasmus+ EU Official'
),
(
    'DAAD Helmut-Schmidt-Programme (Master in Public Policy & Good Governance)',
    'German Academic Exchange Service (DAAD)',
    'scholarship',
    'Germany',
    'Berlin / Munich',
    '2026-07-31',
    'fully_funded',
    '€934/month + Travel Subsidy + Health Insurance + Free German Language Course',
    'Master',
    '["Bachelor degree in Social/Political Sciences, Economics, or Law", "First academic degree above average", "English proficiency proof"]'::jsonb,
    'Full scholarship for future leaders at top German universities. Zero tuition fees + monthly stipend.',
    'https://www2.daad.de/deutschland/stipendien/datenbank/en/21148-scholarship-database/',
    'DAAD Germany'
),
(
    'Chevening Scholarship for Master in the United Kingdom',
    'UK Foreign, Commonwealth & Development Office (FCDO)',
    'scholarship',
    'United Kingdom',
    'London / Oxford / Cambridge',
    '2026-11-05',
    'fully_funded',
    '100% Full UK Tuition + Monthly Stipend (£1,400+) + Return Flights',
    'Master (1 Year)',
    '["Undergraduate degree equivalent to UK upper second-class 2:1", "Minimum 2 years work experience", "Leadership essays"]'::jsonb,
    'The UK governments flagship global scholarship covering complete tuition at any UK university, flights, and monthly living allowance.',
    'https://www.chevening.org/scholarships/',
    'Chevening UK'
),
(
    'Working Student (Werkstudent) - Software Engineering & AI',
    'Siemens AG',
    'job',
    'Germany',
    'Munich / Remote',
    '2026-03-31',
    'paid',
    '€16 - €22 / hour (up to 20 hrs/week = ~€1,400 - €1,800/month)',
    'Enrolled Master Student',
    '["Enrolled in European Master in Computer Science or related", "Python or Java knowledge", "English proficiency"]'::jsonb,
    'Official German Werkstudent contract allowing up to 20 hours/week during semester. Build strong German industry experience.',
    'https://jobs.siemens.com/',
    'Siemens Careers'
) ON CONFLICT DO NOTHING;

