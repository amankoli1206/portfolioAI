# PortfolioAI — AI-Powered Portfolio Database & Dynamic Resume Generator

PortfolioAI is a full-stack web application designed for students and professionals to maintain a single, verified master portfolio in a structured SQLite database, synchronize records with Google Sheets across 10 dedicated category tabs, analyze job descriptions using Google Gemini AI, and generate downloadable, ATS-compliant PDF resumes with ReportLab without hallucinating or inventing any professional qualifications.

---

## Table of Contents

1. [Project Overview & Objectives](#1-project-overview--objectives)
2. [Key Features](#2-key-features)
3. [Technology Stack](#3-technology-stack)
4. [Project Structure](#4-project-structure)
5. [Database Architecture & Schema](#5-database-architecture--schema)
6. [Installation & Setup](#6-installation--setup)
7. [Environment Variables Configuration](#7-environment-variables-configuration)
8. [Google Gemini API Setup](#8-google-gemini-api-setup)
9. [Google Sheets Integration Setup](#9-google-sheets-integration-setup)
10. [Running the Application](#10-running-the-application)
11. [User Workflows](#11-user-workflows)
    - [Portfolio Management](#portfolio-management)
    - [Importing an Existing Resume PDF](#importing-an-existing-resume-pdf)
    - [Job Description Analysis & Matching](#job-description-analysis--matching)
    - [Dynamic ATS Resume Builder](#dynamic-ats-resume-builder)
    - [Google Sheets Export & Synchronization](#google-sheets-export--synchronization)
12. [Two Demonstration Resumes](#12-two-demonstration-resumes)
13. [Testing & Verification Procedure](#13-testing--verification-procedure)
14. [Security & Anti-Hallucination Safeguards](#14-security--anti-hallucination-safeguards)
15. [Troubleshooting](#15-troubleshooting)
16. [College Submission & Video Recording Guide](#16-college-submission--video-recording-guide)

---

## 1. Project Overview & Objectives

Traditional resumes are static, brittle, and time-consuming to customize. Candidates often maintain multiple untracked documents or rely on generative AI tools that hallucinate skills, metrics, and experiences that the candidate never had.

**PortfolioAI solves this problem by:**
- Maintaining **one master truth**: All candidate credentials are stored in a normalized relational SQLite database across 11 major professional categories.
- **Enforcing Anti-Fabrication Safeguards**: All resume bullet points, skills, and projects are strictly ground-checked against verified portfolio records. Unmatched skills are flagged as *Learning Gaps*, never claimed as possessed.
- **Synchronizing with Google Sheets**: Automatically exports and syncs all database tables to 10 structured Google Sheet tabs with stable record IDs.
- **Generating ATS-Friendly PDFs**: Compiles tailored PDF resumes on demand using ReportLab with custom typography and layouts.

---

## 2. Key Features

- **11 Master Portfolio Categories**:
  1. Personal & Contact Information
  2. Professional Summary & Career Objective
  3. Education & Academic Coursework
  4. Technical Skills (categorized with proficiency & experience)
  5. Soft Skills & Leadership Competencies
  6. Professional Certifications & Licenses
  7. Technical & Applied Engineering Projects
  8. Internships & Work Experience
  9. Honors, Awards & Hackathon Achievements
  10. Publications, Research Papers & Student Activities
  11. Languages & Spoken Proficiencies
- **Resume PDF Text Extraction**: Extracts text with `pypdf`, extracts structured JSON using Gemini 2.5 Flash, and provides an editable human review screen with approve/reject controls.
- **Job Description Analyzer**: Extracts required skills, preferred qualifications, responsibilities, and compares them against verified records to compute an ATS match score.
- **Customizable ATS Templates**: Supports 3 distinct layout designs:
  - `modern_ats`: Professional navy blue accents, clean dividing rules.
  - `classic_executive`: Timeless monochrome charcoal, centered header.
  - `minimal_tech`: Modern teal highlights, compact spacing.
- **Google Sheets Two-Way Synchronization**: Exports structured records to 10 tabs, tracks sync timestamp and status, and preserves record IDs.
- **Pre-Configured Demos**: Generates two distinct resumes from the same master portfolio:
  - *Resume A:* Frontend Developer Internship
  - *Resume B:* AI / Machine Learning Engineering Internship

---

## 3. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript | Modern, minimal charcoal sidebar & light-gray UI |
| **Backend** | Python 3.14, Flask 3.1 | Modular RESTful API and web application server |
| **Database** | SQLite3 (`instance/portfolio.db`) | Normalized local relational database |
| **AI Integration** | `google-genai` Python SDK | Official SDK for Gemini 2.5 Flash |
| **PDF Generation** | ReportLab 5.1 | Precision typographic PDF generation for ATS |
| **PDF Extraction** | `pypdf` 6.2 | Text extraction from candidate resume PDFs |
| **Spreadsheets** | `gspread` 6.2, `google-auth` | Automated Google Sheets API synchronization |
| **Configuration** | `python-dotenv` | Secure environment variable management |
| **Testing** | `pytest` 9.2 | Automated unit and integration test suite |

---

## 4. Project Structure

```text
portfolio Database/
├── app.py                     # Main Flask web application & routing
├── database.py                # SQLite schema management & CRUD helpers
├── gemini_service.py          # Google Gen AI SDK integration & guardrails
├── resume_generator.py        # ReportLab ATS PDF resume generation engine
├── sheets.py                  # Google Sheets API export & sync manager
├── schema.sql                 # Normalized SQLite database schema
├── requirements.txt           # Python dependency definitions
├── conftest.py                # Pytest configuration
├── .env                       # Local environment variables (gitignored)
├── .env.example               # Template environment configuration
├── .gitignore                 # Protected files and secrets
├── README.md                  # Comprehensive documentation
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Base shell with sidebar & navigation
│   ├── index.html             # Dashboard with stats, profile & sync card
│   ├── portfolio.html         # Master portfolio CRUD for 11 categories
│   ├── import_resume.html     # PDF upload & interactive review screen
│   ├── job_analyzer.html      # Job analyzer & skill gap detector
│   ├── resume_builder.html    # Interactive resume builder & PDF generator
│   ├── sheets.html            # Google Sheets sync status & setup guide
│   └── resumes_list.html      # Generated resumes archive & download links
├── static/                    # Frontend styling & JavaScript
│   ├── style.css              # Custom design system (dark sidebar, light content)
│   └── script.js              # Modals, tabs, and client-side interactions
├── instance/                  # SQLite runtime directory
│   └── portfolio.db           # Persistent SQLite database file
├── uploads/                   # Uploaded candidate PDF resumes
├── generated_resumes/         # Compiled downloadable ReportLab PDFs
└── tests/                     # Automated test suite
    └── test_portfolio_ai.py   # Pytest integration & unit test suite
```

---

## 5. Database Architecture & Schema

The database uses a normalized SQLite design with foreign keys, timestamps, and separate tables for every category. Defined in `schema.sql`:

1. `personal_info`: Single-row master profile (`id=1`) with name, email, phone, location, LinkedIn, GitHub, and portfolio URL.
2. `summary`: Career objective and professional summary (`id=1`).
3. `education`: Degree, institution, field of study, dates, GPA, location, coursework.
4. `technical_skills`: Categorized skill records (`category`, `skill_name`, `proficiency_level`, `years_of_experience`).
5. `soft_skills`: Interpersonal and leadership skills with descriptions.
6. `certifications`: Professional licenses, issuers, dates, and credential IDs.
7. `projects`: Software engineering projects with title, role, tech stack, links, and bullet points.
8. `experience`: Internships and jobs with company, role, type, dates, responsibilities, and achievements.
9. `achievements`: Collegiate honors, hackathons, and awards.
10. `publications_activities`: Research papers, symposiums, student club leadership, open source.
11. `languages`: Spoken languages with proficiency levels and certifications.
12. `generated_resumes`: Archive of all compiled resumes, timestamps, and parameters.
13. `sheets_sync_state`: Metadata on spreadsheet URL, ID, records count, and sync status.

---

## 6. Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git

### Step-by-Step Setup

1. **Clone or navigate into the project directory**:
   ```bash
   cd "/Users/amankoli/Documents/portfolio Database"
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install all required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the SQLite database with sample records**:
   ```bash
   python database.py
   ```
   *(This creates `instance/portfolio.db` and seeds sample student records for instant testing).*

---

## 7. Environment Variables Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Contents of `.env`:
```ini
# Flask Web Server
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=portfolio-ai-secret-key-college-demo
PORT=5001

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Google Sheets Integration
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
SPREADSHEET_ID=
```

---

## 8. Google Gemini API Setup

1. Visit [Google AI Studio](https://aistudio.google.com/) and create an API key.
2. Open your local `.env` file and set:
   ```ini
   GEMINI_API_KEY=AIzaSy...your_actual_key
   GEMINI_MODEL=gemini-2.5-flash
   ```
3. *Fallback Safeguard:* If the Gemini API key is missing or invalid, PortfolioAI will automatically fall back to deterministic ATS keyword extraction and notify the user with a helpful alert banner without crashing.

---

## 9. Google Sheets Integration Setup

PortfolioAI connects to the Google Sheets API using a Google Service Account:

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Google Cloud project (e.g. `PortfolioAI-Demo`).
3. In **APIs & Services > Library**, enable:
   - **Google Sheets API**
   - **Google Drive API**
4. In **IAM & Admin > Service Accounts**, click **Create Service Account**:
   - Name: `portfolioai-sync`
   - Role: `Editor` or `Owner`
5. Go to the newly created service account > **Keys** tab > **Add Key** > **Create new key** > Select **JSON**.
6. Save the downloaded JSON file into the project root directory as:
   ```text
   service_account.json
   ```
7. *(Optional)* If you want to sync to a specific existing Google Sheet, add its ID from the URL (`https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`) to `.env`:
   ```ini
   SPREADSHEET_ID=your_sheet_id_here
   ```
   and share that spreadsheet with your service account's `client_email` with **Editor** permissions.
8. If `SPREADSHEET_ID` is left empty, PortfolioAI will automatically create a brand new Google Sheet named **PortfolioAI Master Database - [Candidate Name]** on your first sync.

---

## 10. Running the Application

Activate the virtual environment and start the Flask development server:
```bash
source venv/bin/activate
python app.py
```

The application will start on:
👉 **`http://127.0.0.1:5001/`**

---

## 11. User Workflows

### Portfolio Management
1. Click **My Portfolio** in the sidebar.
2. Navigate between the 11 tabs (Personal Info, Summary, Technical Skills, Projects, Experience, Education, Certifications, Soft Skills, Achievements, Publications, Languages).
3. Click **+ Add Item** to open a modal form with input validation.
4. Delete records with the confirmation prompt.

### Importing an Existing Resume PDF
1. Click **Import Resume PDF** in the sidebar.
2. Choose a text-based PDF file (up to 16MB).
3. `pypdf` extracts the raw text and passes it to Gemini 2.5 Flash.
4. **Editable Verification Screen**: All extracted items appear in an editable review screen with checkboxes. Inspect and edit details.
5. Click **✓ Approve & Save Verified Records to Database** to commit to SQLite.

### Job Description Analysis & Matching
1. Click **Job Description Analyzer** in the sidebar.
2. Paste any job posting or click **Load Frontend Sample** / **Load AI/ML Sample**.
3. Click **Analyze Job & Match Portfolio**.
4. Review:
   - **Match Score % Meter**
   - **Verified Matched Skills** (skills you possess)
   - **Learning Gaps** (skills requested in the job but missing from your portfolio — never claimed on your resume)
   - **Recommended Projects** ranked by tech stack relevance.

### Dynamic ATS Resume Builder
1. Click **Resume Builder** in the sidebar.
2. Enter the target job role and paste the job description (or select Frontend / AI/ML presets).
3. Click **Match Portfolio & Suggest Tailored Summary** (Gemini crafts a tailored summary grounded exclusively in verified facts).
4. Select or deselect skills, projects, experience, and certifications using the checkboxes.
5. Choose one of the 3 templates: `Modern ATS`, `Classic Executive`, or `Minimal Tech`.
6. Preview the layout in the **Live Resume Content Preview** panel.
7. Click **⚡ Generate & Download PDF Resume** to compile and download via ReportLab.

### Google Sheets Export & Synchronization
1. Click **Google Sheets Sync** in the sidebar.
2. Click **🔄 Synchronize Portfolio Now**.
3. PortfolioAI creates or opens the Google Spreadsheet, updates 10 worksheet tabs with column headers and stable record IDs, and logs the sync timestamp.
4. Click the spreadsheet link to view the synchronized data in your browser.

---

## 12. Two Demonstration Resumes

PortfolioAI is pre-configured to generate two tailored resumes from the same candidate portfolio:

### Resume A: Frontend Developer Internship
- **Focus**: React.js, TypeScript, Tailwind CSS, Next.js, Redux Toolkit, Web Accessibility.
- **Projects**: CloudPulse DevOps Dashboard, DevMarket E-Commerce Component Library.
- **Experience**: Frontend Software Engineering Intern at TechForward Solutions.
- **Template**: `modern_ats` (Navy Blue).
- **Download**: Saved as `generated_resumes/Demo_Resume_A_Frontend_Developer_Internship.pdf`.

### Resume B: AI / Machine Learning Internship
- **Focus**: Python, PyTorch, Scikit-learn, Google Gemini API / LLMs, FAISS, Docker, FastAPI.
- **Projects**: VisionMed Biomedical Image Classification, DocuSense Multi-Document RAG Agent.
- **Experience**: Undergraduate Research Assistant in University AI & Vision Lab.
- **Template**: `minimal_tech` (Deep Teal).
- **Download**: Saved as `generated_resumes/Demo_Resume_B_AIML_Internship.pdf`.

You can regenerate both resumes with 1 click from the Dashboard or by visiting:
👉 `http://127.0.0.1:5001/sample-resumes/generate-defaults`

---

## 13. Testing & Verification Procedure

Run the automated test suite with `pytest`:
```bash
./venv/bin/pytest tests/test_portfolio_ai.py -v
```

### Test Cases Covered:
1. `test_database_initialization_and_seeding`: Verifies table creation and default seed data.
2. `test_portfolio_crud_operations`: Tests adding, reading, updating, and deleting records.
3. `test_database_persistence`: Verifies data persists across connection close and application restarts.
4. `test_gemini_missing_credentials_graceful_handling`: Verifies system degrades gracefully with fallback parsing when API keys are absent.
5. `test_job_description_analysis_and_safeguards`: Verifies job keyword extraction, match scoring, and learning gap segregation.
6. `test_reportlab_pdf_generation_and_anti_fabrication`: Verifies ReportLab compiles valid PDFs and extracts text with `pypdf` to prove unselected skills are omitted.
7. `test_two_customized_resume_demonstrations`: Verifies generation and role-specific contents of Resume A and Resume B.
8. `test_secure_download_route`: Verifies path traversal attacks (`../../`) are blocked.
9. `test_google_sheets_graceful_missing_credentials`: Verifies Sheets integration returns clear instructions when credentials file is missing.
10. `test_resume_pdf_text_extraction_and_import`: Verifies `pypdf` text extraction from an uploaded PDF and presentation in the review screen.

---

## 14. Security & Anti-Hallucination Safeguards

- **API Keys & Secrets**: Stored exclusively in `.env`, which is included in `.gitignore`. Never exposed in frontend client scripts or API responses.
- **Path Traversal Protection**: Resume download routes use Werkzeug's `secure_filename()` to ensure only valid filenames inside `generated_resumes/` are served.
- **SQL Injection Prevention**: Safe parameterized SQLite queries (`?` and `:named_params`) are used throughout `database.py`.
- **Anti-Fabrication Guarantee**: Missing job skills are explicitly flagged as **Learning Gaps** and are never added to the candidate's resume. AI summary tailoring is strictly bounded by verified facts.

---

## 15. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `GEMINI_API_KEY is not configured` | API key missing in `.env` | Add key to `.env`. Application will use local deterministic keyword matcher until key is added. |
| `Service account key file not found` | Google credentials JSON missing | Place `service_account.json` in project root following Section 9 instructions. |
| `No extractable text found in PDF` | Scanned PDF or image-only file | Upload a text-based PDF resume (created in Word, Google Docs, or LaTeX). |
| Port 5001 already in use | Another application is using port 5001 | Change `PORT=5002` in `.env` and restart `python app.py`. |

---

## 16. College Submission & Video Recording Guide

### Recommended Demo Video Flow (3–5 minutes):
1. **Introduction (30s)**: Show the Dashboard at `http://127.0.0.1:5001/`, explain the single source of truth architecture, and review the 11 database categories.
2. **Portfolio CRUD (45s)**: Navigate to **My Portfolio**, show technical skills, add a new record, and delete a test record.
3. **Resume Import (60s)**: Upload an existing resume PDF, demonstrate text extraction with `pypdf`, review the editable verification screen, and explain the anti-hallucination safeguard.
4. **Job Analysis & Skill Gaps (45s)**: Load the Frontend sample job description, show the ATS match score, verified matched skills, and learning gaps.
5. **Resume Generation (60s)**: Open **Resume Builder**, show dynamic selection of items, template switching (Modern ATS vs Minimal Tech), live preview, and download the compiled ReportLab PDF.
6. **Two Customized Resumes (30s)**: Display the downloaded `Resume A (Frontend)` and `Resume B (AI/ML)` side-by-side to prove dynamic tailoring without fabrication.
7. **Google Sheets Sync (30s)**: Show the Google Sheets Sync dashboard, explain the 10-tab export schema, and demonstrate synchronization.
