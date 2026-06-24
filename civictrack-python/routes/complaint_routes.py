"""
Complaint Routes
Full CRUD for complaints with Python AI classification,
Pandas analytics and ReportLab PDF generation
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from bson import ObjectId
from bson.json_util import dumps
import json
from datetime import datetime
import os
import uuid

from database import get_db
from utils.image_classifier import classify_image, classify_image_bytes, DEPARTMENTS, PRIORITIES
from utils.routing import auto_route, compute_urgency
from utils.email_sender import send_confirmation, send_status_update
from utils.analytics import (complaints_to_dataframe, get_overview_stats, get_by_type,
                               get_by_priority, get_by_ward, get_by_status, get_daily_trend,
                               get_department_stats, get_top_issues, generate_issue_type_chart,
                               generate_priority_pie_chart, generate_daily_trend_chart,
                               generate_ward_chart, generate_status_chart)
from utils.pdf_generator import generate_complaint_report, generate_analytics_report

complaint_bp = Blueprint('complaints', __name__)

UPLOAD_FOLDER = 'uploads/complaints'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def complaint_to_dict(c):
    """Convert MongoDB complaint to JSON-serializable dict"""
    if not c:
        return None
    c['_id']       = str(c['_id'])
    c['citizen']   = str(c.get('citizen', ''))
    if c.get('assignedOfficer'):
        c['assignedOfficer'] = str(c['assignedOfficer'])
    if c.get('upvotes'):
        c['upvotes'] = [str(u) for u in c['upvotes']]
    for t in c.get('timeline', []):
        if t.get('updatedBy'):
            t['updatedBy'] = str(t['updatedBy'])
        if t.get('updatedAt'):
            t['updatedAt'] = str(t['updatedAt'])
    if c.get('createdAt'):
        c['createdAt'] = str(c['createdAt'])
    if c.get('updatedAt'):
        c['updatedAt'] = str(c['updatedAt'])
    if c.get('resolvedAt'):
        c['resolvedAt'] = str(c['resolvedAt'])
    if c.get('estimatedResolution'):
        c['estimatedResolution'] = str(c['estimatedResolution'])
    return c


def get_current_user():
    """Get current user from JWT"""
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        db      = get_db()
        return db.users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return None


def generate_tracking_id():
    ts   = str(int(datetime.utcnow().timestamp()))[-6:]
    rand = str(uuid.uuid4().int)[:4]
    return f'CVT-{ts}-{rand}'


# ── CREATE COMPLAINT ──────────────────────────────────────────────────────────
@complaint_bp.route('', methods=['POST'])
@jwt_required()
def create_complaint():
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        user    = db.users.find_one({'_id': ObjectId(user_id)})

        title      = request.form.get('title', '').strip()
        description= request.form.get('description', '').strip()
        issue_type = request.form.get('issueType', 'other')
        lat        = float(request.form.get('lat', 0))
        lng        = float(request.form.get('lng', 0))
        address    = request.form.get('address', '')
        ward       = request.form.get('ward', '')
        landmark   = request.form.get('landmark', '')
        is_anon    = request.form.get('isAnonymous', 'false') == 'true'

        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400

        # Save uploaded photos
        photos = []
        files  = request.files.getlist('photos')
        ai_result = None

        for file in files[:5]:
            if file and allowed_file(file.filename):
                ext      = file.filename.rsplit('.', 1)[1].lower()
                filename = f'{uuid.uuid4().hex}.{ext}'
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                photos.append({'filename': filename, 'path': filepath, 'url': f'/uploads/complaints/{filename}', 'uploadedAt': datetime.utcnow()})

                # Run Python AI classification on first photo
                if ai_result is None:
                    ai_result = classify_image(filepath, hint=issue_type)

        # Use AI result or fallback
        if ai_result:
            final_type = ai_result['predicted_type']
            confidence = ai_result['confidence']
            all_scores = ai_result.get('all_scores', {})
        else:
            final_type = issue_type
            confidence = 0.85
            all_scores = {}

        # Auto route using Python routing engine
        routing = auto_route(final_type)

        # Compute urgency score
        urgency = compute_urgency(routing['priority'])

        complaint_doc = {
            'trackingId':       generate_tracking_id(),
            'title':            title,
            'description':      description,
            'issueType':        final_type,
            'aiClassification': {
                'predictedType': final_type,
                'confidence':    confidence,
                'allScores':     all_scores,
                'method':        'Python OpenCV + NumPy',
            },
            'priority':            routing['priority'],
            'urgencyScore':        urgency,
            'status':              'submitted',
            'citizen':             ObjectId(user_id),
            'assignedOfficer':     None,
            'department':          routing['department'],
            'estimatedResolution': routing['estimated_resolution'],
            'isAnonymous':         is_anon,
            'location': {
                'address':     address,
                'ward':        ward,
                'landmark':    landmark,
                'coordinates': {'lat': lat, 'lng': lng},
            },
            'photos':      photos,
            'upvotes':     [],
            'upvoteCount': 0,
            'timeline': [{
                'status':    'submitted',
                'message':   'Complaint submitted and automatically classified by Python AI',
                'updatedBy': ObjectId(user_id),
                'updatedAt': datetime.utcnow(),
            }],
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
        }

        result = db.complaints.insert_one(complaint_doc)
        complaint_doc['_id'] = result.inserted_id

        # Send confirmation email
        if not is_anon and user:
            send_confirmation(user['email'], user['name'], complaint_doc)

        return jsonify(complaint_to_dict(complaint_doc)), 201

    except Exception as e:
        print(f'Create complaint error: {e}')
        return jsonify({'error': str(e)}), 500


# ── MAP DATA (public) ─────────────────────────────────────────────────────────
@complaint_bp.route('/map', methods=['GET'])
def get_map_data():
    try:
        db   = get_db()
        data = list(db.complaints.find(
            {'status': {'$nin': ['rejected']}, 'location.coordinates.lat': {'$ne': 0}},
            {'trackingId':1,'title':1,'issueType':1,'priority':1,'status':1,'location':1,'upvoteCount':1,'createdAt':1}
        ).limit(500))
        return jsonify([complaint_to_dict(c) for c in data])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── MY COMPLAINTS (citizen) ───────────────────────────────────────────────────
@complaint_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_complaints():
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        data    = list(db.complaints.find({'citizen': ObjectId(user_id)}).sort('createdAt', -1))

        # Populate assigned officer names
        result = []
        for c in data:
            if c.get('assignedOfficer'):
                officer = db.users.find_one({'_id': c['assignedOfficer']}, {'name':1,'phone':1})
                if officer:
                    c['assignedOfficer'] = {'_id': str(officer['_id']), 'name': officer.get('name'), 'phone': officer.get('phone')}
            result.append(complaint_to_dict(c))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ASSIGNED COMPLAINTS (officer) ─────────────────────────────────────────────
@complaint_bp.route('/assigned', methods=['GET'])
@jwt_required()
def get_assigned():
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        data    = list(db.complaints.find({'assignedOfficer': ObjectId(user_id)}).sort('urgencyScore', -1))
        result  = []
        for c in data:
            citizen = db.users.find_one({'_id': c['citizen']}, {'name':1,'email':1,'phone':1})
            if citizen:
                c['citizen'] = {'_id': str(citizen['_id']), 'name': citizen.get('name'), 'email': citizen.get('email'), 'phone': citizen.get('phone')}
            result.append(complaint_to_dict(c))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── TRACK BY TRACKING ID (public) ─────────────────────────────────────────────
@complaint_bp.route('/track/<tracking_id>', methods=['GET'])
def track_complaint(tracking_id):
    try:
        db = get_db()
        c  = db.complaints.find_one({'trackingId': tracking_id})
        if not c:
            return jsonify({'error': 'Complaint not found'}), 404
        if c.get('assignedOfficer'):
            officer = db.users.find_one({'_id': c['assignedOfficer']}, {'name':1,'phone':1})
            if officer:
                c['assignedOfficer'] = {'_id': str(officer['_id']), 'name': officer.get('name'), 'phone': officer.get('phone')}
        return jsonify(complaint_to_dict(c))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ALL COMPLAINTS (admin) ────────────────────────────────────────────────────
@complaint_bp.route('', methods=['GET'])
@jwt_required()
def get_all_complaints():
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        user    = db.users.find_one({'_id': ObjectId(user_id)})
        if user.get('role') not in ['admin', 'super_admin']:
            return jsonify({'error': 'Access denied'}), 403

        filt   = {}
        status = request.args.get('status')
        type_  = request.args.get('type')
        prio   = request.args.get('priority')
        ward   = request.args.get('ward')
        search = request.args.get('search')
        page   = int(request.args.get('page', 1))
        limit  = int(request.args.get('limit', 30))

        if status: filt['status']         = status
        if type_:  filt['issueType']      = type_
        if prio:   filt['priority']        = prio
        if ward:   filt['location.ward']   = ward
        if search:
            filt['$or'] = [
                {'title':      {'$regex': search, '$options': 'i'}},
                {'trackingId': {'$regex': search, '$options': 'i'}},
            ]

        total = db.complaints.count_documents(filt)
        data  = list(db.complaints.find(filt).sort('createdAt', -1).skip((page-1)*limit).limit(limit))

        result = []
        for c in data:
            if c.get('citizen') and isinstance(c['citizen'], ObjectId):
                cit = db.users.find_one({'_id': c['citizen']}, {'name':1,'email':1,'phone':1})
                if cit:
                    c['citizen'] = {'_id': str(cit['_id']), 'name': cit.get('name'), 'email': cit.get('email'), 'phone': cit.get('phone')}
            if c.get('assignedOfficer') and isinstance(c['assignedOfficer'], ObjectId):
                off = db.users.find_one({'_id': c['assignedOfficer']}, {'name':1,'phone':1})
                if off:
                    c['assignedOfficer'] = {'_id': str(off['_id']), 'name': off.get('name'), 'phone': off.get('phone')}
            result.append(complaint_to_dict(c))

        return jsonify({'complaints': result, 'total': total, 'pages': -(-total // limit)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── UPVOTE ────────────────────────────────────────────────────────────────────
@complaint_bp.route('/<cid>/upvote', methods=['POST'])
@jwt_required()
def upvote(cid):
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        c       = db.complaints.find_one({'_id': ObjectId(cid)})
        if not c:
            return jsonify({'error': 'Not found'}), 404

        uid     = ObjectId(user_id)
        upvotes = c.get('upvotes', [])
        if uid in upvotes:
            upvotes.remove(uid)
            upvoted = False
        else:
            upvotes.append(uid)
            upvoted = True

        db.complaints.update_one({'_id': ObjectId(cid)}, {'$set': {'upvotes': upvotes, 'upvoteCount': len(upvotes)}})
        return jsonify({'upvoteCount': len(upvotes), 'upvoted': upvoted})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ASSIGN OFFICER (admin) ────────────────────────────────────────────────────
@complaint_bp.route('/<cid>/assign', methods=['PATCH'])
@jwt_required()
def assign_officer(cid):
    try:
        user_id   = get_jwt_identity()
        data      = request.get_json()
        officer_id= data.get('officerId')
        message   = data.get('message', 'Assigned to field officer')
        db        = get_db()

        officer   = db.users.find_one({'_id': ObjectId(officer_id)})
        db.complaints.update_one(
            {'_id': ObjectId(cid)},
            {'$set': {'assignedOfficer': ObjectId(officer_id), 'status': 'assigned', 'updatedAt': datetime.utcnow()},
             '$push': {'timeline': {'status': 'assigned', 'message': message, 'updatedBy': ObjectId(user_id), 'updatedAt': datetime.utcnow()}}}
        )
        c    = db.complaints.find_one({'_id': ObjectId(cid)})
        cit  = db.users.find_one({'_id': c['citizen']})
        if cit:
            c['citizen'] = {'name': cit.get('name'), 'email': cit.get('email')}
            send_status_update(cit['email'], cit['name'], c, f'Your complaint has been assigned to {officer.get("name")} for resolution.')
        return jsonify(complaint_to_dict(c))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── UPDATE STATUS ─────────────────────────────────────────────────────────────
@complaint_bp.route('/<cid>/status', methods=['PATCH'])
@jwt_required()
def update_status(cid):
    try:
        user_id = get_jwt_identity()
        data    = request.get_json()
        status  = data.get('status')
        message = data.get('message', f'Status updated to {status}')
        db      = get_db()

        update  = {
            '$set':  {'status': status, 'updatedAt': datetime.utcnow()},
            '$push': {'timeline': {'status': status, 'message': message, 'updatedBy': ObjectId(user_id), 'updatedAt': datetime.utcnow()}}
        }
        if status == 'resolved':
            c     = db.complaints.find_one({'_id': ObjectId(cid)})
            hours = int((datetime.utcnow() - c['createdAt']).total_seconds() / 3600)
            update['$set']['resolvedAt']          = datetime.utcnow()
            update['$set']['resolutionTimeHours']  = hours
            update['$set']['resolutionNote']       = message

        db.complaints.update_one({'_id': ObjectId(cid)}, update)
        c   = db.complaints.find_one({'_id': ObjectId(cid)})
        cit = db.users.find_one({'_id': c['citizen']})
        if cit:
            send_status_update(cit['email'], cit['name'], c, message)
        return jsonify(complaint_to_dict(c))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ANALYTICS (Pandas + Matplotlib) ──────────────────────────────────────────
@complaint_bp.route('/stats/overview', methods=['GET'])
@jwt_required()
def get_analytics():
    try:
        db   = get_db()
        data = list(db.complaints.find({}))

        # Convert to Pandas DataFrame for analysis
        df   = complaints_to_dataframe(data)

        stats = {
            **get_overview_stats(df),
            'by_type':          get_by_type(df),
            'by_priority':      get_by_priority(df),
            'by_ward':          get_by_ward(df),
            'by_status':        get_by_status(df),
            'trend':            get_daily_trend(df),
            'department_stats': get_department_stats(df),
            'top_issues':       get_top_issues(df),
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── CHART IMAGES (Matplotlib) ─────────────────────────────────────────────────
@complaint_bp.route('/stats/charts', methods=['GET'])
@jwt_required()
def get_charts():
    try:
        db   = get_db()
        data = list(db.complaints.find({}))
        df   = complaints_to_dataframe(data)

        charts = {
            'by_type':    generate_issue_type_chart(df),
            'by_priority':generate_priority_pie_chart(df),
            'trend':      generate_daily_trend_chart(df),
            'by_ward':    generate_ward_chart(df),
            'by_status':  generate_status_chart(df),
        }
        return jsonify({k: v for k, v in charts.items() if v})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── GENERATE COMPLAINT PDF (ReportLab) ────────────────────────────────────────
@complaint_bp.route('/<cid>/pdf', methods=['GET'])
@jwt_required()
def download_complaint_pdf(cid):
    try:
        db      = get_db()
        c       = db.complaints.find_one({'_id': ObjectId(cid)})
        if not c:
            return jsonify({'error': 'Not found'}), 404

        officer_name = None
        if c.get('assignedOfficer'):
            off          = db.users.find_one({'_id': c['assignedOfficer']})
            officer_name = off.get('name') if off else None

        pdf_buf = generate_complaint_report(c, officer_name)
        return send_file(pdf_buf, mimetype='application/pdf', as_attachment=True, download_name=f'{c["trackingId"]}_report.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── GENERATE ANALYTICS PDF (ReportLab) ───────────────────────────────────────
@complaint_bp.route('/stats/pdf', methods=['GET'])
@jwt_required()
def download_analytics_pdf():
    try:
        db   = get_db()
        data = list(db.complaints.find({}))
        df   = complaints_to_dataframe(data)
        stats = {
            **get_overview_stats(df),
            'by_type':          get_by_type(df),
            'department_stats': get_department_stats(df),
        }
        pdf_buf = generate_analytics_report(stats, df)
        return send_file(pdf_buf, mimetype='application/pdf', as_attachment=True, download_name='civictrack_analytics.pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── DEPARTMENT STATS ──────────────────────────────────────────────────────────
@complaint_bp.route('/stats/departments', methods=['GET'])
@jwt_required()
def dept_stats():
    try:
        db   = get_db()
        data = list(db.complaints.find({}))
        df   = complaints_to_dataframe(data)
        return jsonify(get_department_stats(df))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
