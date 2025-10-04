# In app/routes.py

from flask import request, jsonify, Blueprint
from app import db
from app.models import Users, Company
from flask_jwt_extended import create_access_token

# This line defines the 'bp' variable
bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/auth/register', methods=['POST'])
def register():
    # 1. Get data from the incoming request
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('company_name'):
        return jsonify({'message': 'Missing required fields'}), 400

    # 2. Check if the user already exists
    if Users.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User with this email already exists'}), 409

    # 3. Create a new Company
    new_company = Company(
        name=data['company_name'],
        default_currency='USD' 
    )
    db.session.add(new_company)
    db.session.commit()

    # 4. Create a new User (as Admin) and link to the company
    new_user = Users(
        email=data['email'],
        role='Admin',
        company_id=new_company.id
    )
    new_user.set_password(data['password'])

    # 5. Add to database and save
    db.session.add(new_user)
    db.session.commit()

    # 6. Return a success response
    return jsonify({'message': 'Admin user registered successfully'}), 201


@bp.route('/auth/login', methods=['POST'])
def login():
    # 1. Get email and password from the request
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400

    email = data.get('email')
    password = data.get('password')

    # 2. Find the user in the database
    user = Users.query.filter_by(email=email).first()

    # 3. Check if the user exists and the password is correct
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401

    # 4. Create and return a new access token (JWT)
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token)