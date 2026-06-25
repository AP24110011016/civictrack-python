"""
User Management Routes
Admin and Super Admin user management
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import bcrypt
from datetime import datetime
from database import get_db

user_bp = Blueprint('users', __name__)


def user_to_dict(u):
    if not u:
        return None
    return {
        'id':         str(u['_id']),
        '_id':        str(u['_id']),
        'name':       u.get('name', ''),
        'email':      u.get('email', ''),
        'role':       u.get('role', 'citizen'),
        'phone':      u.get('phone', ''),
        'ward':       u.get('ward', ''),
        'department': u.get('department', ''),
        'isActive':   u.get('isActive', True),
        'createdAt':  str(u.get('createdAt', '')),
        'lastLogin':  str(u.get('lastLogin', '')),
    }


@user_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        me      = db.users.find_one({'_id': ObjectId(user_id)})
        if me.get('role') not in ['admin', 'super_admin']:
            return jsonify({'error': 'Access denied'}), 403
        filt    = {}
        role    = request.args.get('role')
        if role:
            filt['role'] = role
        users = list(db.users.find(filt, {'password': 0}).sort('createdAt', -1))
        return jsonify([user_to_dict(u) for u in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/officers', methods=['GET'])
@jwt_required()
def get_officers():
    try:
        db      = get_db()
        officers= list(db.users.find({'role': 'field_officer', 'isActive': True}, {'password': 0}))
        result  = []
        for o in officers:
            active   = db.complaints.count_documents({'assignedOfficer': o['_id'], 'status': {'$in': ['assigned','in_progress']}})
            resolved = db.complaints.count_documents({'assignedOfficer': o['_id'], 'status': 'resolved'})
            d        = user_to_dict(o)
            d['activeComplaints'] = active
            d['totalResolved']    = resolved
            result.append(d)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('', methods=['POST'])
@jwt_required()
def create_user():
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        me      = db.users.find_one({'_id': ObjectId(user_id)})
        if me.get('role') != 'super_admin':
            return jsonify({'error': 'Only super admin can create users'}), 403
        data    = request.get_json()
        if db.users.find_one({'email': data.get('email', '').lower()}):
            return jsonify({'error': 'Email already exists'}), 400
        hashed  = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        doc     = {
            'name':       data.get('name'),
            'email':      data.get('email', '').lower(),
            'password':   hashed,
            'phone':      data.get('phone', ''),
            'role':       data.get('role', 'citizen'),
            'ward':       data.get('ward', ''),
            'department': data.get('department', ''),
            'isActive':   True,
            'createdAt':  datetime.utcnow(),
        }
        result = db.users.insert_one(doc)
        doc['_id'] = result.inserted_id
        return jsonify(user_to_dict(doc)), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/<uid>', methods=['PUT'])
@jwt_required()
def update_user(uid):
    try:
        data = request.get_json()
        db   = get_db()
        db.users.update_one(
            {'_id': ObjectId(uid)},
            {'$set': {'name': data.get('name'), 'phone': data.get('phone'), 'role': data.get('role'), 'ward': data.get('ward'), 'department': data.get('department'), 'isActive': data.get('isActive', True)}}
        )
        u = db.users.find_one({'_id': ObjectId(uid)})
        return jsonify(user_to_dict(u))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/<uid>', methods=['DELETE'])
@jwt_required()
def delete_user(uid):
    try:
        db = get_db()
        db.users.delete_one({'_id': ObjectId(uid)})
        return jsonify({'message': 'User deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
