import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, Any, Optional

async def extract_opportunity_from_url(url: str) -> Dict[str, Any]:
    """Fetches and parses a scholarship or job announcement page to extract details."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    result = {
        "title": "",
        "organization": "",
        "type": "scholarship",
        "country": "Europe",
        "deadline": "",
        "funding_type": "fully_funded",
        "stipend_amount": "",
        "degree_level": "Master",
        "requirements": [],
        "description": "",
        "url": url,
        "source": "Web Extractor"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Title
                title_tag = soup.find("h1") or soup.find("title")
                if title_tag:
                    result["title"] = title_tag.get_text(strip=True)[:150]

                # Full text
                text = soup.get_text(separator=" ", strip=True)
                result["description"] = text[:1200]

                # Detect type (job vs scholarship)
                lower_text = text.lower()
                if any(k in lower_text for k in ["werkstudent", "working student", "internship", "developer", "engineer", "hourly rate", "salary"]):
                    result["type"] = "job"
                    result["funding_type"] = "paid"
                else:
                    result["type"] = "scholarship"
                    if "fully funded" in lower_text or "tuition waiver" in lower_text:
                        result["funding_type"] = "fully_funded"

                # Detect country
                countries = ["Germany", "United Kingdom", "Netherlands", "Sweden", "Switzerland", "France", "Italy", "Spain", "Denmark", "Norway", "Finland", "Austria", "Belgium", "Ireland"]
                for c in countries:
                    if c.lower() in lower_text:
                        result["country"] = c
                        break

                # Extract deadline regex (e.g. 15 January 2026, 2026-05-30, etc.)
                dl_match = re.search(r'(?:deadline|apply before|closing date)[\s:]*([0-9]{1,2}[\s\/\-][A-Za-z0-9]+[\s\/\-][0-9]{2,4}|[A-Za-z]+[\s][0-9]{1,2},?[\s][0-9]{4})', text, re.IGNORECASE)
                if dl_match:
                    result["deadline"] = dl_match.group(1).strip()
                else:
                    result["deadline"] = "See portal"

                # Extract common requirements
                reqs = []
                if "bachelor" in lower_text or "undergraduate" in lower_text:
                    reqs.append("Recognized Bachelor's degree in relevant discipline")
                if "ielts" in lower_text or "toefl" in lower_text or "english" in lower_text:
                    reqs.append("Proof of English Language Proficiency")
                if "gpa" in lower_text:
                    reqs.append("Competitive GPA / Academic Transcripts")
                if "recommendation" in lower_text or "reference" in lower_text:
                    reqs.append("Letters of Recommendation")
                if "motivation" in lower_text or "statement of purpose" in lower_text:
                    reqs.append("Motivation Letter / Statement of Purpose")

                result["requirements"] = reqs if reqs else ["Academic Transcripts", "Curriculum Vitae", "Motivation Letter"]

    except Exception as e:
        result["description"] = f"Could not automatically fetch page: {str(e)}. You can enter details manually."
        result["title"] = "Custom Opportunity"

    return result

