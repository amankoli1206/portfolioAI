import os
import json
from datetime import datetime
from dotenv import load_dotenv
import database

load_dotenv()

# Google Sheets scopes required
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_google_credentials_info():
    """
    Checks if Google Service Account credentials are provided.
    Returns (creds_source, error_message)
    creds_source can be a filepath (str) or parsed dictionary.
    """
    json_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    json_string = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

    if json_string:
        try:
            creds_dict = json.loads(json_string)
            return creds_dict, None
        except Exception as e:
            return None, f"Invalid GOOGLE_SERVICE_ACCOUNT_JSON format: {str(e)}"

    # Check file path
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                creds_dict = json.load(f)
                if "client_email" in creds_dict and "private_key" in creds_dict:
                    return json_path, None
                else:
                    return None, f"Credentials file '{json_path}' is missing 'client_email' or 'private_key'."
        except Exception as e:
            return None, f"Failed reading credentials file '{json_path}': {str(e)}"

    return None, f"Service account key file '{json_path}' not found. Please follow the setup instructions to configure Google credentials."

def get_gspread_client():
    """Initializes and returns an authenticated gspread client."""
    creds_info, error = get_google_credentials_info()
    if error:
        return None, error

    try:
        import gspread
        if isinstance(creds_info, dict):
            client = gspread.service_account_from_dict(creds_info, scopes=SCOPES)
        else:
            client = gspread.service_account(filename=creds_info, scopes=SCOPES)
        return client, None
    except Exception as e:
        return None, f"Google authentication failed: {str(e)}"

def format_sheet_headers(worksheet, headers):
    """Writes styled header row."""
    worksheet.update(values=[headers], range_name='A1')
    try:
        worksheet.format('A1:Z1', {
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}},
            'backgroundColor': {'red': 0.12, 'green': 0.25, 'blue': 0.69}, # Navy blue
            'horizontalAlignment': 'CENTER'
        })
    except Exception:
        pass # Formatting is best-effort

def sync_portfolio_to_google_sheets():
    """
    Exports and synchronizes all SQLite portfolio records to a Google Spreadsheet.
    Maintains separate worksheet tabs for each category.
    Uses stable record IDs to prevent duplicates.
    Keeps SQLite as the primary source of truth.
    """
    client, auth_error = get_gspread_client()
    if auth_error:
        database.update_sheets_sync_state("Failed", auth_error)
        return {
            "success": False,
            "error": auth_error,
            "requires_setup": True
        }

    try:
        spreadsheet_id = os.getenv("SPREADSHEET_ID", "").strip()
        portfolio_data = database.get_all_portfolio_data()
        personal = portfolio_data.get("personal_info") or {}
        user_name = personal.get("full_name", "User")

        # Open existing or create new spreadsheet
        spreadsheet = None
        if spreadsheet_id:
            try:
                spreadsheet = client.open_by_key(spreadsheet_id)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to open Google Sheet with ID '{spreadsheet_id}': {str(e)}"
                }
        else:
            # Check if we stored a previously created spreadsheet_id in the DB
            state = database.get_sheets_sync_state()
            if state and state.get("spreadsheet_id"):
                try:
                    spreadsheet = client.open_by_key(state["spreadsheet_id"])
                except Exception:
                    spreadsheet = None

            if not spreadsheet:
                # Create a new spreadsheet
                title = f"PortfolioAI Master Database - {user_name}"
                spreadsheet = client.create(title)
                # Share with user email if available
                user_email = personal.get("email")
                if user_email and "@" in user_email and "example.com" not in user_email:
                    try:
                        spreadsheet.share(user_email, perm_type='user', role='writer')
                    except Exception:
                        pass

        # Worksheet tab definitions: (Tab Name, Headers, Row Data Generator)
        tabs_config = [
            (
                "Personal Information",
                ["Record ID", "Full Name", "Email", "Phone", "Location", "LinkedIn", "GitHub", "Portfolio URL", "Last Updated"],
                lambda: [[
                    1,
                    personal.get("full_name", ""),
                    personal.get("email", ""),
                    personal.get("phone", ""),
                    personal.get("location", ""),
                    personal.get("linkedin_url", ""),
                    personal.get("github_url", ""),
                    personal.get("portfolio_url", ""),
                    personal.get("updated_at", "")
                ]] if personal else []
            ),
            (
                "Education",
                ["Record ID", "Institution", "Degree", "Field of Study", "Start Date", "End Date", "GPA / Grade", "Location", "Description", "Last Updated"],
                lambda: [[
                    edu.get("id"),
                    edu.get("institution", ""),
                    edu.get("degree", ""),
                    edu.get("field_of_study", ""),
                    edu.get("start_date", ""),
                    edu.get("end_date", ""),
                    edu.get("gpa_or_grade", ""),
                    edu.get("location", ""),
                    edu.get("description", ""),
                    edu.get("updated_at", "")
                ] for edu in portfolio_data.get("education", [])]
            ),
            (
                "Technical Skills",
                ["Record ID", "Category", "Skill Name", "Proficiency Level", "Years of Experience", "Last Updated"],
                lambda: [[
                    s.get("id"),
                    s.get("category", ""),
                    s.get("skill_name", ""),
                    s.get("proficiency_level", ""),
                    s.get("years_of_experience", ""),
                    s.get("updated_at", "")
                ] for s in portfolio_data.get("technical_skills", [])]
            ),
            (
                "Soft Skills",
                ["Record ID", "Skill Name", "Category", "Description", "Last Updated"],
                lambda: [[
                    s.get("id"),
                    s.get("skill_name", ""),
                    s.get("category", ""),
                    s.get("description", ""),
                    s.get("updated_at", "")
                ] for s in portfolio_data.get("soft_skills", [])]
            ),
            (
                "Projects",
                ["Record ID", "Project Title", "Role", "Technologies", "Start Date", "End Date", "GitHub URL", "Live Demo URL", "Description", "Highlights", "Last Updated"],
                lambda: [[
                    p.get("id"),
                    p.get("title", ""),
                    p.get("role", ""),
                    p.get("technologies", ""),
                    p.get("start_date", ""),
                    p.get("end_date", ""),
                    p.get("github_url", ""),
                    p.get("live_url", ""),
                    p.get("description", ""),
                    p.get("highlights", ""),
                    p.get("updated_at", "")
                ] for p in portfolio_data.get("projects", [])]
            ),
            (
                "Certifications",
                ["Record ID", "Certification Title", "Issuing Organization", "Issue Date", "Expiration Date", "Credential ID", "Credential URL", "Last Updated"],
                lambda: [[
                    c.get("id"),
                    c.get("title", ""),
                    c.get("issuing_organization", ""),
                    c.get("issue_date", ""),
                    c.get("expiration_date", ""),
                    c.get("credential_id", ""),
                    c.get("credential_url", ""),
                    c.get("updated_at", "")
                ] for c in portfolio_data.get("certifications", [])]
            ),
            (
                "Experience",
                ["Record ID", "Job Title", "Company Name", "Employment Type", "Location", "Start Date", "End Date", "Currently Working", "Responsibilities", "Key Achievements", "Last Updated"],
                lambda: [[
                    e.get("id"),
                    e.get("job_title", ""),
                    e.get("company_name", ""),
                    e.get("employment_type", ""),
                    e.get("location", ""),
                    e.get("start_date", ""),
                    e.get("end_date", ""),
                    "Yes" if e.get("is_current") else "No",
                    e.get("responsibilities", ""),
                    e.get("achievements", ""),
                    e.get("updated_at", "")
                ] for e in portfolio_data.get("experience", [])]
            ),
            (
                "Achievements",
                ["Record ID", "Award / Achievement Title", "Issuer / Organization", "Date Received", "Description", "Last Updated"],
                lambda: [[
                    a.get("id"),
                    a.get("title", ""),
                    a.get("issuer", ""),
                    a.get("date_received", ""),
                    a.get("description", ""),
                    a.get("updated_at", "")
                ] for a in portfolio_data.get("achievements", [])]
            ),
            (
                "Publications & Activities",
                ["Record ID", "Title", "Activity Type", "Organization / Venue", "Date / Duration", "URL", "Description", "Last Updated"],
                lambda: [[
                    pub.get("id"),
                    pub.get("title", ""),
                    pub.get("activity_type", ""),
                    pub.get("organization_or_venue", ""),
                    pub.get("date_or_duration", ""),
                    pub.get("url", ""),
                    pub.get("description", ""),
                    pub.get("updated_at", "")
                ] for pub in portfolio_data.get("publications_activities", [])]
            ),
            (
                "Languages & Competencies",
                ["Record ID", "Language", "Proficiency Level", "Certifications", "Last Updated"],
                lambda: [[
                    lang.get("id"),
                    lang.get("language_name", ""),
                    lang.get("proficiency", ""),
                    lang.get("certifications", ""),
                    lang.get("updated_at", "")
                ] for lang in portfolio_data.get("languages", [])]
            )
        ]

        total_records_synced = 0
        existing_worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}

        for tab_title, headers, data_generator in tabs_config:
            rows = data_generator()
            total_records_synced += len(rows)

            if tab_title in existing_worksheets:
                ws = existing_worksheets[tab_title]
            else:
                ws = spreadsheet.add_worksheet(title=tab_title, rows=max(100, len(rows) + 10), cols=len(headers) + 2)

            # Clear old rows and rewrite fresh clean synchronized table
            ws.clear()
            # Combine headers and rows
            all_values = [headers] + rows
            ws.update(values=all_values, range_name='A1')
            format_sheet_headers(ws, headers)

        # Remove default 'Sheet1' if present and we created custom tabs
        if "Sheet1" in existing_worksheets and len(spreadsheet.worksheets()) > 1:
            try:
                spreadsheet.del_worksheet(existing_worksheets["Sheet1"])
            except Exception:
                pass

        spreadsheet_url = spreadsheet.url
        spreadsheet_id = spreadsheet.id

        # Update SQLite sync state
        success_msg = f"Successfully synchronized {total_records_synced} records across 10 category tabs."
        database.update_sheets_sync_state(
            status="Success",
            message=success_msg,
            url=spreadsheet_url,
            count=total_records_synced,
            spreadsheet_id=spreadsheet_id
        )

        return {
            "success": True,
            "spreadsheet_url": spreadsheet_url,
            "spreadsheet_id": spreadsheet_id,
            "records_synced": total_records_synced,
            "message": success_msg,
            "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        error_msg = f"Google Sheets sync error: {str(e)}"
        database.update_sheets_sync_state("Failed", error_msg)
        return {
            "success": False,
            "error": error_msg
        }

def export_portfolio_to_workbook(output_path=None):
    """
    Generates a 10-tab spreadsheet workbook (.xlsx) directly compatible with Google Sheets & Excel.
    Allows instant one-click download and import into Google Sheets with 0 setup required.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    if not output_path:
        exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated_resumes')
        os.makedirs(exports_dir, exist_ok=True)
        output_path = os.path.join(exports_dir, 'PortfolioAI_Master_Database.xlsx')

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    portfolio_data = database.get_all_portfolio_data()
    personal = portfolio_data.get("personal_info") or {}

    tabs_config = [
        (
            "Personal Information",
            ["Record ID", "Full Name", "Email", "Phone", "Location", "LinkedIn", "GitHub", "Portfolio URL", "Last Updated"],
            [[
                1, personal.get("full_name", ""), personal.get("email", ""), personal.get("phone", ""),
                personal.get("location", ""), personal.get("linkedin_url", ""), personal.get("github_url", ""),
                personal.get("portfolio_url", ""), personal.get("updated_at", "")
            ]] if personal else []
        ),
        (
            "Education",
            ["Record ID", "Institution", "Degree", "Field of Study", "Start Date", "End Date", "GPA / Grade", "Location", "Description", "Last Updated"],
            [[
                edu.get("id"), edu.get("institution", ""), edu.get("degree", ""), edu.get("field_of_study", ""),
                edu.get("start_date", ""), edu.get("end_date", ""), edu.get("gpa_or_grade", ""), edu.get("location", ""),
                edu.get("description", ""), edu.get("updated_at", "")
            ] for edu in portfolio_data.get("education", [])]
        ),
        (
            "Technical Skills",
            ["Record ID", "Category", "Skill Name", "Proficiency Level", "Years Experience", "Last Updated"],
            [[
                s.get("id"), s.get("category", ""), s.get("skill_name", ""), s.get("proficiency_level", ""),
                s.get("years_of_experience", ""), s.get("updated_at", "")
            ] for s in portfolio_data.get("technical_skills", [])]
        ),
        (
            "Soft Skills",
            ["Record ID", "Skill Name", "Category", "Description", "Last Updated"],
            [[
                s.get("id"), s.get("skill_name", ""), s.get("category", ""), s.get("description", ""), s.get("updated_at", "")
            ] for s in portfolio_data.get("soft_skills", [])]
        ),
        (
            "Projects",
            ["Record ID", "Project Title", "Role", "Technologies", "Start Date", "End Date", "GitHub URL", "Live Demo URL", "Description", "Highlights", "Last Updated"],
            [[
                p.get("id"), p.get("title", ""), p.get("role", ""), p.get("technologies", ""),
                p.get("start_date", ""), p.get("end_date", ""), p.get("github_url", ""), p.get("live_url", ""),
                p.get("description", ""), p.get("highlights", ""), p.get("updated_at", "")
            ] for p in portfolio_data.get("projects", [])]
        ),
        (
            "Certifications",
            ["Record ID", "Certification Title", "Issuing Organization", "Issue Date", "Expiration Date", "Credential ID", "Credential URL", "Last Updated"],
            [[
                c.get("id"), c.get("title", ""), c.get("issuing_organization", ""), c.get("issue_date", ""),
                c.get("expiration_date", ""), c.get("credential_id", ""), c.get("credential_url", ""), c.get("updated_at", "")
            ] for c in portfolio_data.get("certifications", [])]
        ),
        (
            "Experience",
            ["Record ID", "Job Title", "Company Name", "Employment Type", "Location", "Start Date", "End Date", "Currently Working", "Responsibilities", "Key Achievements", "Last Updated"],
            [[
                e.get("id"), e.get("job_title", ""), e.get("company_name", ""), e.get("employment_type", ""),
                e.get("location", ""), e.get("start_date", ""), e.get("end_date", ""), "Yes" if e.get("is_current") else "No",
                e.get("responsibilities", ""), e.get("achievements", ""), e.get("updated_at", "")
            ] for e in portfolio_data.get("experience", [])]
        ),
        (
            "Achievements",
            ["Record ID", "Award / Achievement Title", "Issuer / Organization", "Date Received", "Description", "Last Updated"],
            [[
                a.get("id"), a.get("title", ""), a.get("issuer", ""), a.get("date_received", ""),
                a.get("description", ""), a.get("updated_at", "")
            ] for a in portfolio_data.get("achievements", [])]
        ),
        (
            "Publications & Activities",
            ["Record ID", "Title", "Activity Type", "Organization / Venue", "Date / Duration", "URL", "Description", "Last Updated"],
            [[
                pub.get("id"), pub.get("title", ""), pub.get("activity_type", ""), pub.get("organization_or_venue", ""),
                pub.get("date_or_duration", ""), pub.get("url", ""), pub.get("description", ""), pub.get("updated_at", "")
            ] for pub in portfolio_data.get("publications_activities", [])]
        ),
        (
            "Languages & Competencies",
            ["Record ID", "Language", "Proficiency Level", "Certifications", "Last Updated"],
            [[
                lang.get("id"), lang.get("language_name", ""), lang.get("proficiency", ""),
                lang.get("certifications", ""), lang.get("updated_at", "")
            ] for lang in portfolio_data.get("languages", [])]
        )
    ]

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="007AFF", end_color="007AFF", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    for tab_name, headers, rows in tabs_config:
        ws = wb.create_sheet(title=tab_name)
        ws.append(headers)

        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        for row in rows:
            ws.append(row)

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

    wb.save(output_path)
    return output_path
