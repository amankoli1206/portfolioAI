import os
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

GENERATED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_resumes')
os.makedirs(GENERATED_DIR, exist_ok=True)

def sanitize_text(text):
    """Escapes XML entities for ReportLab Paragraphs."""
    if not text:
        return ""
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def build_pdf_resume(resume_data, template_name='modern_ats', output_filename=None):
    """
    Generates a professional, ATS-friendly PDF resume using ReportLab.
    
    resume_data: dict containing:
      - personal_info: {full_name, email, phone, location, linkedin_url, github_url, portfolio_url}
      - summary_text: string
      - target_role: string
      - education: list of dicts
      - technical_skills: list of dicts or list of strings
      - experience: list of dicts
      - projects: list of dicts
      - certifications: list of dicts
      - achievements: list of dicts
      - languages: list of dicts
    """
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_role = re.sub(r'[^a-zA-Z0-9]', '_', resume_data.get("target_role", "Resume"))
        output_filename = f"Resume_{sanitized_role}_{timestamp}.pdf"

    output_path = os.path.join(GENERATED_DIR, output_filename)

    # Document margins: 0.5 inch (ATS standard)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    # Palette selection based on template
    if template_name == 'classic_executive':
        primary_color = colors.HexColor('#1f2937')   # Slate dark
        secondary_color = colors.HexColor('#4b5563') # Slate gray
        divider_color = colors.HexColor('#d1d5db')
        header_align = 1 # Center
    elif template_name == 'minimal_tech':
        primary_color = colors.HexColor('#0f766e')   # Deep Teal
        secondary_color = colors.HexColor('#374151') # Charcoal
        divider_color = colors.HexColor('#14b8a6')
        header_align = 0 # Left
    else: # modern_ats (Default)
        primary_color = colors.HexColor('#1e40af')   # Royal Navy Blue
        secondary_color = colors.HexColor('#334155') # Slate
        divider_color = colors.HexColor('#2563eb')
        header_align = 0 # Left

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_name = ParagraphStyle(
        'ResumeName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=header_align
    )

    style_target_role = ParagraphStyle(
        'ResumeTargetRole',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=secondary_color,
        alignment=header_align
    )

    style_contact = ParagraphStyle(
        'ResumeContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=header_align
    )

    style_section_heading = ParagraphStyle(
        'ResumeSection',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True
    )

    style_item_title = ParagraphStyle(
        'ResumeItemTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    style_item_subtitle = ParagraphStyle(
        'ResumeItemSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=11.5,
        textColor=colors.HexColor('#334155')
    )

    style_date_loc = ParagraphStyle(
        'ResumeDateLoc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        alignment=2, # Right align
        textColor=colors.HexColor('#64748b')
    )

    style_body = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1e293b')
    )

    style_bullet = ParagraphStyle(
        'ResumeBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        leftIndent=12,
        firstLineIndent=-8,
        textColor=colors.HexColor('#1e293b')
    )

    elements = []

    # 1. Header (Name, Target Role, Contact Links)
    personal = resume_data.get("personal_info") or {}
    full_name = sanitize_text(personal.get("full_name", "Portfolio Candidate"))
    elements.append(Paragraph(full_name, style_name))

    target_role = sanitize_text(resume_data.get("target_role", ""))
    if target_role:
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(target_role.upper(), style_target_role))

    # Contact line with clickable email & links
    contact_parts = []
    if personal.get("email"):
        contact_parts.append(f'<a href="mailto:{personal["email"]}"><font color="#2563eb">{sanitize_text(personal["email"])}</font></a>')
    if personal.get("phone"):
        contact_parts.append(sanitize_text(personal["phone"]))
    if personal.get("location"):
        contact_parts.append(sanitize_text(personal["location"]))
    if personal.get("linkedin_url"):
        contact_parts.append(f'<a href="{personal["linkedin_url"]}"><font color="#2563eb">LinkedIn</font></a>')
    if personal.get("github_url"):
        contact_parts.append(f'<a href="{personal["github_url"]}"><font color="#2563eb">GitHub</font></a>')
    if personal.get("portfolio_url"):
        contact_parts.append(f'<a href="{personal["portfolio_url"]}"><font color="#2563eb">Portfolio</font></a>')

    if contact_parts:
        elements.append(Spacer(1, 4))
        contact_line = "  •  ".join(contact_parts)
        elements.append(Paragraph(contact_line, style_contact))

    # Divider bar
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=divider_color, spaceBefore=3, spaceAfter=6))

    # 2. Summary
    summary_text = resume_data.get("summary_text", "").strip()
    if summary_text:
        elements.append(Paragraph("PROFESSIONAL SUMMARY", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))
        elements.append(Paragraph(sanitize_text(summary_text), style_body))
        elements.append(Spacer(1, 4))

    # 3. Technical Skills
    tech_skills = resume_data.get("technical_skills", [])
    if tech_skills:
        elements.append(Paragraph("TECHNICAL SKILLS", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))

        # Group skills by category if dicts, or comma separate if strings
        if isinstance(tech_skills[0], dict):
            categories = {}
            for item in tech_skills:
                cat = item.get("category", "Core Competencies")
                categories.setdefault(cat, []).append(item.get("skill_name", ""))
            
            for cat, items in categories.items():
                items_str = ", ".join(items)
                skill_para = f"<b>{sanitize_text(cat)}:</b> {sanitize_text(items_str)}"
                elements.append(Paragraph(skill_para, style_body))
                elements.append(Spacer(1, 1.5))
        else:
            items_str = ", ".join(tech_skills)
            elements.append(Paragraph(sanitize_text(items_str), style_body))

        elements.append(Spacer(1, 4))

    # 4. Work Experience & Internships
    experience = resume_data.get("experience", [])
    if experience:
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))

        for exp in experience:
            exp_elements = []
            title = sanitize_text(exp.get("job_title", ""))
            company = sanitize_text(exp.get("company_name", ""))
            emp_type = f" ({exp.get('employment_type')})" if exp.get("employment_type") else ""
            date_range = f"{exp.get('start_date', '')} – {'Present' if exp.get('is_current') else exp.get('end_date', '')}"
            loc = sanitize_text(exp.get("location", ""))
            right_text = f"{sanitize_text(date_range)} | {loc}" if loc else sanitize_text(date_range)

            # Two-column layout for Role + Company on left, Date + Location on right
            table_data = [
                [
                    Paragraph(f"<b>{title}</b> — {company}{emp_type}", style_item_title),
                    Paragraph(right_text, style_date_loc)
                ]
            ]
            t = Table(table_data, colWidths=[380, 160])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1)
            ]))
            exp_elements.append(t)

            # Responsibilities as bullet points
            resps = exp.get("responsibilities", "")
            if resps:
                lines = [l.strip().lstrip('•-–* ') for l in resps.split('\n') if l.strip()]
                for line in lines:
                    exp_elements.append(Paragraph(f"• {sanitize_text(line)}", style_bullet))

            # Achievements if present
            ach = exp.get("achievements", "")
            if ach:
                exp_elements.append(Paragraph(f"• <i>Key Result:</i> {sanitize_text(ach)}", style_bullet))

            exp_elements.append(Spacer(1, 4))
            elements.append(KeepTogether(exp_elements))

    # 5. Key Projects
    projects = resume_data.get("projects", [])
    if projects:
        elements.append(Paragraph("PROJECTS", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))

        for proj in projects:
            proj_elements = []
            title = sanitize_text(proj.get("title", ""))
            role = sanitize_text(proj.get("role", ""))
            tech = sanitize_text(proj.get("technologies", ""))
            
            date_range = ""
            if proj.get("start_date") or proj.get("end_date"):
                date_range = f"{proj.get('start_date', '')} – {proj.get('end_date', '')}".strip(" – ")

            left_sub = f"<b>{title}</b>"
            if role:
                left_sub += f" | <i>{role}</i>"
            
            table_data = [
                [
                    Paragraph(left_sub, style_item_title),
                    Paragraph(sanitize_text(date_range), style_date_loc)
                ]
            ]
            t = Table(table_data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1)
            ]))
            proj_elements.append(t)

            if tech:
                proj_elements.append(Paragraph(f"<b>Technologies:</b> {tech}", style_item_subtitle))

            desc = proj.get("description", "")
            if desc:
                proj_elements.append(Paragraph(sanitize_text(desc), style_body))

            highlights = proj.get("highlights", "")
            if highlights:
                lines = [l.strip().lstrip('•-–* ') for l in highlights.split('\n') if l.strip()]
                for line in lines:
                    proj_elements.append(Paragraph(f"• {sanitize_text(line)}", style_bullet))

            proj_elements.append(Spacer(1, 4))
            elements.append(KeepTogether(proj_elements))

    # 6. Education
    education = resume_data.get("education", [])
    if education:
        elements.append(Paragraph("EDUCATION", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))

        for edu in education:
            edu_elements = []
            inst = sanitize_text(edu.get("institution", ""))
            deg = sanitize_text(edu.get("degree", ""))
            field = sanitize_text(edu.get("field_of_study", ""))
            dates = f"{edu.get('start_date', '')} – {edu.get('end_date', '')}".strip(" – ")
            loc = sanitize_text(edu.get("location", ""))
            gpa = sanitize_text(edu.get("gpa_or_grade", ""))

            deg_str = f"<b>{deg} in {field}</b>" if field else f"<b>{deg}</b>"
            right_text = f"{dates} | {loc}" if loc else dates

            table_data = [
                [
                    Paragraph(f"{deg_str} — {inst}", style_item_title),
                    Paragraph(sanitize_text(right_text), style_date_loc)
                ]
            ]
            t = Table(table_data, colWidths=[380, 160])
            t.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 1),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1)
            ]))
            edu_elements.append(t)

            if gpa:
                edu_elements.append(Paragraph(f"<b>GPA:</b> {gpa}", style_body))

            desc = edu.get("description", "")
            if desc:
                edu_elements.append(Paragraph(sanitize_text(desc), style_body))

            edu_elements.append(Spacer(1, 3))
            elements.append(KeepTogether(edu_elements))

    # 7. Certifications
    certifications = resume_data.get("certifications", [])
    if certifications:
        elements.append(Paragraph("CERTIFICATIONS", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))

        for cert in certifications:
            title = sanitize_text(cert.get("title", ""))
            issuer = sanitize_text(cert.get("issuing_organization", ""))
            date = sanitize_text(cert.get("issue_date", ""))
            cred_id = sanitize_text(cert.get("credential_id", ""))
            
            line = f"• <b>{title}</b> — {issuer}"
            if date:
                line += f" ({date})"
            if cred_id:
                line += f" [ID: {cred_id}]"
            elements.append(Paragraph(line, style_body))
            elements.append(Spacer(1, 1.5))
        elements.append(Spacer(1, 3))

    # 8. Achievements / Awards
    achievements = resume_data.get("achievements", [])
    if achievements:
        elements.append(Paragraph("HONORS & ACHIEVEMENTS", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))
        for ach in achievements:
            title = sanitize_text(ach.get("title", ""))
            issuer = sanitize_text(ach.get("issuer", ""))
            desc = sanitize_text(ach.get("description", ""))
            line = f"• <b>{title}</b> ({issuer})"
            if desc:
                line += f": {desc}"
            elements.append(Paragraph(line, style_body))
            elements.append(Spacer(1, 1.5))
        elements.append(Spacer(1, 3))

    # 9. Languages
    languages = resume_data.get("languages", [])
    if languages:
        elements.append(Paragraph("LANGUAGES", style_section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=1, spaceAfter=4))
        lang_parts = []
        for lang in languages:
            name = sanitize_text(lang.get("language_name", ""))
            prof = sanitize_text(lang.get("proficiency", ""))
            lang_parts.append(f"<b>{name}</b> ({prof})" if prof else f"<b>{name}</b>")
        elements.append(Paragraph("  •  ".join(lang_parts), style_body))

    # Build the document
    doc.build(elements)

    return {
        "filename": output_filename,
        "file_path": output_path,
        "relative_path": f"/download-resume/{output_filename}"
    }
