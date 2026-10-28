import os
import sqlite3
from datetime import datetime

DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'portfolio.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

def get_db():
    """Get a SQLite database connection with row factory enabled."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initialize database tables using schema.sql and seed sample data if empty."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    with get_db() as conn:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        
        # Initialize sync state row if absent
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sheets_sync_state WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO sheets_sync_state (id, last_sync_status, last_sync_message) VALUES (1, 'Never Synchronized', 'No export has been performed yet.')"
            )
        conn.commit()

    # Seed initial data if personal info doesn't exist
    seed_sample_data(force=False)

def dict_from_row(row):
    """Convert sqlite3.Row to standard Python dictionary."""
    if row is None:
        return None
    return dict(row)

def dict_list_from_rows(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]

# ==================== PERSONAL INFO ====================
def get_personal_info():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM personal_info WHERE id = 1").fetchone()
        return dict_from_row(row)

def save_personal_info(data):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO personal_info (id, full_name, email, phone, location, linkedin_url, github_url, portfolio_url, updated_at)
            VALUES (1, :full_name, :email, :phone, :location, :linkedin_url, :github_url, :portfolio_url, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                full_name = :full_name,
                email = :email,
                phone = :phone,
                location = :location,
                linkedin_url = :linkedin_url,
                github_url = :github_url,
                portfolio_url = :portfolio_url,
                updated_at = CURRENT_TIMESTAMP
        """, {
            "full_name": data.get("full_name", "").strip(),
            "email": data.get("email", "").strip(),
            "phone": data.get("phone", "").strip(),
            "location": data.get("location", "").strip(),
            "linkedin_url": data.get("linkedin_url", "").strip(),
            "github_url": data.get("github_url", "").strip(),
            "portfolio_url": data.get("portfolio_url", "").strip()
        })
        conn.commit()

# ==================== SUMMARY & OBJECTIVE ====================
def get_summary():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM summary WHERE id = 1").fetchone()
        return dict_from_row(row)

def save_summary(data):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO summary (id, professional_summary, career_objective, updated_at)
            VALUES (1, :professional_summary, :career_objective, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                professional_summary = :professional_summary,
                career_objective = :career_objective,
                updated_at = CURRENT_TIMESTAMP
        """, {
            "professional_summary": data.get("professional_summary", "").strip(),
            "career_objective": data.get("career_objective", "").strip()
        })
        conn.commit()

# ==================== EDUCATION ====================
def get_education(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM education WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM education ORDER BY end_date DESC, id DESC").fetchall()
        return dict_list_from_rows(rows)

def add_education(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO education (institution, degree, field_of_study, start_date, end_date, gpa_or_grade, location, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("institution", "").strip(),
            data.get("degree", "").strip(),
            data.get("field_of_study", "").strip(),
            data.get("start_date", "").strip(),
            data.get("end_date", "").strip(),
            data.get("gpa_or_grade", "").strip(),
            data.get("location", "").strip(),
            data.get("description", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_education(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE education SET
                institution = ?, degree = ?, field_of_study = ?,
                start_date = ?, end_date = ?, gpa_or_grade = ?,
                location = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("institution", "").strip(),
            data.get("degree", "").strip(),
            data.get("field_of_study", "").strip(),
            data.get("start_date", "").strip(),
            data.get("end_date", "").strip(),
            data.get("gpa_or_grade", "").strip(),
            data.get("location", "").strip(),
            data.get("description", "").strip(),
            item_id
        ))
        conn.commit()

def delete_education(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM education WHERE id = ?", (item_id,))
        conn.commit()

# ==================== TECHNICAL SKILLS ====================
def get_technical_skills(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM technical_skills WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM technical_skills ORDER BY category ASC, skill_name ASC").fetchall()
        return dict_list_from_rows(rows)

def add_technical_skill(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO technical_skills (category, skill_name, proficiency_level, years_of_experience)
            VALUES (?, ?, ?, ?)
        """, (
            data.get("category", "General").strip(),
            data.get("skill_name", "").strip(),
            data.get("proficiency_level", "Intermediate").strip(),
            float(data.get("years_of_experience", 1.0) or 1.0)
        ))
        conn.commit()
        return cursor.lastrowid

def update_technical_skill(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE technical_skills SET
                category = ?, skill_name = ?, proficiency_level = ?,
                years_of_experience = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("category", "General").strip(),
            data.get("skill_name", "").strip(),
            data.get("proficiency_level", "Intermediate").strip(),
            float(data.get("years_of_experience", 1.0) or 1.0),
            item_id
        ))
        conn.commit()

def delete_technical_skill(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM technical_skills WHERE id = ?", (item_id,))
        conn.commit()

# ==================== SOFT SKILLS ====================
def get_soft_skills(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM soft_skills WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM soft_skills ORDER BY category ASC, skill_name ASC").fetchall()
        return dict_list_from_rows(rows)

def add_soft_skill(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO soft_skills (skill_name, category, description)
            VALUES (?, ?, ?)
        """, (
            data.get("skill_name", "").strip(),
            data.get("category", "Interpersonal").strip(),
            data.get("description", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_soft_skill(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE soft_skills SET
                skill_name = ?, category = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("skill_name", "").strip(),
            data.get("category", "Interpersonal").strip(),
            data.get("description", "").strip(),
            item_id
        ))
        conn.commit()

def delete_soft_skill(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM soft_skills WHERE id = ?", (item_id,))
        conn.commit()

# ==================== CERTIFICATIONS ====================
def get_certifications(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM certifications WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM certifications ORDER BY issue_date DESC, id DESC").fetchall()
        return dict_list_from_rows(rows)

def add_certification(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO certifications (title, issuing_organization, issue_date, expiration_date, credential_id, credential_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("title", "").strip(),
            data.get("issuing_organization", "").strip(),
            data.get("issue_date", "").strip(),
            data.get("expiration_date", "").strip(),
            data.get("credential_id", "").strip(),
            data.get("credential_url", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_certification(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE certifications SET
                title = ?, issuing_organization = ?, issue_date = ?,
                expiration_date = ?, credential_id = ?, credential_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("title", "").strip(),
            data.get("issuing_organization", "").strip(),
            data.get("issue_date", "").strip(),
            data.get("expiration_date", "").strip(),
            data.get("credential_id", "").strip(),
            data.get("credential_url", "").strip(),
            item_id
        ))
        conn.commit()

def delete_certification(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM certifications WHERE id = ?", (item_id,))
        conn.commit()

# ==================== PROJECTS ====================
def get_projects(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        return dict_list_from_rows(rows)

def add_project(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO projects (title, role, technologies, start_date, end_date, github_url, live_url, description, highlights)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("title", "").strip(),
            data.get("role", "").strip(),
            data.get("technologies", "").strip(),
            data.get("start_date", "").strip(),
            data.get("end_date", "").strip(),
            data.get("github_url", "").strip(),
            data.get("live_url", "").strip(),
            data.get("description", "").strip(),
            data.get("highlights", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_project(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE projects SET
                title = ?, role = ?, technologies = ?,
                start_date = ?, end_date = ?, github_url = ?,
                live_url = ?, description = ?, highlights = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("title", "").strip(),
            data.get("role", "").strip(),
            data.get("technologies", "").strip(),
            data.get("start_date", "").strip(),
            data.get("end_date", "").strip(),
            data.get("github_url", "").strip(),
            data.get("live_url", "").strip(),
            data.get("description", "").strip(),
            data.get("highlights", "").strip(),
            item_id
        ))
        conn.commit()

def delete_project(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (item_id,))
        conn.commit()

# ==================== EXPERIENCE ====================
def get_experience(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM experience WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM experience ORDER BY start_date DESC, id DESC").fetchall()
        return dict_list_from_rows(rows)

def add_experience(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO experience (job_title, company_name, employment_type, location, start_date, end_date, is_current, responsibilities, achievements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("job_title", "").strip(),
            data.get("company_name", "").strip(),
            data.get("employment_type", "Internship").strip(),
            data.get("location", "").strip(),
            data.get("start_date", "").strip(),
            data.get("end_date", "").strip(),
            1 if data.get("is_current") in (True, 1, '1', 'true', 'on') else 0,
            data.get("responsibilities", "").strip(),
            data.get("achievements", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_experience(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE experience SET
                job_title = ?, company_name = ?, employment_type = ?,
                location = ?, start_date = ?, end_date = ?, is_current = ?,
                responsibilities = ?, achievements = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("job_title", "").strip(),
            data.get("company_name", "").strip(),
            data.get("employment_type", "Internship").strip(),
            data.get("location", "").strip(),
            data.get("start_date", "").strip(),
            data.get("end_date", "").strip(),
            1 if data.get("is_current") in (True, 1, '1', 'true', 'on') else 0,
            data.get("responsibilities", "").strip(),
            data.get("achievements", "").strip(),
            item_id
        ))
        conn.commit()

def delete_experience(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM experience WHERE id = ?", (item_id,))
        conn.commit()

# ==================== ACHIEVEMENTS ====================
def get_achievements(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM achievements WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM achievements ORDER BY id DESC").fetchall()
        return dict_list_from_rows(rows)

def add_achievement(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO achievements (title, issuer, date_received, description)
            VALUES (?, ?, ?, ?)
        """, (
            data.get("title", "").strip(),
            data.get("issuer", "").strip(),
            data.get("date_received", "").strip(),
            data.get("description", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_achievement(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE achievements SET
                title = ?, issuer = ?, date_received = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("title", "").strip(),
            data.get("issuer", "").strip(),
            data.get("date_received", "").strip(),
            data.get("description", "").strip(),
            item_id
        ))
        conn.commit()

def delete_achievement(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM achievements WHERE id = ?", (item_id,))
        conn.commit()

# ==================== PUBLICATIONS & ACTIVITIES ====================
def get_publications_activities(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM publications_activities WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM publications_activities ORDER BY id DESC").fetchall()
        return dict_list_from_rows(rows)

def add_publication_activity(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO publications_activities (title, activity_type, organization_or_venue, date_or_duration, url, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get("title", "").strip(),
            data.get("activity_type", "Research Paper").strip(),
            data.get("organization_or_venue", "").strip(),
            data.get("date_or_duration", "").strip(),
            data.get("url", "").strip(),
            data.get("description", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_publication_activity(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE publications_activities SET
                title = ?, activity_type = ?, organization_or_venue = ?,
                date_or_duration = ?, url = ?, description = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("title", "").strip(),
            data.get("activity_type", "Research Paper").strip(),
            data.get("organization_or_venue", "").strip(),
            data.get("date_or_duration", "").strip(),
            data.get("url", "").strip(),
            data.get("description", "").strip(),
            item_id
        ))
        conn.commit()

def delete_publication_activity(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM publications_activities WHERE id = ?", (item_id,))
        conn.commit()

# ==================== LANGUAGES ====================
def get_languages(item_id=None):
    with get_db() as conn:
        if item_id:
            row = conn.execute("SELECT * FROM languages WHERE id = ?", (item_id,)).fetchone()
            return dict_from_row(row)
        rows = conn.execute("SELECT * FROM languages ORDER BY id ASC").fetchall()
        return dict_list_from_rows(rows)

def add_language(data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO languages (language_name, proficiency, certifications)
            VALUES (?, ?, ?)
        """, (
            data.get("language_name", "").strip(),
            data.get("proficiency", "Professional Working").strip(),
            data.get("certifications", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def update_language(item_id, data):
    with get_db() as conn:
        conn.execute("""
            UPDATE languages SET
                language_name = ?, proficiency = ?, certifications = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get("language_name", "").strip(),
            data.get("proficiency", "Professional Working").strip(),
            data.get("certifications", "").strip(),
            item_id
        ))
        conn.commit()

def delete_language(item_id):
    with get_db() as conn:
        conn.execute("DELETE FROM languages WHERE id = ?", (item_id,))
        conn.commit()

# ==================== MASTER PORTFOLIO DICT ====================
def get_all_portfolio_data():
    """Returns the complete portfolio aggregated as a clean dictionary."""
    return {
        "personal_info": get_personal_info(),
        "summary": get_summary(),
        "education": get_education(),
        "technical_skills": get_technical_skills(),
        "soft_skills": get_soft_skills(),
        "certifications": get_certifications(),
        "projects": get_projects(),
        "experience": get_experience(),
        "achievements": get_achievements(),
        "publications_activities": get_publications_activities(),
        "languages": get_languages()
    }

def get_portfolio_counts():
    """Returns statistics for dashboard cards."""
    with get_db() as conn:
        counts = {}
        for table in ["education", "technical_skills", "soft_skills", "certifications", 
                      "projects", "experience", "achievements", "publications_activities", 
                      "languages", "generated_resumes"]:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        
        has_profile = conn.execute("SELECT COUNT(*) FROM personal_info WHERE id=1").fetchone()[0]
        counts["has_profile"] = bool(has_profile)
        return counts

# ==================== GENERATED RESUMES ====================
def save_generated_resume(resume_data):
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO generated_resumes (resume_title, target_role, template_name, job_description, selected_items_json, customized_summary, pdf_filename, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resume_data.get("resume_title", "Custom Resume").strip(),
            resume_data.get("target_role", "Software Engineer").strip(),
            resume_data.get("template_name", "modern_ats").strip(),
            resume_data.get("job_description", "").strip(),
            resume_data.get("selected_items_json", "{}"),
            resume_data.get("customized_summary", "").strip(),
            resume_data.get("pdf_filename", "").strip(),
            resume_data.get("file_path", "").strip()
        ))
        conn.commit()
        return cursor.lastrowid

def get_generated_resumes():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM generated_resumes ORDER BY created_at DESC, id DESC").fetchall()
        return dict_list_from_rows(rows)

def get_generated_resume(item_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM generated_resumes WHERE id = ?", (item_id,)).fetchone()
        return dict_from_row(row)

# ==================== SHEETS SYNC STATE ====================
def get_sheets_sync_state():
    with get_db() as conn:
        row = conn.execute("SELECT * FROM sheets_sync_state WHERE id = 1").fetchone()
        return dict_from_row(row)

def update_sheets_sync_state(status, message, url=None, count=0, spreadsheet_id=None):
    with get_db() as conn:
        if url or spreadsheet_id:
            conn.execute("""
                UPDATE sheets_sync_state SET
                    last_sync_status = ?,
                    last_sync_message = ?,
                    spreadsheet_url = COALESCE(?, spreadsheet_url),
                    spreadsheet_id = COALESCE(?, spreadsheet_id),
                    records_synced = ?,
                    last_sync_time = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (status, message, url, spreadsheet_id, count))
        else:
            conn.execute("""
                UPDATE sheets_sync_state SET
                    last_sync_status = ?,
                    last_sync_message = ?,
                    records_synced = ?,
                    last_sync_time = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (status, message, count))
        conn.commit()

# ==================== SEED SAMPLE DATA ====================
def seed_sample_data(force=False):
    """
    Populates sample portfolio records for a fictional college candidate (Alex Morgan),
    carefully crafted with both Frontend and AI/ML competencies so both Resume A and Resume B
    can be generated immediately and tested thoroughly.
    """
    with get_db() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM personal_info WHERE id = 1").fetchone()[0]
        if existing > 0 and not force:
            return

        # 1. Personal Info
        conn.execute("""
            INSERT OR REPLACE INTO personal_info (id, full_name, email, phone, location, linkedin_url, github_url, portfolio_url)
            VALUES (1, 'Alex Morgan', 'alex.morgan.cs@example.com', '+1 (555) 234-5678', 'San Francisco, CA', 
                    'https://linkedin.com/in/alexmorgan-cs', 'https://github.com/alexmorgan-dev', 'https://alexmorgan.dev')
        """)

        # 2. Summary
        conn.execute("""
            INSERT OR REPLACE INTO summary (id, professional_summary, career_objective)
            VALUES (1, 
            'Motivated Computer Science senior with hands-on experience in full-stack web engineering, React/TypeScript frontends, and applied AI/ML systems using Python and PyTorch. Proven ability to build responsive web interfaces, optimize REST APIs, and deploy machine learning models with strong attention to code quality and user experience.',
            'Seeking a software engineering internship or entry-level role where I can contribute to high-impact web and AI applications while collaborating with talented engineering teams.')
        """)

        # 3. Education
        conn.execute("DELETE FROM education")
        conn.execute("""
            INSERT INTO education (institution, degree, field_of_study, start_date, end_date, gpa_or_grade, location, description)
            VALUES 
            ('California State University', 'Bachelor of Science', 'Computer Science', '2022-09', '2026-06', '3.88 / 4.00', 'San Francisco, CA', 
             'Relevant Coursework: Data Structures & Algorithms, Full-Stack Web Development, Machine Learning, Database Management Systems, Operating Systems, Cloud Computing. Dean''s Honor List (4 Semesters).')
        """)

        # 4. Technical Skills
        conn.execute("DELETE FROM technical_skills")
        skills = [
            # Programming Languages
            ('Programming Languages', 'Python', 'Expert', 3.5),
            ('Programming Languages', 'JavaScript (ES6+)', 'Advanced', 3.0),
            ('Programming Languages', 'TypeScript', 'Advanced', 2.0),
            ('Programming Languages', 'HTML5 & CSS3', 'Expert', 3.5),
            ('Programming Languages', 'SQL', 'Advanced', 2.5),
            ('Programming Languages', 'C++', 'Intermediate', 2.0),
            # Frontend & UI
            ('Frontend & Web', 'React.js', 'Advanced', 2.5),
            ('Frontend & Web', 'Next.js', 'Intermediate', 1.5),
            ('Frontend & Web', 'Tailwind CSS', 'Advanced', 2.0),
            ('Frontend & Web', 'Redux Toolkit', 'Intermediate', 1.5),
            ('Frontend & Web', 'Responsive UI & Accessibility (a11y)', 'Advanced', 3.0),
            # AI / Machine Learning
            ('AI & Machine Learning', 'PyTorch', 'Intermediate', 2.0),
            ('AI & Machine Learning', 'Scikit-learn', 'Advanced', 2.5),
            ('AI & Machine Learning', 'TensorFlow', 'Intermediate', 1.5),
            ('AI & Machine Learning', 'Pandas & NumPy', 'Expert', 3.0),
            ('AI & Machine Learning', 'Hugging Face Transformers', 'Intermediate', 1.5),
            ('AI & Machine Learning', 'Google Gemini API / LLMs', 'Advanced', 1.5),
            # Backend & Databases
            ('Backend & Databases', 'Flask', 'Advanced', 2.5),
            ('Backend & Databases', 'FastAPI', 'Intermediate', 1.5),
            ('Backend & Databases', 'Node.js / Express', 'Intermediate', 2.0),
            ('Backend & Databases', 'PostgreSQL', 'Intermediate', 2.0),
            ('Backend & Databases', 'SQLite', 'Expert', 3.0),
            # Developer Tools & Cloud
            ('DevOps & Tools', 'Git & GitHub', 'Advanced', 3.5),
            ('DevOps & Tools', 'Docker', 'Intermediate', 1.5),
            ('DevOps & Tools', 'RESTful API Design', 'Advanced', 3.0),
            ('DevOps & Tools', 'Linux / Bash Scripting', 'Intermediate', 2.0)
        ]
        conn.executemany("""
            INSERT INTO technical_skills (category, skill_name, proficiency_level, years_of_experience)
            VALUES (?, ?, ?, ?)
        """, skills)

        # 5. Soft Skills
        conn.execute("DELETE FROM soft_skills")
        soft_skills = [
            ('Technical Communication', 'Communication', 'Ability to articulate complex engineering problems clearly to cross-functional teams and stakeholders.'),
            ('Agile / Scrum Collaboration', 'Teamwork', 'Experienced in sprint ceremonies, peer code reviews, and pair programming in academic and internship settings.'),
            ('Problem Solving & Analytical Thinking', 'Problem Solving', 'Structured approach to debugging, algorithmic problem solving, and performance profiling.'),
            ('Adaptability & Fast Learner', 'Growth Mindset', 'Quick to pick up modern frameworks, cloud tools, and emerging AI technologies.')
        ]
        conn.executemany("""
            INSERT INTO soft_skills (skill_name, category, description)
            VALUES (?, ?, ?)
        """, soft_skills)

        # 6. Certifications
        conn.execute("DELETE FROM certifications")
        certs = [
            ('AWS Certified Cloud Practitioner', 'Amazon Web Services', '2025-01', '2028-01', 'AWS-CCP-987452', 'https://aws.amazon.com/verification'),
            ('Meta Front-End Developer Professional Certificate', 'Meta (Coursera)', '2024-08', '', 'META-FED-88419', 'https://coursera.org/verify/professional-cert/META-FED-88419'),
            ('Deep Learning Specialization', 'DeepLearning.AI', '2024-11', '', 'DL-SPEC-77312', 'https://coursera.org/verify/specialization/DL-SPEC-77312')
        ]
        conn.executemany("""
            INSERT INTO certifications (title, issuing_organization, issue_date, expiration_date, credential_id, credential_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, certs)

        # 7. Projects
        conn.execute("DELETE FROM projects")
        projects = [
            (
                'CloudPulse - Interactive DevOps Monitoring Dashboard',
                'Frontend Lead & Full-Stack Developer',
                'React, TypeScript, Tailwind CSS, Chart.js, Flask, WebSocket',
                '2024-09', '2024-12',
                'https://github.com/alexmorgan-dev/cloudpulse-dashboard',
                'https://cloudpulse-demo.web.app',
                'Engineered a real-time cluster health dashboard displaying CPU, memory, and container metrics with interactive charts and low-latency WebSocket streams.',
                'Designed responsive UI components adhering to WCAG 2.1 AA accessibility guidelines.\nImplemented custom reusable React charts handling 5,000+ data points with 60 FPS rendering.\nIntegrated state management with React Context and optimistic UI updates for quick user interactions.'
            ),
            (
                'VisionMed - Biomedical Image Classification with PyTorch',
                'Machine Learning Engineer',
                'Python, PyTorch, Torchvision, Scikit-learn, OpenCV, Docker',
                '2024-06', '2024-08',
                'https://github.com/alexmorgan-dev/visionmed-ai',
                '',
                'Developed a deep learning convolutional neural network pipeline to detect and classify pulmonary anomalies from chest X-ray radiographs.',
                'Fine-tuned a ResNet-50 architecture achieving 93.4% validation accuracy and 0.95 ROC-AUC on 15,000 public scans.\nImplemented data augmentation (mixup, affine transforms) mitigating class imbalance and reducing overfitting by 18%.\nContainerized the inference pipeline with Docker and FastAPI, maintaining sub-120ms latency per inference.'
            ),
            (
                'DevMarket - E-Commerce Component Library & Web App',
                'Full-Stack Developer',
                'Next.js, React, Tailwind CSS, Stripe API, PostgreSQL, Prisma',
                '2024-02', '2024-05',
                'https://github.com/alexmorgan-dev/devmarket-store',
                'https://devmarket-store.vercel.app',
                'Created a modern developer asset marketplace featuring dynamic filtering, server-side rendering for SEO, and checkout processing.',
                'Constructed an accessible design system with 25+ modular UI components.\nDecreased page load time by 42% utilizing Next.js incremental static regeneration (ISR) and image optimization.\nConnected secure Stripe webhooks for automated order fulfillment.'
            ),
            (
                'DocuSense - Multi-Document RAG Question-Answering Agent',
                'AI Developer',
                'Python, Google Gemini API, LangChain, FAISS, Streamlit',
                '2025-01', '2025-02',
                'https://github.com/alexmorgan-dev/docusense-rag',
                '',
                'Built an AI-powered document analysis system allowing users to query research PDFs with cited answers and source attribution.',
                'Utilized Google Gemini 2.5 Flash and vector similarity search over text embeddings with FAISS.\nImplemented strict hallucination guardrails verifying answers against chunked context citations.\nProcessed and indexed documents up to 200 pages with an average question turnaround of 1.4 seconds.'
            )
        ]
        conn.executemany("""
            INSERT INTO projects (title, role, technologies, start_date, end_date, github_url, live_url, description, highlights)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, projects)

        # 8. Experience / Internships
        conn.execute("DELETE FROM experience")
        experience = [
            (
                'Software Engineering Intern (Frontend)',
                'TechForward Solutions',
                'Internship',
                'San Jose, CA (Hybrid)',
                '2024-06', '2024-09', 0,
                'Refactored legacy customer portal pages into reusable React 18 functional components and TypeScript hooks.\nAccelerated initial page load speed by 35% through code-splitting, lazy-loading routes, and bundle analysis.\nCollaborated with UI/UX designers in Figma and participated in bi-weekly Agile sprint planning and code reviews.\nAuthored unit and component tests with Jest and React Testing Library, boosting code coverage from 54% to 81%.',
                'Received "Outstanding Intern Contribution" commendation for delivering key analytics widget ahead of schedule.'
            ),
            (
                'Undergraduate Research Assistant (Machine Learning Lab)',
                'University AI & Vision Research Lab',
                'Internship',
                'San Francisco, CA',
                '2023-09', '2024-05', 0,
                'Preprocessed, curated, and annotated diverse tabular and image datasets totaling 40GB+ using Pandas and OpenCV.\nAssisted PhD candidates in implementing baseline comparative models in PyTorch and TensorFlow for anomaly detection.\nMaintained clean experiment tracking and hyperparameter optimization scripts with Weights & Biases (W&B).',
                'Co-authored a conference workshop poster detailing data augmentation techniques in medical imaging.'
            )
        ]
        conn.executemany("""
            INSERT INTO experience (job_title, company_name, employment_type, location, start_date, end_date, is_current, responsibilities, achievements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, experience)

        # 9. Achievements & Awards
        conn.execute("DELETE FROM achievements")
        achievements = [
            ('1st Place Winner - HackTech 2024', 'California Tech Collegiate Hackathon', '2024-10', 'Awarded first place among 65+ student teams for building an AI-powered accessibility assistant for visually impaired developers.'),
            ('Dean''s Honor List (4 Consecutive Semesters)', 'California State University', '2024-12', 'Recognized for sustaining a cumulative GPA above 3.85 while completing full-time engineering coursework.')
        ]
        conn.executemany("""
            INSERT INTO achievements (title, issuer, date_received, description)
            VALUES (?, ?, ?, ?)
        """, achievements)

        # 10. Publications & Activities
        conn.execute("DELETE FROM publications_activities")
        pub_activities = [
            ('A Study on Data Augmentation Strategies for Low-Resource Medical Image Analysis', 'Research Paper', 'CSU Undergraduate Research Symposium', '2024-05', 'https://example.org/publications/alexmorgan-2024', 'Presented research findings on synthetic augmentation methods for small diagnostic imaging datasets.'),
            ('Google Developer Student Clubs (GDSC) - Web & AI Lead', 'Activity', 'Student Chapter', '2023 - Present', '', 'Mentored 80+ collegiate developers through hands-on technical workshops covering modern React, Git workflows, and Python machine learning basics.')
        ]
        conn.executemany("""
            INSERT INTO publications_activities (title, activity_type, organization_or_venue, date_or_duration, url, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, pub_activities)

        # 11. Languages
        conn.execute("DELETE FROM languages")
        languages = [
            ('English', 'Native / Bilingual', ''),
            ('Spanish', 'Professional Working', 'DELE B2 Certified')
        ]
        conn.executemany("""
            INSERT INTO languages (language_name, proficiency, certifications)
            VALUES (?, ?, ?)
        """, languages)

        conn.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with sample portfolio data.")
