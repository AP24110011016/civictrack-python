"""
CivicTrack — Smart Civic Complaint Management System
Full Python Backend using:
- Flask          : Web framework + REST API
- PyMongo        : MongoDB database connection
- bcrypt         : Password hashing
- JWT Extended   : Authentication tokens
- OpenCV         : Image processing and classification
- NumPy          : Numerical computations on pixel data
- Pandas         : Data analysis and aggregation
- Matplotlib     : Chart generation
- ReportLab      : PDF report generation
- smtplib        : Email notifications
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import routes
from routes.auth_routes import auth_bp
from routes.complaint_routes import complaint_bp
from routes.user_routes import user_bp
from database import connect_db

# ── App Setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static')
CORS(app, origins='*', supports_credentials=True)

# JWT Configuration
app.config['JWT_SECRET_KEY']       = os.getenv('JWT_SECRET', 'civictrack_secret_2026')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Tokens don't expire for demo

jwt = JWTManager(app)

# ── Register Blueprints (Routes) ───────────────────────────────────────────────
app.register_blueprint(auth_bp,      url_prefix='/api/auth')
app.register_blueprint(complaint_bp, url_prefix='/api/complaints')
app.register_blueprint(user_bp,      url_prefix='/api/users')

# ── Serve uploaded files ───────────────────────────────────────────────────────
@app.route('/uploads/complaints/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads/complaints', filename)

# ── Health Check ───────────────────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({
        'status':  'ok',
        'service': 'CivicTrack Full Python Backend',
        'stack':   'Flask + OpenCV + NumPy + Pandas + Matplotlib + ReportLab',
        'version': '1.0.0'
    })

# ── Start Server ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════╗
║        🏛️  CIVICTRACK — FULL PYTHON BACKEND              ║
╠══════════════════════════════════════════════════════════╣
║  Flask          → Web API                                ║
║  PyMongo        → MongoDB Database                       ║
║  OpenCV + NumPy → Image AI Classification                ║
║  Pandas         → Data Analytics Engine                  ║
║  Matplotlib     → Chart Generation                       ║
║  ReportLab      → PDF Report Generation                  ║
║  smtplib        → Email Notifications                    ║
╠══════════════════════════════════════════════════════════╣
║  Running on: http://localhost:5000                       ║
╚══════════════════════════════════════════════════════════╝
    """)
    connect_db()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
