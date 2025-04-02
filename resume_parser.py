import os
import sqlite3
import pdfplumber
import re
from pyresparser import ResumeParser
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class ResumeParserService:
    DB_PATH = r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\Backend\DRDO_Normalized_Updated_Names.db"

    @staticmethod
    def extract_text_from_pdf(file_path):
        try:
            all_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    all_text += text + "\n"
            print(f"Extracted text from PDF: {all_text}")
            return all_text
        except Exception as e:
            print(f"❌ Error extracting text from PDF: {e}")
            return ""

    @staticmethod
    def extract_name(text):
        try:
            # Pattern to match "Name: [some text]" or "Name: some text"
            name_pattern = r'Name\s*:\s*(.+?)(?:\n|$)'
            matches = re.findall(name_pattern, text, re.IGNORECASE)
            if not matches:
                print("⚠️ No name found in the text using regex.")
                return "Unknown"
            # Remove any square brackets if present (e.g., [Your Name] -> Your Name)
            name = matches[0].strip().strip('[]')
            print(f"Extracted name: {name}")
            return name
        except Exception as e:
            print(f"❌ Error extracting name: {e}")
            return "Unknown"

    @staticmethod
    def extract_email(text):
        try:
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, text)
            return emails[0] if emails else "unknown@example.com"
        except Exception as e:
            print(f"❌ Error extracting email: {e}")
            return "unknown@example.com"

    @staticmethod
    def extract_phone(text):
        try:
            phone_pattern = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
            phones = re.findall(phone_pattern, text)
            return phones[0] if phones else "Unknown"
        except Exception as e:
            print(f"❌ Error extracting phone: {e}")
            return "Unknown"

    @staticmethod
    def extract_gate_score(text):
        try:
            gate_pattern = r'GATE\s+Score\s*(?:\n\s*)?Score\s*[:=]\s*(\d{3,4})'
            matches = re.findall(gate_pattern, text, re.IGNORECASE)
            print(f"GATE score matches: {matches}")
            return int(matches[0]) if matches else 0
        except Exception as e:
            print(f"❌ Error extracting GATE score: {e}")
            return 0

    @staticmethod
    def extract_core_field(text):
        try:
            fields = {
                "Aerospace": ["aerospace", "aeronautical", "aviation", "avionics"],
                "Computer Science": ["computer science", "cs", "cse", "information technology", "it"],
                "Electronics": ["electronics", "ece", "eee", "electrical", "communication"],
                "Mechanical": ["mechanical", "mech", "production engineering", "automobile"],
                "Civil": ["civil engineering", "civil", "structural engineering"],
                "Chemical": ["chemical", "chem", "petroleum", "petrochemical"],
                "Biotechnology": ["biotechnology", "biotech", "biomedical", "biochemical"],
                "Physics": ["physics", "applied physics"],
                "Mathematics": ["mathematics", "math", "applied mathematics", "statistics"],
                "Medical": ["medicine", "medical", "mbbs", "md", "surgery"]
            }
            text_lower = text.lower()
            print(f"Text for core field extraction: {text_lower}")
            matched_field = "General Engineering"
            max_specificity = 0  # Track the longest matching keyword for specificity
            for field, keywords in fields.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        specificity = len(keyword.split())  # More words = more specific
                        if specificity > max_specificity:
                            max_specificity = specificity
                            matched_field = field
                            print(f"Matched core field: {field} with keyword: {keyword}")
            return matched_field
        except Exception as e:
            print(f"❌ Error extracting core field: {e}")
            return "General Engineering"

    @staticmethod
    def parse_resume(file_path):
        try:
            full_text = ResumeParserService.extract_text_from_pdf(file_path)
            try:
                parsed_data = ResumeParser(file_path).get_extracted_data()
            except Exception as e:
                print(f"⚠️ pyresparser failed: {e}, using fallback extraction")
                parsed_data = {}

            if not parsed_data.get("name"):
                parsed_data["name"] = ResumeParserService.extract_name(full_text)
            if not parsed_data.get("email"):
                parsed_data["email"] = ResumeParserService.extract_email(full_text)
            if not parsed_data.get("phone"):
                parsed_data["phone"] = ResumeParserService.extract_phone(full_text)
            gate_score = parsed_data.get("gate_score", 0)
            if not gate_score:
                gate_score = ResumeParserService.extract_gate_score(full_text)
            parsed_data["gate_score"] = gate_score
            if not parsed_data.get("core_field"):
                parsed_data["core_field"] = ResumeParserService.extract_core_field(full_text)
            if not parsed_data.get("experience"):
                parsed_data["experience"] = parsed_data.get("total_experience", 0)
            parsed_data["full_text"] = full_text
            return parsed_data
        except Exception as e:
            print(f"❌ Error parsing resume: {e}")
            return {}

    @staticmethod
    def store_resume_data(user_id, file_path, gate_score, parsed_data):
        try:
            name = parsed_data.get("name", "Unknown")
            email = parsed_data.get("email", "Unknown")
            phone = parsed_data.get("phone", "Unknown")
            age = parsed_data.get("age", 0)
            experience = parsed_data.get("experience", 0)
            core_field = parsed_data.get("core_field", "Unknown")

            with sqlite3.connect(ResumeParserService.DB_PATH, timeout=10) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO Interviewee 
                    (interviewee_id, name, email, phone) 
                    VALUES (?, ?, ?, ?)
                """, (user_id, name, email, phone))
                cursor.execute("""
                    INSERT OR REPLACE INTO Interviewee_Interests 
                    (interviewee_id, field_of_interest) 
                    VALUES (?, ?)
                """, (user_id, core_field))
                conn.commit()
            return "✅ Resume data stored successfully."
        except Exception as e:
            print(f"❌ Database error: {e}")
            return f"❌ Database error: {e}"

    @staticmethod
    def create_resume_pdf(filename="prakash.pdf"):
        try:
            output_path = os.path.join(os.getcwd(), filename)
            doc = SimpleDocTemplate(output_path, pagesize=letter,
                                    leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                                    topMargin=1 * inch, bottomMargin=1 * inch)
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            title_style.alignment = 1
            section_style = styles['Heading2']
            body_style = ParagraphStyle(
                'BodyText',
                parent=styles['Normal'],
                fontSize=12,
                leading=14,
                spaceAfter=12
            )
            story = []
            story.append(Paragraph("Resume", title_style))
            story.append(Spacer(1, 0.25 * inch))
            story.append(Paragraph("Personal Information", section_style))
            story.append(Paragraph("Name: R.Prakash", body_style))
            story.append(Paragraph("Email: prakashr00@rediffmail.com", body_style))
            story.append(Paragraph("Phone: 9936528585", body_style))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Education", section_style))
            story.append(Paragraph("B.Tech in Aerospace Engineering", body_style))
            story.append(Paragraph("XYZ University, Graduated: May 2023", body_style))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Field of Interest", section_style))
            story.append(Paragraph("Aerospace Engg (Avionics)", body_style))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("GATE Score", section_style))
            story.append(Paragraph("Score: 1250 (2023)", body_style))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Experience", section_style))
            story.append(Paragraph("Intern, Aerospace Innovations Pvt. Ltd.", body_style))
            story.append(Paragraph("June 2022 - December 2022", body_style))
            story.append(Paragraph("Assisted in the design and testing of avionics systems for aircraft.", body_style))
            doc.build(story)
            print(f"✅ Resume PDF created at: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ Error creating resume PDF: {e}")
            return None