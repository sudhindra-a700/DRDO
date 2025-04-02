from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os


def create_resume_pdf(filename="prakash.pdf"):
    # Define output path
    output_path = os.path.join(os.getcwd(), filename)

    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=1 * inch, bottomMargin=1 * inch)

    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center align
    section_style = styles['Heading2']
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=12
    )

    # Content
    story = []

    # Header
    story.append(Paragraph("Resume", title_style))
    story.append(Spacer(1, 0.25 * inch))

    # Personal Information
    story.append(Paragraph("Personal Information", section_style))
    story.append(Paragraph("Name: R.Prakash", body_style))  # Replace with your name
    story.append(Paragraph("Email: prakashr00@rediffmail.com", body_style))  # Replace with your email
    story.append(Paragraph("Phone: 9936528585", body_style))  # Replace with your phone if needed
    story.append(Spacer(1, 0.2 * inch))

    # Education
    story.append(Paragraph("Education", section_style))
    story.append(Paragraph("B.Tech in Aerospace Engineering", body_style))
    story.append(Paragraph("XYZ University, Graduated: May 2023", body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Field of Interest
    story.append(Paragraph("Field of Interest", section_style))
    story.append(Paragraph("Aerospace Engg (Avionics)", body_style))  # Matches interviewer_id = 1
    story.append(Spacer(1, 0.2 * inch))

    # GATE Score
    story.append(Paragraph("GATE Score", section_style))
    story.append(Paragraph("Score: 1250 (2023)", body_style))  # Eligible score ≥1150
    story.append(Spacer(1, 0.2 * inch))

    # Experience
    story.append(Paragraph("Experience", section_style))
    story.append(Paragraph("Intern, Aerospace Innovations Pvt. Ltd.", body_style))
    story.append(Paragraph("June 2022 - December 2022", body_style))
    story.append(Paragraph("Assisted in the design and testing of avionics systems for aircraft.", body_style))

    # Build PDF
    doc.build(story)
    print(f"✅ Resume PDF created at: {output_path}")
    return output_path


if __name__ == "__main__":
    # Install reportlab if not already installed: pip install reportlab
    pdf_path = create_resume_pdf()
    print(f"Please check your current directory for the file: {pdf_path}")