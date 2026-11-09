import asyncio
import json
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

active_browsers = {}

def generate_bookmarklet_code(profile: Dict[str, Any], tailored_doc: Optional[str] = "") -> str:
    """Generates a JavaScript bookmarklet that autofills applications in ANY browser."""
    profile_json = json.dumps(profile)
    doc_json = json.dumps(tailored_doc or "")
    
    js = f"""(function(){{
        const p = {profile_json};
        const doc = {doc_json};
        
        function fillMatching(selector, val) {{
            const els = document.querySelectorAll(selector);
            els.forEach(el => {{
                if (el && !el.value) {{
                    el.value = val;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    el.style.backgroundColor = '#ecfdf5';
                    el.style.border = '2px solid #10b981';
                }}
            }});
        }}

        const nameParts = (p.full_name || '').split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || '';

        // Name mappings
        fillMatching('input[name*="first" i], input[id*="first" i], input[placeholder*="first name" i]', firstName);
        fillMatching('input[name*="last" i], input[id*="last" i], input[placeholder*="last name" i]', lastName);
        fillMatching('input[name*="full_name" i], input[name*="name" i]:not([name*="first" i]):not([name*="last" i]), input[id*="name" i]:not([id*="first" i]):not([id*="last" i])', p.full_name || '');
        
        // Contacts
        fillMatching('input[type="email"], input[name*="email" i], input[id*="email" i]', p.email || '');
        fillMatching('input[type="tel"], input[name*="phone" i], input[id*="phone" i], input[name*="mobile" i]', p.phone || '');
        fillMatching('input[name*="city" i], input[name*="location" i], input[id*="location" i]', p.location || '');
        fillMatching('input[name*="country" i], input[id*="country" i], select[name*="country" i]', p.nationality || 'Germany');

        // Education & Academics
        fillMatching('input[name*="gpa" i], input[id*="gpa" i], input[placeholder*="gpa" i]', (p.gpa || '3.8').toString());
        fillMatching('input[name*="university" i], input[name*="college" i], input[name*="school" i]', p.bachelor_university || '');
        fillMatching('input[name*="degree" i], input[placeholder*="degree" i]', p.bachelor_degree || '');
        fillMatching('input[name*="grad" i], input[name*="year" i]', (p.graduation_year || 2025).toString());
        fillMatching('input[name*="ielts" i], input[placeholder*="ielts" i]', (p.ielts_score || '7.5').toString());

        // Social Links
        fillMatching('input[name*="linkedin" i], input[placeholder*="linkedin" i]', p.linkedin_url || '');
        fillMatching('input[name*="github" i], input[placeholder*="github" i]', p.github_url || '');
        fillMatching('input[name*="portfolio" i], input[name*="website" i]', p.portfolio_url || '');

        // Textareas (Cover Letter / Motivation / SOP)
        if (doc) {{
            const textareas = document.querySelectorAll('textarea');
            if (textareas.length > 0 && !textareas[0].value) {{
                textareas[0].value = doc;
                textareas[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                textareas[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                textareas[0].style.backgroundColor = '#ecfdf5';
                textareas[0].style.border = '2px solid #10b981';
            }}
        }}

        // Floating HUD confirmation
        const hud = document.createElement('div');
        hud.style.position = 'fixed';
        hud.style.bottom = '24px';
        hud.style.right = '24px';
        hud.style.background = '#1e293b';
        hud.style.color = '#ffffff';
        hud.style.padding = '14px 20px';
        hud.style.borderRadius = '12px';
        hud.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.4)';
        hud.style.zIndex = '999999';
        hud.style.fontFamily = 'system-ui, sans-serif';
        hud.style.fontSize = '14px';
        hud.innerHTML = '✨ <b>ScholarPilot Copilot:</b> Autofill completed! Review each highlighted field and submit when ready.';
        document.body.appendChild(hud);
        setTimeout(() => hud.remove(), 7000);
    }})();"""
    # Clean bookmarklet format
    clean_js = js.replace("\n", " ").replace("  ", " ")
    return f"javascript:{clean_js}"

async def launch_assisted_apply_session(target_url: str, profile: Dict[str, Any], tailored_doc: str = ""):
    """Launches Playwright in headed interactive mode to assist the user in applying."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(viewport=None)
        page = await context.new_page()

        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)  # Wait for hydration
        except Exception:
            pass  # Proceed even if portal takes time to load

        # Inject Smart Assistant
        name_parts = (profile.get("full_name") or "Applicant").split(" ")
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        autofill_script = f"""
        (function() {{
            const p = {json.dumps(profile)};
            const doc = {json.dumps(tailored_doc or "")};
            const fName = {json.dumps(first_name)};
            const lName = {json.dumps(last_name)};

            function fillInputs() {{
                let filled = 0;
                const rules = [
                    {{ keys: ['first', 'fname', 'given'], val: fName }},
                    {{ keys: ['last', 'lname', 'surname', 'family'], val: lName }},
                    {{ keys: ['full_name', 'name'], val: p.full_name }},
                    {{ keys: ['email'], val: p.email }},
                    {{ keys: ['phone', 'mobile', 'tel'], val: p.phone }},
                    {{ keys: ['location', 'city', 'address'], val: p.location }},
                    {{ keys: ['country', 'nationality'], val: p.nationality || 'Germany' }},
                    {{ keys: ['gpa', 'grade'], val: (p.gpa || '3.8').toString() }},
                    {{ keys: ['university', 'college', 'institution'], val: p.bachelor_university }},
                    {{ keys: ['degree', 'major', 'program'], val: p.bachelor_degree }},
                    {{ keys: ['graduation', 'year'], val: (p.graduation_year || 2025).toString() }},
                    {{ keys: ['ielts'], val: (p.ielts_score || '7.5').toString() }},
                    {{ keys: ['linkedin'], val: p.linkedin_url }},
                    {{ keys: ['github'], val: p.github_url }},
                    {{ keys: ['portfolio', 'website'], val: p.portfolio_url }}
                ];

                document.querySelectorAll('input, textarea, select').forEach(el => {{
                    if (el.type === 'hidden' || el.type === 'submit' || el.type === 'button') return;
                    const descriptor = ((el.name || '') + ' ' + (el.id || '') + ' ' + (el.placeholder || '') + ' ' + (el.getAttribute('aria-label') || '')).toLowerCase();

                    for (const rule of rules) {{
                        if (rule.keys.some(k => descriptor.includes(k)) && !el.value && rule.val) {{
                            el.value = rule.val;
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            el.style.backgroundColor = '#ecfdf5';
                            el.style.outline = '2px solid #10b981';
                            filled++;
                            break;
                        }}
                    }}
                }});

                if (doc) {{
                    const textareas = Array.from(document.querySelectorAll('textarea'));
                    const targetArea = textareas.find(t => !t.value && (t.name.toLowerCase().includes('cover') || t.name.toLowerCase().includes('motivat') || t.name.toLowerCase().includes('sop') || t.name.toLowerCase().includes('statement'))) || textareas[0];
                    if (targetArea && !targetArea.value) {{
                        targetArea.value = doc;
                        targetArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        targetArea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        targetArea.style.backgroundColor = '#ecfdf5';
                        targetArea.style.outline = '2px solid #10b981';
                        filled++;
                    }}
                }}
                return filled;
            }}

            const filledCount = fillInputs();

            // Inject floating ScholarPilot Control Bar
            const bar = document.createElement('div');
            bar.id = 'scholarpilot-copilot-bar';
            bar.style.position = 'fixed';
            bar.style.bottom = '20px';
            bar.style.right = '20px';
            bar.style.maxWidth = '420px';
            bar.style.background = '#0f172a';
            bar.style.color = '#ffffff';
            bar.style.padding = '16px 20px';
            bar.style.borderRadius = '16px';
            bar.style.boxShadow = '0 25px 50px -12px rgba(0, 0, 0, 0.5)';
            bar.style.border = '1px solid #3b82f6';
            bar.style.zIndex = '2147483647';
            bar.style.fontFamily = 'Inter, system-ui, sans-serif';
            bar.style.fontSize = '13px';

            bar.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                    <div style="font-weight: 700; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                        <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#10b981;"></span>
                        ScholarPilot Copilot
                    </div>
                    <span style="background:#2563eb; color:#fff; font-size:11px; padding:2px 8px; border-radius:9999px;">Assisted Mode</span>
                </div>
                <div style="margin-bottom: 12px; color: #94a3b8; font-size: 12px; line-height: 1.4;">
                    Detected and populated <b>${{filledCount}} fields</b> with your master profile. Review each section before final submission.
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button id="sp-refill-btn" style="background: #2563eb; color: #fff; border: none; padding: 7px 12px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 12px;">⚡ Re-scan & Fill</button>
                    <button id="sp-copy-sop-btn" style="background: #334155; color: #fff; border: none; padding: 7px 12px; border-radius: 8px; font-weight: 500; cursor: pointer; font-size: 12px;">📋 Copy SOP</button>
                    <button id="sp-close-btn" style="background: transparent; color: #94a3b8; border: 1px solid #475569; padding: 7px 10px; border-radius: 8px; cursor: pointer; font-size: 12px;">Dismiss</button>
                </div>
            `;

            document.body.appendChild(bar);

            document.getElementById('sp-refill-btn').onclick = () => {{
                const c = fillInputs();
                alert('Copilot scanned and filled ' + c + ' form fields.');
            }};

            document.getElementById('sp-copy-sop-btn').onclick = () => {{
                if (doc) {{
                    navigator.clipboard.writeText(doc).then(() => alert('SOP / Motivation text copied to clipboard!'));
                }} else {{
                    alert('No SOP generated yet for this opportunity.');
                }}
            }};

            document.getElementById('sp-close-btn').onclick = () => {{
                bar.remove();
            }};
        }})();
        """

        try:
            await page.evaluate(autofill_script)
        except Exception:
            pass

        # Keep browser open for user interaction
        # It will stay open until user closes the window or 30 minutes pass
        try:
            await page.wait_for_timeout(1800000)
        except Exception:
            pass
        finally:
            await browser.close()

