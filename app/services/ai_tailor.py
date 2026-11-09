import json
import re
from typing import Dict, Any, List

def safe_float(val, default=0.0) -> float:
    try:
        if val is None or val == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0) -> int:
    try:
        if val is None or val == "":
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default

def safe_list(val) -> List[Any]:
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            try:
                return json.loads(val)
            except Exception:
                pass
        return [item.strip() for item in val.split(",") if item.strip()]
    return []

def calculate_match_score(profile: Dict[str, Any], opp: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates eligibility & relevance score between applicant profile and opportunity."""
    score = 65  # baseline
    reasons = []
    gaps = []

    # 1. GPA check with safe float conversion
    user_gpa = safe_float(profile.get("gpa"), 3.5)
    gpa_scale = safe_float(profile.get("gpa_scale"), 4.0)
    if gpa_scale <= 0:
        gpa_scale = 4.0

    normalized_gpa = (user_gpa / gpa_scale) * 4.0

    if normalized_gpa >= 3.7:
        score += 15
        reasons.append("Exceptional GPA (top tier academic qualification)")
    elif normalized_gpa >= 3.2:
        score += 10
        reasons.append("Solid competitive GPA meeting European standards")
    else:
        score -= 5
        gaps.append("GPA is close to minimum threshold; emphasize research or work experience")

    # 2. English Proficiency with safe float/int conversion
    ielts = safe_float(profile.get("ielts_score"), 0.0)
    toefl = safe_int(profile.get("toefl_score"), 0)

    if ielts >= 7.0 or toefl >= 95:
        score += 10
        reasons.append(f"Strong English proficiency (IELTS {ielts} / TOEFL {toefl}) exceeds requirement")
    elif ielts >= 6.5 or toefl >= 80:
        score += 5
        reasons.append("Meets standard English language requirement")
    else:
        gaps.append("Ensure official IELTS 6.5+ or TOEFL score report is submitted")

    # 3. Field / Skills Alignment
    profile_skills = safe_list(profile.get("skills"))
    opp_text = f"{opp.get('title', '')} {opp.get('description', '')} {opp.get('requirements', '')}".lower()
    matched_skills = [s for s in profile_skills if isinstance(s, str) and s.lower() in opp_text]
    
    if len(matched_skills) >= 3:
        score += 10
        reasons.append(f"Key skills matched: {', '.join(matched_skills[:4])}")
    elif len(matched_skills) >= 1:
        score += 5
        reasons.append(f"Relevant skills identified: {', '.join(matched_skills)}")

    # 4. Target Country match
    target_countries = safe_list(profile.get("target_countries"))
    opp_country = str(opp.get("country", ""))
    if any(isinstance(tc, str) and tc.lower() in opp_country.lower() for tc in target_countries):
        score += 5
        reasons.append(f"Opportunity matches target region preference: {opp_country}")

    score = max(40, min(98, score))

    return {
        "score": score,
        "reasons": reasons,
        "gaps": gaps if gaps else ["Ensure application is submitted at least 48 hours before deadline"]
    }

def generate_sop(profile: Dict[str, Any], opp: Dict[str, Any]) -> str:
    """Generates a comprehensive, tailored Statement of Purpose / Motivation Letter."""
    name = profile.get("full_name") or "Applicant"
    email = profile.get("email") or ""
    phone = profile.get("phone") or ""
    bachelor_deg = profile.get("bachelor_degree") or "Bachelor's Degree"
    bachelor_uni = profile.get("bachelor_university") or "State University"
    grad_year = profile.get("graduation_year") or 2025
    gpa = profile.get("gpa") or "3.8"
    gpa_scale = profile.get("gpa_scale") or "4.0"
    research_interests = profile.get("research_interests") or "Applied AI and Distributed Systems"
    target_field = profile.get("target_field") or "Computer Science"

    opp_title = opp.get("title") or "Master's Program"
    opp_org = opp.get("organization") or "Admissions Committee"
    opp_country = opp.get("country") or "Europe"
    funding_type = opp.get("funding_type") or "scholarship"

    work_exp = safe_list(profile.get("work_experience"))
    lead_exp = safe_list(profile.get("leadership_experience"))

    work_highlight = ""
    if work_exp and len(work_exp) > 0 and isinstance(work_exp[0], dict):
        first_w = work_exp[0]
        work_highlight = f"During my tenure as a {first_w.get('role', 'Specialist')} at {first_w.get('company', 'Industry Labs')}, I tackled challenging technical frontiers, specifically: {first_w.get('description', 'spearheading systems development')}."
    else:
        work_highlight = f"Through rigorous laboratory coursework and independent research at {bachelor_uni}, I developed strong empirical competencies and applied problem-solving methodologies."

    lead_highlight = ""
    if lead_exp and len(lead_exp) > 0 and isinstance(lead_exp[0], dict):
        first_l = lead_exp[0]
        lead_highlight = f"Beyond technical execution, serving as {first_l.get('role', 'Leader')} at {first_l.get('organization', 'Community')}, where I {first_l.get('description', 'mentored peers and organized technical initiatives')}, honed my cross-cultural collaboration and leadership resilience."
    else:
        lead_highlight = "Collaborative team projects and peer mentorship have instilled in me a steadfast commitment to scientific integrity and open exchange."

    sop = f"""STATEMENT OF PURPOSE & MOTIVATION

Applicant: {name}
Email: {email} | Phone: {phone}
Applying to: {opp_title}
Institution / Consortium: {opp_org} ({opp_country})

Dear Members of the Academic Selection and Scholarship Committee,

I am writing to express my earnest enthusiasm and formally submit my application for the {opp_title} supported by {opp_org}. As a graduate with a {bachelor_deg} from {bachelor_uni} (Class of {grad_year}, GPA: {gpa}/{gpa_scale}), my academic trajectory and research ambitions in {target_field} align directly with the vision, rigorous curriculum, and transnational exposure embodied by your prestigious program.

### 1. Academic Foundation & Technical Trajectory
During my undergraduate tenure, I deliberately pursued an intensive trajectory grounded in analytical depth and practical engineering. My senior investigations focused on {research_interests}, challenging me to examine theoretical foundations while engineering scalable implementations. Maintaining a cumulative GPA of {gpa}/{gpa_scale} reflected not merely academic discipline, but a deep curiosity to explore beyond syllabus benchmarks.

{work_highlight} This exposure underscored that modern challenges cannot be resolved in isolation; they necessitate robust methodology, reproducible experimentation, and an agile mindset.

### 2. Alignment with {opp_org} and European Academic Excellence
The {opp_title} stands out internationally for its unmatched standard of pedagogical rigor and collaborative research infrastructure. Studying in {opp_country} will immerse me in an academic environment renowned for innovation, academic freedom, and world-class faculty. 

Specifically, your program's emphasis on interdisciplinary problem-solving matches my focus on {research_interests}. The opportunity to engage with international peers across top European institutions will provide the exact intellectual impetus needed to elevate my research from theoretical proofs to societal applications.

### 3. Leadership, Resilience & Cross-Cultural Contribution
{lead_highlight}

As an international scholar in {opp_country}, I am prepared to act as an active contributor rather than a passive recipient. I look forward to participating actively in seminar discourses, hackathons, and university student initiatives, representing the collaborative ethos of {opp_org}.

### 4. Career Vision & Long-Term Societal Impact
Upon completion of my Master's studies, I intend to bridge advanced research in {target_field} with high-impact industry and public sector solutions. Benefiting from the support of this {funding_type} opportunity will eliminate financial constraints, enabling me to dedicate 100% of my energy toward academic excellence, impactful publications, and international collaboration.

I am deeply confident that my rigorous academic background, proven work ethic, and clear research direction make me a worthy candidate for admission and scholarship award. Thank you for your time, consideration, and dedication to fostering international scholars.

Respectfully submitted,

{name}
"""
    return sop.strip()

def generate_tailored_resume(profile: Dict[str, Any], opp: Dict[str, Any]) -> str:
    """Generates an ATS-optimized, tailored CV text ready for European formats."""
    name = profile.get("full_name") or "Applicant"
    email = profile.get("email") or ""
    phone = profile.get("phone") or ""
    location = profile.get("location") or ""
    linkedin = profile.get("linkedin_url") or ""
    github = profile.get("github_url") or ""
    bachelor_deg = profile.get("bachelor_degree") or "B.Sc."
    bachelor_uni = profile.get("bachelor_university") or "University"
    grad_year = profile.get("graduation_year") or 2025
    gpa = profile.get("gpa") or "3.8"
    gpa_scale = profile.get("gpa_scale") or "4.0"
    skills = safe_list(profile.get("skills"))

    work_exp = safe_list(profile.get("work_experience"))
    lead_exp = safe_list(profile.get("leadership_experience"))

    opp_title = opp.get("title") or "Target Program"
    opp_org = opp.get("organization") or "Institution"

    links = " | ".join(filter(None, [email, phone, location, linkedin, github]))

    work_str = ""
    for w in work_exp:
        if isinstance(w, dict):
            work_str += f"""
**{w.get('role', 'Role')}** | {w.get('company', 'Organization')} ({w.get('duration', 'Period')})
- Spearheaded development and technical deliverables: {w.get('description', '')}
- Applied agile engineering practices, continuous integration, and technical documentation.
- Collaborated with multidisciplinary cross-functional teams to exceed benchmark performance metrics.
"""

    lead_str = ""
    for l in lead_exp:
        if isinstance(l, dict):
            lead_str += f"""
**{l.get('role', 'Leader')}** | {l.get('organization', 'Organization')} ({l.get('duration', 'Period')})
- {l.get('description', '')}
- Coordinated cross-cultural peer activities, workshops, and student mentorship programs.
"""

    cv = f"""# {name}
{links}

---

## PROFESSIONAL & ACADEMIC SUMMARY
Dedicated, high-achieving candidate ({bachelor_deg}) targeting {opp_title} at {opp_org}. Proven academic record (GPA: {gpa}/{gpa_scale}) combined with solid practical expertise in {', '.join(skills[:5]) if skills else 'Modern Technologies'}. Demonstrates recognized leadership, research aptitude in {profile.get('research_interests', 'advanced systems')}, and a strong work ethic tailored for rigorous European graduate studies and student-employment positions.

---

## EDUCATION
**{bachelor_deg}**
*{bachelor_uni}* | Expected / Graduated: {grad_year}
- Cumulative GPA: {gpa} / {gpa_scale}
- Key Coursework: Algorithms & Data Structures, Distributed Systems, Artificial Intelligence, Database Management, Linear Algebra & Probability.
- Standardized Exams: IELTS {profile.get('ielts_score', 'N/A')} | GRE {profile.get('gre_score', 'N/A')}

---

## TECHNICAL & RESEARCH COMPETENCIES
- **Core Specializations:** {', '.join(skills) if skills else 'Computer Science & Software Development'}
- **Research Domains:** {profile.get('research_interests', 'Systems')}
- **Languages:** English (Proficient/Academic), Working knowledge of target European languages.

---

## PROFESSIONAL & RESEARCH EXPERIENCE
{work_str if work_str else "- Undergraduate Research & Software Projects: Built full-stack applications and scientific computing pipelines."}

---

## LEADERSHIP & COMMUNITY ENGAGEMENT
{lead_str if lead_str else "- Active participant in academic student bodies, coding hackathons, and peer tutoring networks."}
"""
    return cv.strip()

def generate_essay_answers(profile: Dict[str, Any], opp: Dict[str, Any]) -> List[Dict[str, str]]:
    name = profile.get("full_name") or "Applicant"
    opp_title = opp.get("title") or "Scholarship"
    opp_org = opp.get("organization") or "Consortium"
    bachelor_deg = profile.get("bachelor_degree") or "Bachelor's Degree"
    field = profile.get("target_field") or "Computer Science"

    essays = [
        {
            "question": "1. Leadership and Influencing: Describe a situation where you demonstrated leadership and influenced a positive outcome.",
            "answer": (
                f"During my undergraduate studies at {profile.get('bachelor_university', 'university')}, "
                f"our team tackled a high-stakes project requiring the deployment of an end-to-end data processing system. "
                "Faced with tight deadlines and conflicting technical opinions regarding architecture, I stepped forward as technical lead. "
                "I instituted transparent daily scrums, dissected the deliverables into modular milestones, and conducted targeted code reviews. "
                "When a critical pipeline bottleneck threatened delivery, I analyzed memory profiling data and restructured our asynchronous ingestion workers, "
                "reducing latency by 40%. More importantly, I fostered an inclusive atmosphere where each member took ownership of distinct modules, "
                "leading to our project receiving the highest departmental distinction and inspiring two junior cohorts to build upon our codebase."
            )
        },
        {
            "question": f"2. Why {opp_title}? How does this specific program match your academic objectives?",
            "answer": (
                f"The {opp_title} offered by {opp_org} uniquely combines theoretical depth with international, multi-institutional exposure that is unavailable in traditional single-campus degrees. "
                f"Having prepared my academic foundation with a {bachelor_deg} (GPA {profile.get('gpa', 3.8)}/{profile.get('gpa_scale', 4.0)}), "
                f"I seek to specialize in {field}. Your program's curriculum allows me to study cutting-edge methodologies under leading European faculty, "
                "while undertaking practical research in state-of-the-art laboratories. "
                "Furthermore, the cross-border European mobility will broaden my perspective, teaching me to solve complex computational problems in diverse cultural and regulatory environments."
            )
        },
        {
            "question": "3. Future Career Plan & Societal Impact: How will your master's studies contribute to your community and profession?",
            "answer": (
                f"My long-term vision is to lead research and engineering initiatives in {field} that address critical societal infrastructure needs, "
                "such as equitable healthcare AI and sustainable computing systems. "
                f"Completing my Master's with {opp_org} will equip me with both the empirical rigor and the professional European network required to publish high-impact findings and guide ethical deployments. "
                "In the years following graduation, I plan to establish mentorship bridges between European academic hubs and emerging scholars from my home region, "
                "facilitating open-source educational resources and collaborative research pipelines."
            )
        }
    ]
    return essays
