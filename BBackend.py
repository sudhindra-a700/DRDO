from flask import Flask, request, jsonify
from flask_cors import CORS
from resume_parser import ResumeParserService
from dataload import DataLoader
from matching import MatchingService, ScientistLevelAssigner
from interview_scheduler import InterviewScheduler
import os
import shutil

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return "<h1>DRDO Recruitment API Running</h1><p>Use POST /register or /schedule-interviews</p>"

@app.route('/register', methods=['POST'])
def register_user():
    try:
        user_id = request.form.get("user_id")
        gate_score_str = request.form.get("gate_score", "0")
        gate_score = int(gate_score_str) if gate_score_str.isdigit() else 0
        resume = request.files.get('resume')

        if not user_id or not resume:
            return jsonify({"error": "Missing user_id or resume"}), 400

        filepath = os.path.join(UPLOAD_FOLDER, resume.filename)
        resume.save(filepath)

        parsed_data = ResumeParserService.parse_resume(filepath)
        age = parsed_data.get('age')
        experience = parsed_data.get('total_experience', 0)
        core_field = parsed_data.get('core_field', '')

        parsed_data['Scientist_Level_Eligible'] = ScientistLevelAssigner.assign_scientist_level(age, experience)
        parsed_data['Category'] = ScientistLevelAssigner.assign_category(core_field)

        result = ResumeParserService.store_resume_data(user_id, filepath, gate_score, parsed_data)
        if not result:
            return jsonify({"error": "Failed to store resume data."}), 500

        return jsonify({"message": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/schedule-interviews', methods=['POST'])
def schedule_interviews():
    try:
        scheduler = InterviewScheduler('DRDO_Final_All_Degrees_Mapped.csv', 'DRDO_Interviewer_List_With_Phone.csv')
        scheduler.generate_schedule()
        scheduler.send_notifications()
        scheduler.export_schedule('DRDO_Interview_Schedule.csv')
        return jsonify({"message": "✅ Interview schedule created and notifications sent."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/fetch-eligible', methods=['GET'])
def fetch_eligible_candidates():
    df = DataLoader.load_interviewees()
    eligible = df[df['eligible_for_drdo'] == 'Yes']
    return jsonify(eligible.to_dict(orient='records'))

@app.route('/predict-interviewer', methods=['POST'])
def predict_interviewer():
    try:
        data = request.get_json()
        relevance_score = data.get('relevance_score', 0.5)
        matching_score = data.get('matching_score', 0.5)

        model = MatchingService.train_linear_regression()
        prediction = model.predict([[relevance_score, matching_score]])
        return jsonify({"predicted_interviewer_id": prediction.tolist()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/train', methods=['GET'])
def train_model():
    try:
        model = MatchingService.train_linear_regression()
        return jsonify({"message": "✅ Model trained successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
