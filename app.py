from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, send_file
import os
import sqlite3
import time
import re
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from resume_parser import ResumeParserService
from cossimilarity import SimilarityCalculator
from matching import MatchingService
from interview_scheduler import InterviewScheduler
from password import send_otp, generate_candidate_id, store_candidate_data

app = Flask(
    __name__,
    template_folder=r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\Frontend\Templates",
    static_folder=r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\Frontend\Static"
)

limiter = Limiter(app=app, key_func=get_remote_address)

otp_storage = {}
DB_PATH = r"C:\Users\Sudhindra Prakash\Desktop\java project\.venv\Backend\DRDO_Normalized_Updated_Names.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Interviewee (
                    interviewee_id TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    phone TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Interviewer (
                    interviewer_id TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    phone TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Interviewee_Interests (
                    id INTEGER PRIMARY KEY,
                    interviewee_id TEXT,
                    field_of_interest TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Interviewer_Expertise (
                    id INTEGER PRIMARY KEY,
                    interviewer_id TEXT,
                    expertise_field TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interview_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Interviewer_ID TEXT,
                    Interviewee_ID TEXT,
                    date TEXT,
                    time TEXT
                )
            """)
            conn.commit()
        print("✅ Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"❌ Error initializing database: {e}")

init_db()

def validate_phone_number(phone_number):
    pattern = r'^\d{10}$'
    return bool(re.match(pattern, phone_number))

def validate_user_id(role, user_id):
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            if role == 'candidate':
                cursor.execute("SELECT 1 FROM Interviewee WHERE interviewee_id = ?", (user_id,))
            elif role == 'expert':
                cursor.execute("SELECT 1 FROM Interviewer WHERE interviewer_id = ?", (user_id,))
            result = cursor.fetchone()
        return result is not None
    except sqlite3.Error as e:
        print(f"❌ Error validating user ID: {e}")
        return False

@app.route('/')
def home():
    return render_template('DRDO1.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        user_id = request.form.get('user_id')
        phone_number = request.form.get('phone_number')

        if role not in ['expert', 'candidate']:
            return "Invalid role", 400

        if not user_id or not validate_user_id(role, user_id):
            return "Invalid user ID. Please ensure the ID exists in the system.", 400

        if not validate_phone_number(phone_number):
            return "Invalid phone number. Must be 10 digits.", 400

        print(f"Attempting to send OTP to {phone_number} for role {role}")
        response = send_otp(phone_number, role)
        if not response.get("return", False):
            error_message = response.get('message', 'Unknown error')
            print(f"❌ Failed to send OTP: {error_message}")
            return render_template('login.html', error=f"Failed to send OTP: {error_message}")

        otp_storage[phone_number] = {"otp": response.get("otp"), "timestamp": time.time()}
        print(f"✅ OTP sent successfully, redirecting to verify_otp")
        return redirect(url_for('verify_otp', role=role, user_id=user_id, phone_number=phone_number))

    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    phone_number = request.args.get('phone_number')
    role = request.args.get('role')
    user_id = request.args.get('user_id')

    if not all([phone_number, role, user_id]):
        return "Missing required parameters", 400

    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if not user_otp or not user_otp.isdigit():
            return "Invalid OTP format", 400

        otp_data = otp_storage.get(phone_number)
        if not otp_data:
            return "OTP not found", 400

        stored_otp = otp_data["otp"]
        timestamp = otp_data["timestamp"]
        if time.time() - timestamp > 300:
            del otp_storage[phone_number]
            return "OTP expired", 400

        if int(user_otp) == stored_otp:
            del otp_storage[phone_number]
            print(f"✅ OTP verified for {phone_number}, redirecting to {role}_dashboard")
            return redirect(url_for(f'{role}_dashboard', user_id=user_id))
        else:
            return "Invalid OTP", 400

    return render_template('otp.html', role=role, user_id=user_id, phone_number=phone_number)

@app.route('/expert_dashboard')
def expert_dashboard():
    user_id = request.args.get('user_id')
    if not user_id:
        return "Invalid user ID", 400
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.Interviewer_ID, s.Interviewee_ID, s.date, s.time, 
                       s.Interviewer_Email, s.Interviewee_Email,
                       i.name AS interviewee_name
                FROM interview_schedule s
                JOIN Interviewee i ON s.Interviewee_ID = i.interviewee_id
                WHERE s.Interviewer_ID = ?
            """, (user_id,))
            schedule = cursor.fetchall()
        print(f"✅ Loaded schedule for expert {user_id}: {len(schedule)} entries")

        cosine_scores = SimilarityCalculator.compute_similarity()
        matching_scores = MatchingService.compute_matching_scores()
        user_cosine_scores = {pair: score for pair, score in cosine_scores.items() if pair[1] == user_id}
        user_matching_scores = {pair: score for pair, score in matching_scores.items() if pair[1] == user_id}

        schedule_data = []
        for row in schedule:
            interviewee_id = row[1]  # Interviewee_ID
            schedule_data.append({
                "interviewer_id": row[0],  # Interviewer_ID
                "interviewee_id": interviewee_id,
                "date": row[2],  # date
                "time": row[3],  # time
                "interviewer_email": row[4],  # Interviewer_Email
                "interviewee_email": row[5],  # Interviewee_Email
                "interviewee_name": row[6],  # Actual name from Interviewee table
                "cosine_score": user_cosine_scores.get((interviewee_id, user_id), 0),
                "matching_score": user_matching_scores.get((interviewee_id, user_id), 0)
            })

        return render_template('Expert_Dashboard.html', schedule=schedule_data, user_id=user_id)
    except sqlite3.Error as e:
        print(f"❌ Error loading expert dashboard: {e}")
        return "Database error", 500

@app.route('/candidate_dashboard')
def candidate_dashboard():
    user_id = request.args.get('user_id')
    if not user_id:
        return "Invalid user ID", 400
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.Interviewer_ID, s.Interviewee_ID, s.date, s.time, 
                       i.name AS interviewer_name, i.email AS interviewer_email
                FROM interview_schedule s
                JOIN Interviewer i ON s.Interviewer_ID = i.interviewer_id
                WHERE s.Interviewee_ID = ?
            """, (user_id,))
            schedule = cursor.fetchall()

        cosine_scores = SimilarityCalculator.compute_similarity()
        matching_scores = MatchingService.compute_matching_scores()

        schedule_data = []
        for row in schedule:
            interviewer_id = row[0]
            cosine_score = cosine_scores.get((user_id, interviewer_id), 0)
            matching_score = matching_scores.get((user_id, interviewer_id), 0)
            schedule_data.append({
                "interviewer_id": interviewer_id,
                "interviewee_id": row[1],
                "date": row[2],
                "time": row[3],
                "interviewer_name": row[4],
                "interviewer_email": row[5],
                "cosine_score": cosine_score,
                "matching_score": matching_score
            })

        print(f"✅ Loaded schedule for candidate {user_id}: {len(schedule)} entries")
        return render_template('Interviewee_dashboard.html', schedule=schedule_data, user_id=user_id)
    except sqlite3.Error as e:
        print(f"❌ Error loading candidate dashboard: {e}")
        return "Database error", 500

@app.route('/candidate_signup', methods=['GET', 'POST'])
def candidate_signup():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        resume = request.files.get('resume')

        if not (phone_number and resume):
            return "Missing required fields", 400

        if not validate_phone_number(phone_number):
            return "Invalid phone number", 400

        user_id = generate_candidate_id()
        filename = secure_filename(resume.filename)
        timestamp = int(time.time())
        file_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_{timestamp}_{filename}")
        resume.save(file_path)

        try:
            print(f"✅ Parsing resume at path: {file_path}")
            parsed_data = ResumeParserService.parse_resume(file_path)

            name = parsed_data.get("name", "Candidate")
            email = parsed_data.get("email", "unknown@example.com")
            age = parsed_data.get("age", 25)
            experience = parsed_data.get("experience", 0)
            gate_score = parsed_data.get("gate_score", 0)
            core_field = parsed_data.get("core_field", "General")

            print(f"✅ Extracted data: Name={name}, Email={email}, Gate={gate_score}, Core Field={core_field}")

            if gate_score < 1150:
                return render_template(
                    'application_result.html',
                    result="not_eligible",
                    message="Your GATE score does not meet the minimum requirement of 1150 for DRDO.",
                    gate_score=gate_score
                )

            store_candidate_data(user_id, name, email, phone_number, age, experience, gate_score, core_field)
            return render_template(
                'application_result.html',
                result="success",
                message=f"Your application has been successfully submitted! Your candidate ID is {user_id}. Please note this ID for login.",
                candidate_id=user_id
            )

        except sqlite3.Error as e:
            print(f"❌ SQLite error during signup: {e}")
            return render_template(
                'application_result.html',
                result="error",
                message="Database error: Unable to store your data. Please try again later."
            )
        except Exception as e:
            print(f"❌ Error processing resume: {e}")
            return render_template(
                'application_result.html',
                result="error",
                message="There was an error processing your resume. Please ensure it's a valid PDF with all required information."
            )

    return render_template('candidate_signup.html')

@app.route('/compute_schedule', methods=['POST'])
def compute_schedule():
    try:
        similarity_scores = SimilarityCalculator.compute_similarity()
        matching_scores = MatchingService.compute_matching_scores()
        scheduler = InterviewScheduler()
        scheduler.generate_schedule()
        scheduler.store_schedule_in_db()
        print(f"✅ Schedule computed and stored: {len(scheduler.schedule)} interviews")
        return jsonify({"message": "Schedule computed successfully"}), 200
    except Exception as e:
        print(f"❌ Error computing schedule: {e}")
        return jsonify({"message": "Error computing schedule"}), 500

@app.route('/generate_resume', methods=['GET'])
def generate_resume():
    try:
        filename = "prakash.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        ResumeParserService.create_resume_pdf(filename=file_path)
        return send_file(file_path, as_attachment=True, download_name="prakash.pdf")
    except Exception as e:
        print(f"❌ Error generating resume: {e}")
        return jsonify({"message": "Error generating resume"}), 500

if __name__ == '__main__':
    init_db()
    scheduler = InterviewScheduler()
    scheduler.generate_schedule()
    scheduler.store_schedule_in_db()
    app.run(debug=True, host='0.0.0.0', port=5000)