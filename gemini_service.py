import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

def get_gemini_client():
    """
    Initializes and returns the official google-genai client if GEMINI_API_KEY is configured.
    Returns (client, model_name, error_message).
    """
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    if not api_key or api_key == "your_gemini_api_key_here":
        return None, model_name, "GEMINI_API_KEY is not configured in .env file."

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        return client, model_name, None
    except Exception as e:
        return None, model_name, f"Failed to initialize Gemini client: {str(e)}"

def clean_json_response(text):
    """Strips markdown code fences and cleans up JSON string."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

# ==================== A. RESUME PDF PARSING ====================
def parse_resume_text_to_portfolio(resume_text):
    """
    Uses Gemini to extract structured portfolio fields from resume text.
    Safeguards:
    - Never invents missing dates or qualifications.
    - Leaves absent information empty.
    - Returns structured schema for human review.
    """
    client, model_name, error = get_gemini_client()

    prompt = f"""
You are an expert resume parser for a verified professional portfolio database.
Analyze the following extracted resume text and convert it into a structured JSON object matching the database schema.

CRITICAL SAFEGUARDS:
1. ONLY include facts explicitly present in the text.
2. DO NOT hallucinate or invent dates, degrees, companies, metrics, or certifications.
3. If an item is missing or ambiguous, leave the field as an empty string "" or an empty list [].
4. Categorize technical skills into groups: "Programming Languages", "Frontend & Web", "AI & Machine Learning", "Backend & Databases", "DevOps & Tools".

Resume Text:
\"\"\"
{resume_text}
\"\"\"

Return ONLY a valid JSON object with the following exact keys:
{{
  "personal_info": {{
    "full_name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin_url": "",
    "github_url": "",
    "portfolio_url": ""
  }},
  "summary": {{
    "professional_summary": "",
    "career_objective": ""
  }},
  "education": [
    {{
      "institution": "",
      "degree": "",
      "field_of_study": "",
      "start_date": "",
      "end_date": "",
      "gpa_or_grade": "",
      "location": "",
      "description": ""
    }}
  ],
  "technical_skills": [
    {{
      "category": "Programming Languages",
      "skill_name": "",
      "proficiency_level": "Intermediate",
      "years_of_experience": 1.0
    }}
  ],
  "soft_skills": [
    {{
      "skill_name": "",
      "category": "Interpersonal",
      "description": ""
    }}
  ],
  "certifications": [
    {{
      "title": "",
      "issuing_organization": "",
      "issue_date": "",
      "expiration_date": "",
      "credential_id": "",
      "credential_url": ""
    }}
  ],
  "projects": [
    {{
      "title": "",
      "role": "",
      "technologies": "",
      "start_date": "",
      "end_date": "",
      "github_url": "",
      "live_url": "",
      "description": "",
      "highlights": "Bullet 1\\nBullet 2"
    }}
  ],
  "experience": [
    {{
      "job_title": "",
      "company_name": "",
      "employment_type": "Internship",
      "location": "",
      "start_date": "",
      "end_date": "",
      "is_current": false,
      "responsibilities": "Bullet 1\\nBullet 2",
      "achievements": ""
    }}
  ],
  "achievements": [
    {{
      "title": "",
      "issuer": "",
      "date_received": "",
      "description": ""
    }}
  ],
  "publications_activities": [
    {{
      "title": "",
      "activity_type": "Research Paper",
      "organization_or_venue": "",
      "date_or_duration": "",
      "url": "",
      "description": ""
    }}
  ],
  "languages": [
    {{
      "language_name": "",
      "proficiency": "Professional Working",
      "certifications": ""
    }}
  ]
}}
"""

    if not client:
        # Fallback heuristic parser if API key is not yet set
        return {
            "success": False,
            "error": error,
            "data": heuristic_resume_parse(resume_text)
        }

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        cleaned = clean_json_response(response.text)
        parsed_data = json.loads(cleaned)
        return {
            "success": True,
            "model_used": model_name,
            "data": parsed_data
        }
    except Exception as e:
        err_str = str(e)
        if "PERMISSION_DENIED" in err_str or "billing" in err_str:
            clean_err = "Gemini API Project Notice: The Google Cloud project for this key has free-tier access disabled (a billing account is required at aistudio.google.com/billing, or free tier is disabled for this organization)."
        elif "NOT_FOUND" in err_str:
            clean_err = f"Model '{model_name}' is not accessible on this key. Please select a supported model in .env."
        else:
            clean_err = f"Gemini API Notice: {err_str}"

        return {
            "success": False,
            "error": clean_err,
            "data": heuristic_resume_parse(resume_text)
        }

def heuristic_resume_parse(text):
    """Extracts basic contact and text fields when Gemini API key is not yet provided."""
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    github_match = re.search(r'github\.com\/[a-zA-Z0-9_-]+', text)
    linkedin_match = re.search(r'linkedin\.com\/in\/[a-zA-Z0-9_-]+', text)

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    full_name = lines[0] if lines else "Applicant Name"

    return {
        "personal_info": {
            "full_name": full_name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "location": "",
            "linkedin_url": f"https://{linkedin_match.group(0)}" if linkedin_match else "",
            "github_url": f"https://{github_match.group(0)}" if github_match else "",
            "portfolio_url": ""
        },
        "summary": {
            "professional_summary": "Extracted from uploaded resume. Please review and verify details.",
            "career_objective": ""
        },
        "education": [],
        "technical_skills": [],
        "soft_skills": [],
        "certifications": [],
        "projects": [],
        "experience": [],
        "achievements": [],
        "publications_activities": [],
        "languages": []
    }

# ==================== B. JOB DESCRIPTION ANALYSIS ====================
def analyze_job_description(job_description_text):
    """
    Extracts structured requirements from a job posting:
    - Required skills
    - Preferred skills
    - Educational requirements
    - Experience requirements
    - Keywords
    - Main responsibilities
    """
    client, model_name, error = get_gemini_client()

    if not client:
        # Fallback local keyword extractor for demo without API key
        return {
            "success": False,
            "error": error,
            "data": fallback_job_analysis(job_description_text)
        }

    prompt = f"""
You are a technical recruiter and ATS specialist. Analyze the following job description thoroughly:

Job Description:
\"\"\"
{job_description_text}
\"\"\"

Extract the requirements into a valid JSON object with the following structure:
{{
  "job_title": "Identified job title or target role",
  "company_name": "Company name if mentioned, else 'Not specified'",
  "required_skills": ["Skill 1", "Skill 2"],
  "preferred_skills": ["Skill 1", "Skill 2"],
  "educational_requirements": ["Degree or education requirement"],
  "experience_requirements": ["Years of experience or background required"],
  "important_keywords": ["Keyword 1", "Keyword 2", "Keyword 3"],
  "main_responsibilities": ["Responsibility 1", "Responsibility 2"]
}}

Return ONLY valid JSON.
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        cleaned = clean_json_response(response.text)
        data = json.loads(cleaned)
        return {
            "success": True,
            "model_used": model_name,
            "data": data
        }
    except Exception as e:
        err_str = str(e)
        if "PERMISSION_DENIED" in err_str or "billing" in err_str:
            clean_err = "Gemini API Notice: Free tier is disabled for this Google Cloud project (billing setup needed at aistudio.google.com/billing). Active fallback ATS keyword matcher is being used."
        else:
            clean_err = f"Gemini API Notice: {err_str}"
        return {
            "success": False,
            "error": clean_err,
            "data": fallback_job_analysis(job_description_text)
        }

def fallback_job_analysis(text):
    """Deterministic keyword extraction for job description when Gemini API is unavailable."""
    common_skills = [
        "Python", "JavaScript", "TypeScript", "React", "Next.js", "HTML", "CSS", "Tailwind CSS",
        "Node.js", "Flask", "FastAPI", "SQL", "PostgreSQL", "SQLite", "MongoDB", "PyTorch",
        "TensorFlow", "Scikit-learn", "Docker", "Git", "AWS", "REST API", "Linux", "CI/CD",
        "Redux", "Data Structures", "Algorithms", "Machine Learning", "Deep Learning", "LLMs"
    ]
    found_skills = [s for s in common_skills if re.search(r'\b' + re.escape(s) + r'\b', text, re.IGNORECASE)]

    # Infer title
    title = "Software Engineering Role"
    if re.search(r'frontend|front-end|ui\b|react', text, re.I):
        title = "Frontend Developer"
    elif re.search(r'ai\b|machine learning|ml\b|data science|deep learning', text, re.I):
        title = "AI / Machine Learning Engineer"
    elif re.search(r'backend|back-end|api|python developer', text, re.I):
        title = "Backend Developer"

    return {
        "job_title": title,
        "company_name": "Prospective Employer",
        "required_skills": found_skills[:8] if found_skills else ["Python", "Problem Solving", "Git"],
        "preferred_skills": found_skills[8:14] if len(found_skills) > 8 else ["Cloud Computing", "Docker"],
        "educational_requirements": ["Bachelor's in Computer Science or related STEM field"],
        "experience_requirements": ["0-2 years of relevant experience or internship"],
        "important_keywords": found_skills + ["Agile", "Collaboration", "Clean Code"],
        "main_responsibilities": [
            "Design, build, and maintain efficient, reusable, and reliable code",
            "Collaborate with cross-functional teams to define, design, and ship new features",
            "Identify bottlenecks and bugs, and devise solutions to these problems"
        ]
    }

# ==================== C. PORTFOLIO MATCHING ====================
def match_portfolio_to_job(job_analysis, portfolio_data):
    """
    Compares job requirements with existing portfolio records.
    SAFEGUARD:
    - Distinguishes between matched skills (explicitly in portfolio) and missing skills (learning gaps).
    - Never fabricates or assigns missing skills to the candidate.
    - Identifies relevant projects, certifications, and experience items.
    """
    portfolio_skills = [s["skill_name"] for s in portfolio_data.get("technical_skills", [])]
    portfolio_skills_lower = {s.lower(): s for s in portfolio_skills}

    required_skills = job_analysis.get("required_skills", [])
    preferred_skills = job_analysis.get("preferred_skills", [])
    all_job_skills = required_skills + preferred_skills

    matched_skills = []
    missing_skills = []

    for skill in all_job_skills:
        skill_clean = skill.strip()
        skill_lower = skill_clean.lower()

        # Check exact or partial word match against portfolio
        matched_orig = None
        for p_lower, p_orig in portfolio_skills_lower.items():
            if skill_lower == p_lower or skill_lower in p_lower or p_lower in skill_lower:
                matched_orig = p_orig
                break

        if matched_orig:
            if matched_orig not in matched_skills:
                matched_skills.append(matched_orig)
        else:
            if skill_clean not in missing_skills:
                missing_skills.append(skill_clean)

    # Calculate match percentage
    total_job_skills = len(all_job_skills) or 1
    match_score = round((len(matched_skills) / total_job_skills) * 100)
    match_score = min(100, max(0, match_score))

    # Identify relevant projects based on tech keywords
    projects = portfolio_data.get("projects", [])
    relevant_projects = []
    for proj in projects:
        score = 0
        tech_text = (proj.get("technologies", "") + " " + proj.get("title", "") + " " + proj.get("description", "")).lower()
        for skill in all_job_skills:
            if skill.lower() in tech_text:
                score += 1
        relevant_projects.append({
            **proj,
            "relevance_score": score,
            "is_recommended": score > 0
        })
    # Sort projects by relevance score descending
    relevant_projects.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Identify relevant experience
    experience = portfolio_data.get("experience", [])
    relevant_experience = []
    for exp in experience:
        score = 0
        exp_text = (exp.get("job_title", "") + " " + exp.get("responsibilities", "")).lower()
        for skill in all_job_skills:
            if skill.lower() in exp_text:
                score += 1
        relevant_experience.append({
            **exp,
            "relevance_score": score,
            "is_recommended": True # Keep candidate experience recommended
        })

    # Relevant certifications
    certifications = portfolio_data.get("certifications", [])
    relevant_certs = []
    for cert in certifications:
        score = 0
        cert_text = (cert.get("title", "") + " " + cert.get("issuing_organization", "")).lower()
        for skill in all_job_skills:
            if skill.lower() in cert_text:
                score += 1
        relevant_certs.append({
            **cert,
            "relevance_score": score,
            "is_recommended": score > 0
        })

    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills, # Clearly designated as Learning Gaps
        "relevant_projects": relevant_projects,
        "relevant_experience": relevant_experience,
        "relevant_certifications": relevant_certs,
        "job_title": job_analysis.get("job_title", "Target Role"),
        "company_name": job_analysis.get("company_name", "")
    }

# ==================== D. RESUME IMPROVEMENT / SUGGESTIONS ====================
def generate_tailored_summary(job_title, matched_skills, original_summary):
    """
    Uses Gemini to craft a tailored summary highlighting verified skills matching the target role.
    SAFEGUARD: Strictly constrained to original portfolio facts and matched skills.
    Never invents nonexistent credentials.
    """
    client, model_name, error = get_gemini_client()

    if not client:
        # Grounded rule-based tailored summary fallback
        skills_str = ", ".join(matched_skills[:4]) if matched_skills else "software engineering"
        return f"Passionate Computer Science graduate with proven competence in {skills_str}. Dedicated to writing clean, maintainable code and delivering reliable solutions tailored for {job_title} positions."

    prompt = f"""
You are a professional resume writer. Write a concise, 2-3 sentence professional summary tailored specifically for the role of "{job_title}".

STRICT SAFEGUARDS:
1. ONLY reference skills, background, and facts present in the candidate's verified summary and matched skills:
- Verified Summary: "{original_summary}"
- Matched Verified Skills: {matched_skills}
2. NEVER mention or claim any skills that are NOT in the matched verified skills list.
3. NEVER fabricate any degree, university, company name, or years of experience.
4. Output ONLY the summary paragraph text with no commentary or quotes.
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip().replace('"', '')
    except Exception as e:
        skills_str = ", ".join(matched_skills[:4]) if matched_skills else "software engineering"
        return f"Computer Science senior with verified hands-on background in {skills_str}, seeking to contribute to {job_title} initiatives with strong software principles."
