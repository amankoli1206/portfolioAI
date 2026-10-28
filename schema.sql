-- PortfolioAI SQLite Normalized Database Schema
-- Master schema for College Assignment / Portfolio Database

-- 1. Personal & Contact Information (Single row profile, id=1)
CREATE TABLE IF NOT EXISTS personal_info (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    location TEXT,
    linkedin_url TEXT,
    github_url TEXT,
    portfolio_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Professional Summary & Career Objective (Single row, id=1)
CREATE TABLE IF NOT EXISTS summary (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    professional_summary TEXT NOT NULL,
    career_objective TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Education
CREATE TABLE IF NOT EXISTS education (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution TEXT NOT NULL,
    degree TEXT NOT NULL,
    field_of_study TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    gpa_or_grade TEXT,
    location TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Technical Skills
CREATE TABLE IF NOT EXISTS technical_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT 'Programming Languages', -- e.g. Languages, Frameworks, Cloud, Databases, Tools
    skill_name TEXT NOT NULL,
    proficiency_level TEXT DEFAULT 'Intermediate', -- Beginner, Intermediate, Advanced, Expert
    years_of_experience REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Soft Skills
CREATE TABLE IF NOT EXISTS soft_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    category TEXT DEFAULT 'Interpersonal', -- Leadership, Communication, Problem Solving
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Certifications & Courses
CREATE TABLE IF NOT EXISTS certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    issuing_organization TEXT NOT NULL,
    issue_date TEXT,
    expiration_date TEXT,
    credential_id TEXT,
    credential_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Projects & Descriptions
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    role TEXT,
    technologies TEXT NOT NULL, -- Comma-separated or tags
    start_date TEXT,
    end_date TEXT,
    github_url TEXT,
    live_url TEXT,
    description TEXT NOT NULL,
    highlights TEXT, -- Bullet points separated by newline
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Internships & Work Experience
CREATE TABLE IF NOT EXISTS experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    employment_type TEXT DEFAULT 'Internship', -- Internship, Full-time, Part-time, Contract
    location TEXT,
    start_date TEXT NOT NULL,
    end_date TEXT,
    is_current INTEGER DEFAULT 0, -- 1 if currently working here
    responsibilities TEXT NOT NULL, -- Bullet points separated by newline
    achievements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Achievements & Awards
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    issuer TEXT NOT NULL,
    date_received TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Research Papers, Publications & Activities
CREATE TABLE IF NOT EXISTS publications_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    activity_type TEXT DEFAULT 'Research Paper', -- Research Paper, Workshop, Hackathon, Open Source, Volunteer
    organization_or_venue TEXT,
    date_or_duration TEXT,
    url TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Languages & Competencies
CREATE TABLE IF NOT EXISTS languages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT NOT NULL,
    proficiency TEXT DEFAULT 'Professional Working', -- Native, Fluent, Professional Working, Conversational, Elementary
    certifications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Generated Resumes History
CREATE TABLE IF NOT EXISTS generated_resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_title TEXT NOT NULL,
    target_role TEXT NOT NULL,
    template_name TEXT DEFAULT 'modern_ats',
    job_description TEXT,
    selected_items_json TEXT, -- JSON containing IDs of selected skills, projects, exp, certs, edu
    customized_summary TEXT,
    pdf_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. Google Sheets Synchronization State & History
CREATE TABLE IF NOT EXISTS sheets_sync_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    spreadsheet_id TEXT,
    spreadsheet_url TEXT,
    last_sync_status TEXT DEFAULT 'Never Synchronized', -- Success, Failed, In Progress, Never Synchronized
    last_sync_message TEXT,
    last_sync_time TIMESTAMP,
    records_synced INTEGER DEFAULT 0
);
