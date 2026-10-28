import os
import re
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, abort
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import pypdf

import database
import gemini_service
import resume_generator
import sheets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "portfolio-ai-secret-key-college-demo")

# Upload and output directory configs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
GENERATED_FOLDER = os.path.join(BASE_DIR, 'generated_resumes')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max upload

# Initialize database on application start
with app.app_context():
    database.init_db()

# Sample Job Descriptions for Demonstration
SAMPLE_JOB_FRONTEND = """Job Title: Frontend Developer Intern
Company: TechNova Interactive
Location: San Francisco, CA (Hybrid)

About the Role:
We are seeking a talented and proactive Frontend Developer Intern to join our web applications team. You will assist in engineering responsive, high-performance web applications using modern JavaScript and React.

Key Responsibilities:
- Build and maintain accessible, cross-browser web interfaces using React.js, TypeScript, and modern CSS.
- Collaborate with backend engineers to integrate RESTful APIs and WebSocket data feeds.
- Write clean, modular, and maintainable code adhering to UI component design standards.
- Participate in Agile sprint planning, peer code reviews, and automated UI testing.

Required Qualifications & Skills:
- Working knowledge of HTML5, CSS3, JavaScript (ES6+), and React.js.
- Familiarity with TypeScript and CSS frameworks like Tailwind CSS.
- Understanding of state management (Redux Toolkit or React Context).
- Experience with Git version control and collaborative GitHub workflows.
- Strong problem-solving skills and eye for user interface design and accessibility (a11y).

Preferred Qualifications:
- Familiarity with Next.js or server-side rendering concepts.
- Basic understanding of Docker and CI/CD pipelines.
- Enrolled in or recently graduated with a BS in Computer Science, Software Engineering, or related field."""

SAMPLE_JOB_AIML = """Job Title: AI / Machine Learning Engineering Intern
Company: DataCortex AI Labs
Location: San Francisco, CA

About the Role:
DataCortex AI Labs is looking for a driven AI/ML Engineering Intern to help build next-generation machine learning and generative AI workflows. You will work alongside senior research engineers to train, evaluate, and deploy scalable ML models.

Key Responsibilities:
- Implement, fine-tune, and evaluate deep learning models using Python and PyTorch.
- Preprocess, augment, and validate complex tabular and image datasets with Pandas, NumPy, and OpenCV.
- Build retrieval-augmented generation (RAG) pipelines integrating modern LLM APIs (Google Gemini, OpenAI).
- Containerize inference endpoints and optimize latency for real-time model serving.
- Track experiments, loss metrics, and benchmarks with structured experiment tools.

Required Qualifications & Skills:
- Proficiency in Python programming and core scientific computing libraries (NumPy, Pandas, Scikit-learn).
- Hands-on experience developing neural networks with PyTorch or TensorFlow.
- Experience utilizing LLM APIs (Google Gemini API, Hugging Face Transformers) or vector search.
- Strong foundation in linear algebra, statistics, and machine learning fundamentals.
- Enrolled in or graduated with a Degree in Computer Science, Artificial Intelligence, or Data Science.

Preferred Qualifications:
- Experience with Docker, FastAPI, and model deployment pipelines.
- Knowledge of medical image analysis, computer vision, or natural language processing (NLP).
- Proven GitHub projects or hackathon contributions demonstrating applied AI systems."""

# ==================== ROUTE 1: DASHBOARD ====================
@app.route('/')
def index():
    counts = database.get_portfolio_counts()
    personal = database.get_personal_info()
    summary = database.get_summary()
    sync_state = database.get_sheets_sync_state()
    resumes = database.get_generated_resumes()[:5]

    return render_template(
        'index.html',
        counts=counts,
        personal=personal,
        summary=summary,
        sync_state=sync_state,
        recent_resumes=resumes
    )

# ==================== ROUTE 2: PORTFOLIO MANAGEMENT ====================
@app.route('/portfolio')
def portfolio():
    data = database.get_all_portfolio_data()
    active_tab = request.args.get('tab', 'personal')
    return render_template('portfolio.html', data=data, active_tab=active_tab)

# Generic REST APIs for Portfolio CRUD
@app.route('/api/portfolio/personal', methods=['POST'])
def update_personal():
    data = request.form.to_dict() if request.form else request.get_json() or {}
    database.save_personal_info(data)
    flash("Personal contact information updated successfully.", "success")
    return redirect(url_for('portfolio', tab='personal'))

@app.route('/api/portfolio/summary', methods=['POST'])
def update_summary():
    data = request.form.to_dict() if request.form else request.get_json() or {}
    database.save_summary(data)
    flash("Professional summary updated successfully.", "success")
    return redirect(url_for('portfolio', tab='summary'))

@app.route('/api/portfolio/<category>', methods=['POST'])
def add_portfolio_item(category):
    data = request.form.to_dict() if request.form else request.get_json() or {}
    
    if category == 'education':
        database.add_education(data)
    elif category == 'technical_skills':
        database.add_technical_skill(data)
    elif category == 'soft_skills':
        database.add_soft_skill(data)
    elif category == 'certifications':
        database.add_certification(data)
    elif category == 'projects':
        database.add_project(data)
    elif category == 'experience':
        database.add_experience(data)
    elif category == 'achievements':
        database.add_achievement(data)
    elif category == 'publications':
        database.add_publication_activity(data)
    elif category == 'languages':
        database.add_language(data)
    else:
        flash(f"Unknown category '{category}'.", "danger")
        return redirect(url_for('portfolio'))

    flash(f"New {category.replace('_', ' ').rstrip('s')} record added successfully.", "success")
    return redirect(url_for('portfolio', tab=category))

@app.route('/api/portfolio/<category>/<int:item_id>/update', methods=['POST'])
def update_portfolio_item(category, item_id):
    data = request.form.to_dict() if request.form else request.get_json() or {}

    if category == 'education':
        database.update_education(item_id, data)
    elif category == 'technical_skills':
        database.update_technical_skill(item_id, data)
    elif category == 'soft_skills':
        database.update_soft_skill(item_id, data)
    elif category == 'certifications':
        database.update_certification(item_id, data)
    elif category == 'projects':
        database.update_project(item_id, data)
    elif category == 'experience':
        database.update_experience(item_id, data)
    elif category == 'achievements':
        database.update_achievement(item_id, data)
    elif category == 'publications':
        database.update_publication_activity(item_id, data)
    elif category == 'languages':
        database.update_language(item_id, data)
    else:
        flash(f"Unknown category '{category}'.", "danger")
        return redirect(url_for('portfolio'))

    flash(f"{category.replace('_', ' ').rstrip('s').capitalize()} record updated successfully.", "success")
    return redirect(url_for('portfolio', tab=category))

@app.route('/api/portfolio/<category>/<int:item_id>/delete', methods=['POST'])
def delete_portfolio_item(category, item_id):
    if category == 'education':
        database.delete_education(item_id)
    elif category == 'technical_skills':
        database.delete_technical_skill(item_id)
    elif category == 'soft_skills':
        database.delete_soft_skill(item_id)
    elif category == 'certifications':
        database.delete_certification(item_id)
    elif category == 'projects':
        database.delete_project(item_id)
    elif category == 'experience':
        database.delete_experience(item_id)
    elif category == 'achievements':
        database.delete_achievement(item_id)
    elif category == 'publications':
        database.delete_publication_activity(item_id)
    elif category == 'languages':
        database.delete_language(item_id)

    flash(f"Record removed from {category.replace('_', ' ')}.", "info")
    return redirect(url_for('portfolio', tab=category))

# ==================== ROUTE 3: IMPORT RESUME PDF ====================
@app.route('/import-resume', methods=['GET', 'POST'])
def import_resume():
    if request.method == 'GET':
        return render_template('import_resume.html', parsed_data=None)

    # File upload handling
    if 'resume_pdf' not in request.files:
        flash("No file part in the request.", "danger")
        return redirect(request.url)

    file = request.files['resume_pdf']
    if file.filename == '':
        flash("Please select a valid PDF file to upload.", "warning")
        return redirect(request.url)

    if not file.filename.lower().endswith('.pdf'):
        flash("Invalid file format. Only PDF files are supported.", "danger")
        return redirect(request.url)

    # Save uploaded file safely
    filename = secure_filename(f"upload_{int(datetime.now().timestamp())}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract text using pypdf
    try:
        reader = pypdf.PdfReader(filepath)
        extracted_text = ""
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

        if not extracted_text.strip():
            flash("Warning: No extractable text found in this PDF. It appears to be a scanned image or empty. Please upload a text-based PDF.", "warning")
            return render_template('import_resume.html', parsed_data=None, is_scanned_error=True)

    except Exception as e:
        flash(f"Failed to read PDF file: {str(e)}", "danger")
        return render_template('import_resume.html', parsed_data=None)

    # Send to Gemini for structured extraction
    result = gemini_service.parse_resume_text_to_portfolio(extracted_text)
    
    if not result.get("success") and result.get("error"):
        flash(f"Notice: {result.get('error')}. Extracted basic info for review.", "warning")

    return render_template(
        'import_resume.html',
        parsed_data=result.get("data"),
        raw_text=extracted_text[:2000], # preview snippet
        model_used=result.get("model_used")
    )

@app.route('/import-resume/approve', methods=['POST'])
def approve_imported_resume():
    """
    Saves verified imported records into SQLite after candidate review and approval.
    """
    try:
        data = request.get_json() if request.is_json else json.loads(request.form.get("structured_json", "{}"))

        # Save personal info if provided
        if data.get("personal_info") and data["personal_info"].get("full_name"):
            database.save_personal_info(data["personal_info"])

        # Save summary
        if data.get("summary") and data["summary"].get("professional_summary"):
            database.save_summary(data["summary"])

        # Save approved items
        for edu in data.get("education", []):
            if edu.get("institution"):
                database.add_education(edu)

        for skill in data.get("technical_skills", []):
            if skill.get("skill_name"):
                database.add_technical_skill(skill)

        for s_skill in data.get("soft_skills", []):
            if s_skill.get("skill_name"):
                database.add_soft_skill(s_skill)

        for cert in data.get("certifications", []):
            if cert.get("title"):
                database.add_certification(cert)

        for proj in data.get("projects", []):
            if proj.get("title"):
                database.add_project(proj)

        for exp in data.get("experience", []):
            if exp.get("job_title"):
                database.add_experience(exp)

        for ach in data.get("achievements", []):
            if ach.get("title"):
                database.add_achievement(ach)

        for pub in data.get("publications_activities", []):
            if pub.get("title"):
                database.add_publication_activity(pub)

        for lang in data.get("languages", []):
            if lang.get("language_name"):
                database.add_language(lang)

        flash("Verified resume records have been successfully saved into your master database!", "success")
        return jsonify({"success": True, "redirect": url_for('portfolio')})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ==================== ROUTE 4: JOB ANALYZER ====================
@app.route('/job-analyzer', methods=['GET', 'POST'])
def job_analyzer():
    sample_type = request.args.get('sample')
    prefill_text = ""
    if sample_type == 'frontend':
        prefill_text = SAMPLE_JOB_FRONTEND
    elif sample_type == 'aiml':
        prefill_text = SAMPLE_JOB_AIML

    if request.method == 'GET':
        return render_template(
            'job_analyzer.html',
            job_text=prefill_text,
            analysis=None,
            match_result=None
        )

    job_text = request.form.get('job_description', '').strip()
    if not job_text:
        flash("Please enter or paste a job description.", "warning")
        return redirect(url_for('job_analyzer'))

    # Run Gemini Job Analysis
    analysis_res = gemini_service.analyze_job_description(job_text)
    analysis_data = analysis_res.get("data", {})

    # Run Portfolio Match against SQLite
    portfolio_data = database.get_all_portfolio_data()
    match_result = gemini_service.match_portfolio_to_job(analysis_data, portfolio_data)

    return render_template(
        'job_analyzer.html',
        job_text=job_text,
        analysis=analysis_data,
        match_result=match_result,
        gemini_error=analysis_res.get("error")
    )

# ==================== ROUTE 5: RESUME BUILDER ====================
@app.route('/resume-builder', methods=['GET', 'POST'])
def resume_builder():
    portfolio_data = database.get_all_portfolio_data()
    preset = request.args.get('preset')

    initial_job_text = ""
    initial_target_role = "Software Engineer"
    if preset == 'frontend':
        initial_job_text = SAMPLE_JOB_FRONTEND
        initial_target_role = "Frontend Developer Intern"
    elif preset == 'aiml':
        initial_job_text = SAMPLE_JOB_AIML
        initial_target_role = "AI / Machine Learning Engineering Intern"

    return render_template(
        'resume_builder.html',
        portfolio=portfolio_data,
        initial_job_text=initial_job_text,
        initial_target_role=initial_target_role,
        sample_frontend=SAMPLE_JOB_FRONTEND,
        sample_aiml=SAMPLE_JOB_AIML
    )

@app.route('/api/analyze-and-match', methods=['POST'])
def api_analyze_and_match():
    """AJAX endpoint for analyzing job description and returning matched items."""
    data = request.get_json() or {}
    job_text = data.get("job_description", "").strip()

    if not job_text:
        return jsonify({"success": False, "error": "Job description text is empty."}), 400

    analysis_res = gemini_service.analyze_job_description(job_text)
    analysis_data = analysis_res.get("data", {})

    portfolio_data = database.get_all_portfolio_data()
    match_result = gemini_service.match_portfolio_to_job(analysis_data, portfolio_data)

    # Suggest tailored summary grounded in verified facts
    orig_summary = (portfolio_data.get("summary") or {}).get("professional_summary", "")
    target_role = analysis_data.get("job_title") or data.get("target_role") or "Software Engineer"
    suggested_summary = gemini_service.generate_tailored_summary(
        target_role, match_result.get("matched_skills", []), orig_summary
    )

    return jsonify({
        "success": True,
        "analysis": analysis_data,
        "match": match_result,
        "suggested_summary": suggested_summary
    })

@app.route('/api/generate-resume-pdf', methods=['POST'])
def api_generate_resume_pdf():
    """Builds and compiles the official PDF resume using ReportLab."""
    try:
        data = request.get_json() or {}
        portfolio_data = database.get_all_portfolio_data()

        target_role = data.get("target_role", "Software Engineer").strip()
        template_name = data.get("template_name", "modern_ats")
        custom_summary = data.get("summary_text", "").strip()
        job_description = data.get("job_description", "")

        # Extract selected IDs from request
        selected_skills = data.get("selected_skills", [])
        selected_projects = data.get("selected_projects", [])
        selected_experience = data.get("selected_experience", [])
        selected_education = data.get("selected_education", [])
        selected_certs = data.get("selected_certifications", [])
        selected_achievements = data.get("selected_achievements", [])
        selected_languages = data.get("selected_languages", [])

        # Filter portfolio based on verified user selection
        filtered_skills = [s for s in portfolio_data.get("technical_skills", []) if s["id"] in selected_skills]
        filtered_projects = [p for p in portfolio_data.get("projects", []) if p["id"] in selected_projects]
        filtered_exp = [e for e in portfolio_data.get("experience", []) if e["id"] in selected_experience]
        filtered_edu = [ed for ed in portfolio_data.get("education", []) if ed["id"] in selected_education]
        filtered_certs = [c for c in portfolio_data.get("certifications", []) if c["id"] in selected_certs]
        filtered_ach = [a for a in portfolio_data.get("achievements", []) if a["id"] in selected_achievements]
        filtered_lang = [l for l in portfolio_data.get("languages", []) if l["id"] in selected_languages]

        # Assemble PDF payload
        resume_payload = {
            "personal_info": portfolio_data.get("personal_info"),
            "target_role": target_role,
            "summary_text": custom_summary or (portfolio_data.get("summary") or {}).get("professional_summary", ""),
            "technical_skills": filtered_skills,
            "projects": filtered_projects,
            "experience": filtered_exp,
            "education": filtered_edu,
            "certifications": filtered_certs,
            "achievements": filtered_ach,
            "languages": filtered_lang
        }

        # Build PDF with ReportLab
        result = resume_generator.build_pdf_resume(resume_payload, template_name=template_name)

        # Save record in database history
        resume_title = f"{target_role} ({template_name.replace('_', ' ').title()})"
        database.save_generated_resume({
            "resume_title": resume_title,
            "target_role": target_role,
            "template_name": template_name,
            "job_description": job_description[:500],
            "selected_items_json": json.dumps(data),
            "customized_summary": custom_summary,
            "pdf_filename": result["filename"],
            "file_path": result["file_path"]
        })

        return jsonify({
            "success": True,
            "filename": result["filename"],
            "download_url": result["relative_path"],
            "message": "Resume PDF generated successfully!"
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"PDF Generation Error: {str(e)}"}), 500

# ==================== ROUTE 6: DOWNLOAD RESUME (SECURE) ====================
@app.route('/download-resume/<filename>')
def download_resume(filename):
    """
    Secure file download with path traversal protection.
    """
    # Sanitize and ensure only alphanumeric, underscores, dots, hyphens
    sanitized = secure_filename(filename)
    if not sanitized.endswith('.pdf'):
        abort(400, "Invalid file format.")

    file_path = os.path.join(GENERATED_FOLDER, sanitized)
    if not os.path.exists(file_path):
        abort(404, "Requested resume file not found.")

    return send_from_directory(
        GENERATED_FOLDER,
        sanitized,
        as_attachment=True,
        download_name=sanitized
    )

# ==================== ROUTE 7: RESUMES LIST / HISTORY ====================
@app.route('/resumes')
def resumes_list():
    all_resumes = database.get_generated_resumes()
    return render_template('resumes_list.html', resumes=all_resumes)

# ==================== ROUTE 8: GOOGLE SHEETS ====================
@app.route('/google-sheets')
def google_sheets_view():
    sync_state = database.get_sheets_sync_state()
    creds_info, creds_error = sheets.get_google_credentials_info()
    return render_template(
        'sheets.html',
        sync_state=sync_state,
        creds_configured=(creds_error is None),
        creds_error=creds_error
    )

@app.route('/google-sheets/sync', methods=['POST'])
def trigger_google_sheets_sync():
    """Triggers the real Google Sheets export and sync operation."""
    result = sheets.sync_portfolio_to_google_sheets()
    if result.get("success"):
        flash(f"Synchronization successful! {result.get('message')}", "success")
    else:
        flash(f"Synchronization failed: {result.get('error')}", "danger")
    return redirect(url_for('google_sheets_view'))

@app.route('/export-spreadsheet')
def export_spreadsheet():
    """Generates and downloads the full 10-tab spreadsheet workbook for Google Sheets & Excel."""
    filepath = os.path.join(GENERATED_FOLDER, "PortfolioAI_Master_Database.xlsx")
    sheets.export_portfolio_to_workbook(filepath)
    return send_from_directory(
        GENERATED_FOLDER,
        "PortfolioAI_Master_Database.xlsx",
        as_attachment=True,
        download_name="PortfolioAI_Master_Database.xlsx"
    )

# ==================== ROUTE 9: GENERATE DEMO RESUMES ====================
@app.route('/sample-resumes/generate-defaults', methods=['POST', 'GET'])
def generate_default_demonstrations():
    """
    Generates the two required demonstration resumes:
    - Resume A: Frontend Developer Internship
    - Resume B: AI/ML Internship
    using verified portfolio records.
    """
    portfolio_data = database.get_all_portfolio_data()

    # Resume A: Frontend Developer
    frontend_skills = [
        s for s in portfolio_data.get("technical_skills", [])
        if s["category"] in ['Frontend & Web', 'Programming Languages', 'DevOps & Tools'] and
        s["skill_name"] in ['JavaScript (ES6+)', 'TypeScript', 'React.js', 'Next.js', 'HTML5 & CSS3', 'Tailwind CSS', 'Redux Toolkit', 'Git & GitHub', 'RESTful API Design']
    ]
    frontend_projects = [
        p for p in portfolio_data.get("projects", [])
        if 'React' in p.get("technologies", "") or 'Next.js' in p.get("technologies", "")
    ]
    frontend_exp = [
        e for e in portfolio_data.get("experience", [])
        if 'Frontend' in e.get("job_title", "")
    ]
    frontend_certs = [
        c for c in portfolio_data.get("certifications", [])
        if 'Front-End' in c.get("title", "") or 'AWS' in c.get("title", "")
    ]

    res_a = resume_generator.build_pdf_resume({
        "personal_info": portfolio_data.get("personal_info"),
        "target_role": "Frontend Developer Intern",
        "summary_text": "Motivated Computer Science senior specializing in modern frontend engineering with React, TypeScript, and accessible UI systems. Experienced in creating high-performance web applications, optimizing component render speeds, and collaborating in Agile teams.",
        "technical_skills": frontend_skills,
        "projects": frontend_projects,
        "experience": frontend_exp,
        "education": portfolio_data.get("education"),
        "certifications": frontend_certs,
        "achievements": portfolio_data.get("achievements"),
        "languages": portfolio_data.get("languages")
    }, template_name='modern_ats', output_filename='Demo_Resume_A_Frontend_Developer_Internship.pdf')

    database.save_generated_resume({
        "resume_title": "Resume A: Frontend Developer Internship",
        "target_role": "Frontend Developer Intern",
        "template_name": "modern_ats",
        "job_description": SAMPLE_JOB_FRONTEND[:500],
        "selected_items_json": json.dumps({"preset": "frontend"}),
        "customized_summary": "Tailored for Frontend Developer Internship",
        "pdf_filename": res_a["filename"],
        "file_path": res_a["file_path"]
    })

    # Resume B: AI/ML Internship
    aiml_skills = [
        s for s in portfolio_data.get("technical_skills", [])
        if s["category"] in ['AI & Machine Learning', 'Programming Languages', 'Backend & Databases', 'DevOps & Tools'] and
        s["skill_name"] in ['Python', 'PyTorch', 'Scikit-learn', 'TensorFlow', 'Pandas & NumPy', 'Google Gemini API / LLMs', 'Docker', 'FastAPI']
    ]
    aiml_projects = [
        p for p in portfolio_data.get("projects", [])
        if 'PyTorch' in p.get("technologies", "") or 'Gemini' in p.get("technologies", "")
    ]
    aiml_exp = [
        e for e in portfolio_data.get("experience", [])
        if 'Machine Learning' in e.get("job_title", "") or 'Research' in e.get("job_title", "")
    ]
    aiml_certs = [
        c for c in portfolio_data.get("certifications", [])
        if 'Deep Learning' in c.get("title", "") or 'AWS' in c.get("title", "")
    ]

    res_b = resume_generator.build_pdf_resume({
        "personal_info": portfolio_data.get("personal_info"),
        "target_role": "AI / Machine Learning Engineering Intern",
        "summary_text": "Aspiring AI and Machine Learning engineer with hands-on expertise in deep learning model development using PyTorch, medical image classification, and Retrieval-Augmented Generation (RAG) with the Google Gemini API. Solid foundation in data pipelines, statistics, and containerized deployment.",
        "technical_skills": aiml_skills,
        "projects": aiml_projects,
        "experience": aiml_exp,
        "education": portfolio_data.get("education"),
        "certifications": aiml_certs,
        "achievements": portfolio_data.get("achievements"),
        "languages": portfolio_data.get("languages")
    }, template_name='minimal_tech', output_filename='Demo_Resume_B_AIML_Internship.pdf')

    database.save_generated_resume({
        "resume_title": "Resume B: AI / Machine Learning Internship",
        "target_role": "AI / Machine Learning Engineering Intern",
        "template_name": "minimal_tech",
        "job_description": SAMPLE_JOB_AIML[:500],
        "selected_items_json": json.dumps({"preset": "aiml"}),
        "customized_summary": "Tailored for AI/ML Internship",
        "pdf_filename": res_b["filename"],
        "file_path": res_b["file_path"]
    })

    flash("Generated both demonstration resumes successfully (Resume A: Frontend Developer & Resume B: AI/ML)!", "success")
    return redirect(url_for('resumes_list'))

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
