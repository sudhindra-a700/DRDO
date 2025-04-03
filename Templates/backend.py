# Required dependencies: pip install flask flask-cors python-dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import time
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
load_dotenv()

# Temporary storage for OTPs (use Redis in production)
otp_storage = {}
OTP_EXPIRY = 300  # 5 minutes

@app.route('/login', methods=['POST'])
def handle_login():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['user_type', 'identifier', 'phone']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    
    # Store OTP with metadata
    otp_storage[data['phone']] = {
        'otp': otp,
        'timestamp': time.time(),
        'user_type': data['user_type'],
        'identifier': data['identifier']
    }

    # In production: Add SMS gateway integration here
    print(f"DEBUG OTP for {data['phone']}: {otp}")
    
    return jsonify({'message': 'OTP sent successfully'}), 200

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    
    if 'phone' not in data or 'otp' not in data:
        return jsonify({'error': 'Phone and OTP required'}), 400

    stored_data = otp_storage.get(data['phone'])
    if not stored_data:
        return jsonify({'error': 'OTP not found or expired'}), 404

    # Check OTP expiration
    if time.time() - stored_data['timestamp'] > OTP_EXPIRY:
        del otp_storage[data['phone']]
        return jsonify({'error': 'OTP expired'}), 401

    if data['otp'] != stored_data['otp']:
        return jsonify({'error': 'Invalid OTP'}), 401

    # Cleanup and response
    del otp_storage[data['phone']]
    return jsonify({
        'message': 'Authentication successful',
        'user_type': stored_data['user_type'],
        'redirect': f'/{stored_data["user_type"]}_dashboard'
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)