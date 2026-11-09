import sys
import os
import json
import time
import webbrowser

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_browser(target_url: str, profile_json: str, doc_text: str = ""):
    try:
        profile = json.loads(profile_json) if profile_json else {}
    except Exception:
        profile = {}

    if not target_url or not target_url.startswith("http"):
        target_url = "https://www.google.com"

    print(f"[ScholarPilot Browser] Launching for URL: {target_url}")

    # Try launching Playwright Chromium
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Launch headed browser
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            context = browser.new_context(viewport=None)
            page = context.new_page()

            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
                time.sleep(1.5)
            except Exception as e:
                print(f"[Notice] Page load: {e}")

            # Auto-fill script
            name_parts = (profile.get("full_name") or "Applicant").split(" ")
            f_name = name_parts[0]
            l_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            autofill_js = f"""
            (function() {{
                const p = {json.dumps(profile)};
                const doc = {json.dumps(doc_text or "")};
                const fName = {json.dumps(f_name)};
                const lName = {json.dumps(l_name)};

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
                        {{ keys: ['gpa', 'grade'], val: (p.gpa || '3.5').toString() }},
                        {{ keys: ['university', 'college', 'institution'], val: p.bachelor_university }},
                        {{ keys: ['degree', 'major', 'program'], val: p.bachelor_degree }},
                        {{ keys: ['graduation', 'year'], val: (p.graduation_year || 2025).toString() }},
                        {{ keys: ['ielts'], val: (p.ielts_score || '7.0').toString() }},
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
                        if (textareas.length > 0 && !textareas[0].value) {{
                            textareas[0].value = doc;
                            textareas[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                            textareas[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                            textareas[0].style.backgroundColor = '#ecfdf5';
                            textareas[0].style.outline = '2px solid #10b981';
                            filled++;
                        }}
                    }}
                    return filled;
                }}

                const count = fillInputs();

                // Inject control bar
                const bar = document.createElement('div');
                bar.style.position = 'fixed';
                bar.style.bottom = '20px';
                bar.style.right = '20px';
                bar.style.maxWidth = '380px';
                bar.style.background = '#0f172a';
                bar.style.color = '#ffffff';
                bar.style.padding = '14px 18px';
                bar.style.borderRadius = '14px';
                bar.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.5)';
                bar.style.border = '1px solid #3b82f6';
                bar.style.zIndex = '99999999';
                bar.style.fontFamily = 'system-ui, sans-serif';
                bar.style.fontSize = '12px';

                bar.innerHTML = `
                    <div style="font-weight:700; font-size:13px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981;"></span>
                        ScholarPilot Copilot Active
                    </div>
                    <div style="color:#94a3b8; font-size:11px; margin-bottom:10px;">
                        Populated <b>${{count}} fields</b> with your saved profile (${{p.full_name || 'Applicant'}}).
                    </div>
                    <div style="display:flex; gap:6px;">
                        <button id="sp-btn-re" style="background:#2563eb; color:#fff; border:none; padding:6px 10px; border-radius:6px; cursor:pointer; font-size:11px; font-weight:600;">⚡ Re-Fill</button>
                        <button id="sp-btn-copy" style="background:#334155; color:#fff; border:none; padding:6px 10px; border-radius:6px; cursor:pointer; font-size:11px;">📋 Copy SOP</button>
                        <button id="sp-btn-x" style="background:transparent; color:#94a3b8; border:1px solid #475569; padding:6px 8px; border-radius:6px; cursor:pointer; font-size:11px;">Dismiss</button>
                    </div>
                `;
                document.body.appendChild(bar);

                document.getElementById('sp-btn-re').onclick = () => {{
                    const c = fillInputs();
                    alert('Re-scanned and filled ' + c + ' fields.');
                }};
                document.getElementById('sp-btn-copy').onclick = () => {{
                    if (doc) navigator.clipboard.writeText(doc).then(() => alert('SOP copied!'));
                }};
                document.getElementById('sp-btn-x').onclick = () => bar.remove();
            }})();
            """

            try:
                page.evaluate(autofill_js)
            except Exception:
                pass

            # Keep open for 30 minutes or until closed
            try:
                page.wait_for_timeout(1800000)
            except Exception:
                pass
            finally:
                browser.close()

    except Exception as e:
        print(f"[Playwright fallback]: {e}")
        # Fallback to default browser
        webbrowser.open(target_url)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        u = sys.argv[1]
        p_json = sys.argv[2] if len(sys.argv) > 2 else "{}"
        d_text = sys.argv[3] if len(sys.argv) > 3 else ""
        run_browser(u, p_json, d_text)
    else:
        run_browser("https://www.google.com", "{}")

