import os
import io
import json
import pytest
import sqlite3
import pypdf

import database
import app as flask_app
import gemini_service
import resume_generator
import sheets

@pytest.fixture
def client():
    flask_app.app.config['TESTING'] = True
    database.init_db()
    with flask_app.app.test_client() as client:
        yield client

def test_database_initialization_and_seeding():
    """Verify tables exist and sample data is seeded for demo."""
    counts = database.get_portfolio_counts()
    assert counts["has_profile"] is True
    assert counts["technical_skills"] > 0
    assert counts["projects"] > 0
    assert counts["experience"] > 0
    assert counts["education"] > 0
    assert counts["certifications"] > 0

def test_portfolio_crud_operations():
    """Test creating, reading, updating, and deleting a portfolio record."""
    # Add skill
    new_skill = {
        "category": "Cloud Platforms",
        "skill_name": "Google Cloud Platform",
        "proficiency_level": "Intermediate",
        "years_of_experience": 1.5
    }
    skill_id = database.add_technical_skill(new_skill)
    assert skill_id is not None

    # Read skill
    skill = database.get_technical_skills(skill_id)
    assert skill["skill_name"] == "Google Cloud Platform"
    assert skill["category"] == "Cloud Platforms"

    # Update skill
    updated_data = {
        "category": "Cloud Platforms",
        "skill_name": "Google Cloud Platform (GCP)",
        "proficiency_level": "Advanced",
        "years_of_experience": 2.0
    }
    database.update_technical_skill(skill_id, updated_data)
    skill_updated = database.get_technical_skills(skill_id)
    assert skill_updated["skill_name"] == "Google Cloud Platform (GCP)"
    assert skill_updated["proficiency_level"] == "Advanced"

    # Delete skill
    database.delete_technical_skill(skill_id)
    assert database.get_technical_skills(skill_id) is None

def test_database_persistence():
    """Test that records persist across connection close and re-open."""
    test_title = "Persistence Test Project"
    proj_id = database.add_project({
        "title": test_title,
        "role": "Lead",
        "technologies": "SQLite, Python",
        "start_date": "2024-01",
        "end_date": "2024-03",
        "description": "Persistence test"
    })
    
    # Reconnect
    conn = database.get_db()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (proj_id,)).fetchone()
    assert row is not None
    assert row["title"] == test_title
    conn.close()

    # Clean up
    database.delete_project(proj_id)

def test_gemini_missing_credentials_graceful_handling():
    """Ensure missing or dummy GEMINI_API_KEY does not crash the system."""
    client, model, error = gemini_service.get_gemini_client()
    # In test environment, if no key is configured, error is returned cleanly
    analysis = gemini_service.analyze_job_description("Software Engineer needed with Python and React.")
    assert "data" in analysis
    assert len(analysis["data"]["required_skills"]) > 0

def test_job_description_analysis_and_safeguards():
    """Test job analysis extracts skills and portfolio matching categorizes learning gaps."""
    frontend_job = flask_app.SAMPLE_JOB_FRONTEND
    analysis_res = gemini_service.analyze_job_description(frontend_job)
    data = analysis_res["data"]
    assert "required_skills" in data

    portfolio = database.get_all_portfolio_data()
    match = gemini_service.match_portfolio_to_job(data, portfolio)
    
    assert "matched_skills" in match
    assert "missing_skills" in match
    assert match["match_score"] >= 0

    # Ensure missing skills are identified as learning gaps and never falsely listed in matched_skills
    for missing in match["missing_skills"]:
        assert missing not in match["matched_skills"]

def test_reportlab_pdf_generation_and_anti_fabrication():
    """
    Generate PDF and inspect with pypdf to verify that verified items exist
    and unverified claims are excluded.
    """
    portfolio = database.get_all_portfolio_data()
    target_role = "Frontend Test Role"
    
    result = resume_generator.build_pdf_resume({
        "personal_info": portfolio["personal_info"],
        "target_role": target_role,
        "summary_text": "Verified summary text without fabrication.",
        "technical_skills": [s for s in portfolio["technical_skills"] if s["skill_name"] == "React.js"],
        "projects": portfolio["projects"][:1],
        "experience": portfolio["experience"][:1],
        "education": portfolio["education"],
        "certifications": [],
        "achievements": [],
        "languages": []
    }, template_name="modern_ats", output_filename="test_anti_fabrication.pdf")

    assert os.path.exists(result["file_path"])

    # Extract text from generated PDF with pypdf
    reader = pypdf.PdfReader(result["file_path"])
    full_pdf_text = ""
    for page in reader.pages:
        full_pdf_text += page.extract_text()

    assert "FRONTEND TEST ROLE" in full_pdf_text
    assert "React.js" in full_pdf_text
    # Non-selected / unverified skill should not be present
    assert "Kubernetes" not in full_pdf_text

def test_two_customized_resume_demonstrations(client):
    """Test generation of Resume A (Frontend) and Resume B (AI/ML)."""
    response = client.get('/sample-resumes/generate-defaults', follow_redirects=True)
    assert response.status_code == 200

    # Verify both PDF files exist on disk
    res_a_path = os.path.join(flask_app.GENERATED_FOLDER, "Demo_Resume_A_Frontend_Developer_Internship.pdf")
    res_b_path = os.path.join(flask_app.GENERATED_FOLDER, "Demo_Resume_B_AIML_Internship.pdf")

    assert os.path.exists(res_a_path)
    assert os.path.exists(res_b_path)

    # Verify Resume A contains frontend skills and Resume B contains AI/ML skills
    text_a = "".join(page.extract_text() for page in pypdf.PdfReader(res_a_path).pages)
    text_b = "".join(page.extract_text() for page in pypdf.PdfReader(res_b_path).pages)

    assert "FRONTEND DEVELOPER INTERN" in text_a
    assert "TypeScript" in text_a or "React.js" in text_a

    assert "AI / MACHINE LEARNING" in text_b
    assert "PyTorch" in text_b or "Python" in text_b

def test_secure_download_route(client):
    """Verify secure download endpoint protects against directory traversal."""
    # Valid download
    res = client.get('/download-resume/Demo_Resume_A_Frontend_Developer_Internship.pdf')
    assert res.status_code == 200
    assert res.headers["Content-Type"] == "application/pdf"

    # Non-existent file
    res_404 = client.get('/download-resume/nonexistent_file.pdf')
    assert res_404.status_code == 404

    # Traversal attempt
    res_traversal = client.get('/download-resume/../../etc/passwd')
    assert res_traversal.status_code in [400, 404]

def test_google_sheets_graceful_missing_credentials():
    """Verify that absent credentials provide clear, informative errors rather than crashes."""
    res = sheets.sync_portfolio_to_google_sheets()
    assert res["success"] is False
    assert "service_account" in res["error"].lower() or "credentials" in res["error"].lower()

def test_resume_pdf_text_extraction_and_import(client):
    """Test importing an existing PDF resume using pypdf and review workflow."""
    # We can use one of our generated PDFs as an uploaded resume test
    demo_pdf_path = os.path.join(flask_app.GENERATED_FOLDER, "Demo_Resume_A_Frontend_Developer_Internship.pdf")
    with open(demo_pdf_path, 'rb') as f:
        pdf_bytes = io.BytesIO(f.read())

    res = client.post('/import-resume', data={
        'resume_pdf': (pdf_bytes, 'candidate_resume.pdf')
    }, content_type='multipart/form-data')

    assert res.status_code == 200
    assert b"Review &amp; Verify Extracted Records" in res.data or b"Review & Verify Extracted Records" in res.data
