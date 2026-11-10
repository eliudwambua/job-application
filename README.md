# 🎓 ScholarPilot EU
### Automatic Master's Scholarship, European & Kenya Job Application Copilot

> **Zero repetitive forms.** Apply for prestigious European Master's programs (**Erasmus Mundus**, **DAAD Germany**, **British Chevening**, **Swedish Institute**, **Holland Scholarship**), European student employment (**Werkstudent** contracts & graduate internships), and top tech jobs in **Kenya** (**Safaricom**, **Microsoft ADC**, **Equity Bank**, **KCB**, **UN UNEP**) with tailored Statements of Purpose, CVs, and smart browser auto-fill.

---

## 🎨 Theme Toggling (Light & Dark Mode)

ScholarPilot features an instant theme toggler in the top navigation bar:
- **☀️ Light Theme:** Crisp white background with fresh **emerald green** (`#059669`) and **sky / light blue** (`#0284c7`, `#38bdf8`) accents, clean slate typography, and subtle card elevation.
- **🌙 Dark Theme:** Pitch **black** (`#050811`, `#070c18`) canvas with **deep navy** (`#0c1322`) surfaces and vibrant **electric blue** (`#3b82f6`, `#60a5fa`) highlights.
- **Persistent:** Your theme preference is saved in `localStorage` so it persists across page reloads and browser sessions with zero flash of unstyled content.

---

## 🧭 Navigation & System Layout

ScholarPilot features dedicated pages to make finding and applying effortless:

| Tab / Section | URL | Purpose & What You'll Find |
| :--- | :--- | :--- |
| **🏠 Dashboard** | `http://127.0.0.1:8000/` | 3-step action wizard, quick stats, quick category filters (All, Scholarships, Jobs, Kenya), and upcoming deadlines. |
| **🎓 Scholarships** | `http://127.0.0.1:8000/scholarships` | **Dedicated scholarships directory**: Fully funded European Master's degrees, Erasmus Mundus consortia, DAAD grants, stipends, and deadlines. |
| **💼 Jobs & Internships** | `http://127.0.0.1:8000/jobs` | **Dedicated European student employment directory**: German *Werkstudent* positions (up to 20 hrs/week at €16–€25/hr at Siemens, SAP, ASML), and graduate internships. |
| **🇰🇪 Kenya Jobs** | `http://127.0.0.1:8000/kenya-jobs` | **Dedicated Kenya tech careers directory**: Software Engineering, Business IT, and Data Analytics at Safaricom, Microsoft ADC, Equity Bank, KCB, and UNEP with **Confirm & Auto-Apply**. |
| **📋 Tracker** | `http://127.0.0.1:8000/applications` | Visual Kanban board tracking every submission: *Bookmarked* ➔ *Tailoring* ➔ *Ready to Apply* ➔ *Submitted* ➔ *Interview* ➔ *Awarded*! |
| **👤 My Profile (Vault)** | `http://127.0.0.1:8000/profile` | Upload your CV (PDF) to auto-extract details, manage academic metrics (GPA, IELTS/TOEFL), target field, and career history. |
| **⚡ Copilot Studio** | `http://127.0.0.1:8000/copilot/{id}` | AI Tailoring workspace for any program: live editable Statement of Purpose (SOP), ATS-optimized academic CV, scholarship essays, and auto-fill launcher. |

---

## 🚀 How to Run the Application

### Option A: 1-Click Launch (Recommended for Windows)
Simply double-click the **`start.bat`** file in this folder:
```
job application/start.bat
```
This automatically starts the server and opens your web browser to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

### Option B: Terminal Command
Open PowerShell or Command Prompt in the project folder and run:

```powershell
.\.venv\Scripts\python.exe run.py
```

Then open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

*(Interactive API docs are always available at `http://127.0.0.1:8000/docs`)*

---

## 📖 Step-by-Step User Workflow

```
   ┌───────────────────────┐       ┌────────────────────────┐       ┌──────────────────────┐
   │  1. Profile Vault     │ ────> │ 2. Pick Program / URL  │ ────> │ 3. Tailor & Autofill │
   │  (Upload Resume PDF)  │       │ (Scholarship or Job)   │       │ (Playwright Copilot) │
   └───────────────────────┘       └────────────────────────┘       └──────────────────────┘
```

### Step 1: Set Up Your Profile (Takes 1 Minute)
1. In the top navigation bar, click **My Profile** (shows your name and GPA).
2. Click **"Upload CV (PDF)"** — ScholarPilot uses PyPDF to automatically extract your full name, email, phone number, LinkedIn, GitHub, GPA, graduation year, and technical skills.
3. Verify or edit your details (GPA scale, target degree, target countries) and click **"Save & Update Master Profile"**.

### Step 2: Browse Scholarships vs. Jobs
- **Looking for funded Master's studies?** Click **"Scholarships"** in the top navigation. Explore programs like Erasmus Mundus EMAI, DAAD EPOS, or British Chevening. Every card shows your calculated **% Match** based on your GPA and field.
- **Looking for student employment abroad?** Click **"Jobs & Internships"** in the top navigation. Explore working student contracts in Germany (up to 20 hrs/week) that allow you to earn €1,400–€1,800/month while studying.
- **Looking for opportunities in Kenya?** Click **"🇰🇪 Kenya Jobs"** in the top navigation. Explore roles at Safaricom, Microsoft ADC, Equity, KCB, and UNEP.
- **Found a link elsewhere?** Click **"Paste Any Portal Link"** on the Dashboard. ScholarPilot will scrape the webpage, extract the criteria, and add it for you.

### Step 3: Use the AI Copilot Tailoring Studio
Click **"AI Copilot & Tailor"** on any scholarship or job:
1. **Statement of Purpose (SOP):** Generates a comprehensive, persuasive motivation letter explicitly referencing your background, your GPA, and why you are applying to that specific consortium or university.
2. **ATS-Optimized Academic CV:** Generates a structured European academic resume emphasizing relevant coursework and technical impact.
3. **Scholarship Essays:** Provides pre-drafted STAR-method answers for leadership questions, career vision, and overcoming financial barriers.
4. **PDF / Print Button:** Click **"PDF / Print"** on any document to open a publication-quality letterhead formatted for A4 printing or saving directly to PDF!
5. **🔄 Re-tailor with My Profile:** If you edit your profile details at any point, click this button to instantly re-synthesize your documents with your latest information!

### Step 4: 1-Click Auto-Apply & Browser Launch
- Click **"Confirm & Auto-Apply"** on any job card. ScholarPilot prepares your tailored documents, moves the application to the "Applied" stage in your Tracker, and opens the company's portal in your default browser.
- You review the auto-populated details and click the final submission button safely.

---

## 🗄️ Supabase Cloud Database & Data Migration

ScholarPilot supports syncing your applicant profile, applications, and documents directly to **Supabase** cloud PostgreSQL with automatic offline SQLite fallback.

### 1. Database Schema Setup:
1. Open the file [`supabase_schema.sql`](file:///d:/desktop/job%20application/supabase_schema.sql) in this directory.
2. Copy its contents, go to your Supabase project dashboard -> **SQL Editor**, paste and click **Run**.
3. (Optional) Run the migration script to push all existing SQLite rows to Supabase:
   ```powershell
   .\.venv\Scripts\python.exe migrate_to_supabase.py
   ```

---

## 🛡️ Anti-Bot & Ban-Free Guarantee

Most European university portals and job boards (e.g. Siemens, SAP, university application systems) use anti-bot systems (Cloudflare, CAPTCHA, SSO). 

ScholarPilot follows a **Smart Assisted Copilot** model:
- The bot handles the repetitive typing (names, addresses, education history, transcript details, essay answers).
- **You** retain 100% human-in-the-loop oversight to review the filled fields and click the final submit button.
- Zero risk of automated account bans or bot rejections.

---

## 📁 Project Architecture

```
job application/
├── app/
│   ├── data/                 # Local SQLite persistent storage
│   ├── services/
│   │   ├── ai_tailor.py          # SOP, CV & essay generation algorithms
│   │   ├── browser_runner.py     # Independent browser launcher
│   │   ├── pdf_parser.py         # PyPDF extractor for resumes
│   │   ├── playwright_copilot.py # Headed browser & bookmarklet autofill
│   │   └── scholarship_scraper.py# Portal link auto-extractor
│   ├── templates/            # Clean, minimalist UI templates
│   │   ├── base.html             # Top navigation, theme toggle & Supabase modal
│   │   ├── dashboard.html        # 3-step action wizard & opportunity cards
│   │   ├── scholarships.html     # Dedicated European Master's Scholarships directory
│   │   ├── jobs.html             # Dedicated Student Jobs & Internships directory
│   │   ├── kenya_jobs.html       # Dedicated Kenya Jobs directory with Auto-Apply
│   │   ├── copilot_studio.html   # Tailoring studio & Playwright launcher
│   │   ├── print_doc.html        # Publication-grade print & PDF layout
│   │   ├── applications.html     # Kanban pipeline tracker
│   │   └── profile.html          # Profile & CV upload vault
│   ├── database.py           # Database adapter (Supabase + Local SQLite)
│   ├── main.py               # FastAPI web server and endpoints
│   └── supabase_client.py    # Supabase Python SDK client
├── migrate_to_supabase.py    # Data migration script to Supabase
├── supabase_schema.sql       # PostgreSQL schema script for Supabase
├── start.bat                 # 1-Click desktop launcher for Windows
├── run.py                    # Terminal server runner
├── .env                      # Supabase credentials configuration
└── README.md                 # Complete documentation
```

---

*Built for ambitious scholars targeting European Master's degrees and global tech careers.*
