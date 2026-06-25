"""
Authentication Routes
Handles login, register, profile using Flask + JWT + bcrypt
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from bson import ObjectId
from bson.errors import InvalidId
import bcrypt
from datetime import datetime
from database import get_db

auth_bp = Blueprint('auth', __name__)


def user_to_dict(user):
    """Convert MongoDB user document to clean dict"""
    if not user:
        return None
    return {
        'id':         str(user['_id']),
        'name':       user.get('name', ''),
        'email':      user.get('email', ''),
        'role':       user.get('role', 'citizen'),
        'phone':      user.get('phone', ''),
        'ward':       user.get('ward', ''),
        'department': user.get('department', ''),
        'isActive':   user.get('isActive', True),
        'createdAt':  str(user.get('createdAt', '')),
    }


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name     = data.get('name', '').strip()
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')
        phone    = data.get('phone', '')
        ward     = data.get('ward', '')

        if not name or not email or not password:
            return jsonify({'error': 'Name, email and password are required'}), 400

        db = get_db()
        if db.users.find_one({'email': email}):
            return jsonify({'error': 'Email already registered'}), 400

        # Hash password using bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_doc = {
            'name':      name,
            'email':     email,
            'password':  hashed,
            'phone':     phone,
            'ward':      ward,
            'role':      'citizen',
            'isActive':  True,
            'createdAt': datetime.utcnow(),
        }

        result = db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id

        token = create_access_token(identity=str(result.inserted_id))
        return jsonify({'token': token, 'user': user_to_dict(user_doc)}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data     = request.get_json()
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        db   = get_db()
        user = db.users.find_one({'email': email})

        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401

        # Check password using bcrypt
        if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({'error': 'Invalid email or password'}), 401

        if not user.get('isActive', True):
            return jsonify({'error': 'Account is deactivated'}), 401

        # Update last login
        db.users.update_one({'_id': user['_id']}, {'$set': {'lastLogin': datetime.utcnow()}})

        token = create_access_token(identity=str(user['_id']))
        return jsonify({'token': token, 'user': user_to_dict(user)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    try:
        user_id = get_jwt_identity()
        db      = get_db()
        user    = db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user_to_dict(user))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_me():
    try:
        user_id = get_jwt_identity()
        data    = request.get_json()
        db      = get_db()
        db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'name': data.get('name'), 'phone': data.get('phone'), 'ward': data.get('ward')}}
        )
        user = db.users.find_one({'_id': ObjectId(user_id)})
        return jsonify(user_to_dict(user))
    except Exception as e:
        return jsonify({'error': str(e)}), 500
