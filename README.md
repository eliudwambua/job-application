# 🎓 ScholarPilot EU
### Automatic Master's Scholarship & Study-Job Application Copilot

> **Zero repetitive forms.** Apply for European Master's degree programs, prestigious scholarships (Erasmus Mundus, DAAD, Chevening, Swedish Institute), and student employment (German *Werkstudent* and graduate internships) with tailored Statements of Purpose, optimized CVs, and smart browser auto-fill.

---

## 🌟 Key Features

1. **European Master's Intelligence Catalog:**
   - Pre-loaded with top European scholarships: **Erasmus Mundus Joint Master Degrees (EMJMD)**, **DAAD Helmut-Schmidt & EPOS (Germany)**, **British Chevening (UK)**, **Holland NL Scholarship (Netherlands)**, **Swedish Institute SISGP (Sweden)**, and student employment (*Werkstudent* contracts at Siemens, SAP, ASML).
   - **URL Auto-Extractor:** Paste *any* scholarship link, university portal page, or job announcement, and ScholarPilot automatically extracts the criteria, stipend, and deadlines.

2. **AI-Powered Document Tailoring Studio:**
   - **Statement of Purpose (SOP) / Motivation Letter:** Contextually generated matching your undergraduate background, GPA, and research interests to the specific host university and country.
   - **ATS-Optimized Academic CV:** European standard format emphasizing relevant technical coursework, laboratory achievements, and impact metrics.
   - **Scholarship Essay Answers:** Pre-drafted STAR-method answers for leadership prompts, "Why this program?", and long-term societal contribution.

3. **Smart Assisted Autofill Engine (Human-in-the-Loop):**
   - **Playwright Headed Browser:** Launches Chromium directly to the application portal, detects inputs, pre-fills your personal, academic, and document fields, and floats an in-page control bar so you can review before submitting safely.
   - **Universal 1-Click Bookmarklet:** Drag the bookmarklet into your everyday browser (Chrome, Edge, Firefox, Brave) to autofill application forms on any website in one click.

4. **Cloud Database (Supabase PostgreSQL):**
   - Built to connect directly with **Supabase** cloud database, with an automatic local SQLite fallback so everything works right out of the box.

---

## 🚀 60-Second Quick Start

### 1. Launch the Web Application
Open your terminal in the project directory and run:

```powershell
.\.venv\Scripts\python.exe run.py
```

### 2. Open Your Browser
Go to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*(Interactive API documentation is also available at `http://127.0.0.1:8000/docs`)*

---

## 🗄️ Supabase Cloud Database Setup

ScholarPilot is designed to store your applicant profile, applications pipeline, and documents in your free **Supabase** PostgreSQL database.

### Step 1: Create a Free Project
1. Go to [supabase.com](https://supabase.com) and create a free account.
2. Click **New Project** and name it (e.g. `scholarpilot-db`).

### Step 2: Run the Schema Script
1. In your Supabase project dashboard, navigate to the **SQL Editor** tab on the left.
2. Open the file `supabase_schema.sql` from this repository.
3. Paste its contents into the SQL Editor and click **Run**.
4. This creates the `profiles`, `opportunities`, `applications`, and `tailored_docs` tables with initial seed data.

### Step 3: Connect Credentials in 1 Click
You can connect Supabase in either of two ways:

- **Via the Web UI (Easiest):**
  Click the **"Supabase Setup"** pill in the top navigation bar of ScholarPilot, paste your **Project URL** and **API Key**, and click **Save & Connect**.
- **Via the `.env` file:**
  Edit the `.env` file in the root folder:
  ```env
  SUPABASE_URL=https://your-project-id.supabase.co
  SUPABASE_KEY=your-anon-or-service-role-key
  ```

---

## 💡 How to Use the Application

```
   ┌──────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
   │  1. Profile Vault │ ────> │ 2. Choose Opportunity  │ ────> │ 3. Tailor & Autofill │
   │  (Upload CV PDF) │       │ (Erasmus / DAAD / Job) │       │ (1-Click Playwright) │
   └──────────────────┘       └────────────────────────┘       └──────────────────────┘
```

1. **Step 1: Set Up Your Profile (Vault)**
   - Click **My Profile** in the top navigation bar.
   - Click **"Upload CV (PDF)"** — ScholarPilot will automatically parse your text, extract your email, phone, GPA, graduation year, social links, and technical competencies.
   - Fine-tune your target degree (e.g., M.Sc. in Computer Science) and target European destinations.

2. **Step 2: Browse or Add an Opportunity**
   - Click **Scholarships & Jobs** to explore fully-funded European programs.
   - Each card displays your **Match Score (%)**, funding package, and deadline.
   - You can also paste any custom URL into **"Paste Any Portal Link"** to auto-extract details.

3. **Step 3: AI Copilot Tailoring Studio**
   - Click **"AI Copilot & Tailor"** on any opportunity.
   - Review your customized Statement of Purpose, tailored CV, and scholarship essay answers.
   - You can edit in real-time, copy to clipboard, or download as a text file.

4. **Step 4: Smart Assisted Autofill**
   - In the Copilot Studio, switch to the **Smart Form Copilot** tab.
   - Click **"Launch Browser Copilot"** to open Playwright Chromium. It automatically pre-fills the portal's form fields.
   - Or drag the **"⚡ ScholarPilot Fill"** bookmarklet to your bookmarks bar to autofill inside your personal Chrome/Edge browser.

5. **Step 5: Pipeline Tracker**
   - Track your submissions in the visual Kanban board across stages: *Bookmarked* ➔ *Tailoring* ➔ *Ready to Apply* ➔ *Submitted* ➔ *Interview* ➔ *Offer Awarded*!

---

## 🛠️ Project Structure

```
job application/
├── app/
│   ├── data/                 # Local SQLite fallback storage
│   ├── services/
│   │   ├── ai_tailor.py          # SOP, CV & essay generation algorithms
│   │   ├── pdf_parser.py         # PyPDF extractor for resumes
│   │   ├── playwright_copilot.py # Headed browser & bookmarklet autofill
│   │   └── scholarship_scraper.py# Opportunity link auto-extractor
│   ├── templates/            # Clean, minimalist UI templates
│   │   ├── base.html             # Main layout, nav, Supabase modal
│   │   ├── dashboard.html        # 3-step action wizard & overview
│   │   ├── opportunities.html    # Scholarships & jobs directory
│   │   ├── copilot_studio.html   # Tailoring studio & Playwright launcher
│   │   ├── applications.html     # Kanban pipeline tracker
│   │   └── profile.html          # Profile & CV upload vault
│   ├── database.py           # Database abstraction (Supabase + SQLite)
│   ├── main.py               # FastAPI web server and routes
│   └── supabase_client.py    # Supabase Python SDK client
├── supabase_schema.sql       # Ready-to-run PostgreSQL schema for Supabase
├── run.py                    # One-command application launcher
├── .env.example              # Sample environment configuration
└── README.md                 # Documentation
```

---

## 🔒 Ban-Free & Compliant Guarantee

Most scholarship portals and job sites employ anti-bot measures (CAPTCHA, Cloudflare, single sign-on). ScholarPilot uses a **Smart Assisted Copilot** model:
- The bot assists by filling repetitive fields, but **you** maintain control to inspect every answer and click the final submit button.
- Zero risk of automated rejection, account suspension, or captcha blocking.

---

*Built with Python 3.13, FastAPI, Supabase, Playwright, and Tailwind CSS.*

