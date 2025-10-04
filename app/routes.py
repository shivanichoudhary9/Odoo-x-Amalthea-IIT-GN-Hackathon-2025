# In app/routes.py
import requests
from flask import request, jsonify, Blueprint
from app import db
from app.models import Users, Company, ApprovalRule, ApprovalStep
from flask_jwt_extended import create_access_token

# This line defines the 'bp' variable
bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/auth/register', methods=['POST'])
def register():
    # 1. Get data from the incoming request
    data = request.get_json()
    # Add country_code to the validation
    if not all(k in data for k in ['email', 'password', 'company_name', 'country_code']):
        return jsonify({'message': 'Missing required fields'}), 400

    # 2. Check if the user already exists
    if Users.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User with this email already exists'}), 409

    # --- NEW LOGIC TO GET CURRENCY ---
    currency_code = 'USD' # Default currency
    try:
        # Call the external API to get country data
        country_code = data['country_code']
        response = requests.get(f'https://restcountries.com/v3.1/alpha/{country_code}')
        response.raise_for_status() # Raise an exception for bad status codes
        
        country_data = response.json()
        # Extract the first currency code (e.g., 'INR', 'EUR')
        currency_code = list(country_data[0]['currencies'].keys())[0]

    except requests.exceptions.RequestException as e:
        # If the API call fails, we can log the error and use the default
        print(f"Could not fetch currency for {country_code}: {e}")
    except (KeyError, IndexError):
        # If the API response format is unexpected
        print(f"Could not parse currency from API response for {country_code}")
    # ------------------------------------

    # 3. Create a new Company with the fetched currency
    new_company = Company(
        name=data['company_name'],
        default_currency=currency_code
    )
    db.session.add(new_company)
    db.session.commit()

    # 4. Create a new User (as Admin) and link to the company
    # (The rest of the function remains the same)
    new_user = Users(
        email=data['email'],
        role='Admin',
        company_id=new_company.id
    )
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.commit()

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

    # 4. Create token and get the user's role from the database
    access_token = create_access_token(identity=str(user.id))
    user_role = user.role 
    
    # 5. Return both the token and the role in the response
    return jsonify(access_token=access_token, role=user_role)


from flask_jwt_extended import jwt_required, get_jwt_identity



@bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    # 1. Get the ID of the user from the access token
    current_user_id = int(get_jwt_identity())
    admin_user = Users.query.get(current_user_id)

    # 2. Authorization Check: Ensure the user is an Admin
    if admin_user.role != 'Admin':
        return jsonify({'message': 'Admin access required'}), 403

    # 3. Get the new user's data from the request body
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('role'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # --- NEW VALIDATION FOR CFO ---
    # 4. If the new user's role is CFO, check if one already exists
    if data['role'] == 'CFO':
        existing_cfo = Users.query.filter_by(company_id=admin_user.company_id, role='CFO').first()
        if existing_cfo:
            # If a CFO is found, return an error and stop.
            return jsonify({'message': 'Cannot add more than one CFO'}), 409 # 409 is the "Conflict" status code
    # ------------------------------------
    
    # 5. Check if user email already exists
    if Users.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User with this email already exists'}), 409

    # 6. Create the new user
    new_user = Users(
        email=data['email'],
        role=data['role'],
        company_id=admin_user.company_id
    )
    new_user.set_password(data['password'])

    # 7. Save to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': f'{new_user.role} created successfully'}), 201

# Add these to your imports at the top of app/routes.py
from app.models import Expense, ApprovalRule, ExpenseApproval
from datetime import date

# ... (all your other routes are here) ...

@bp.route('/expenses', methods=['POST'])
@jwt_required()
def submit_expense():
    # 1. Identify the logged-in user
    current_user_id = int(get_jwt_identity())
    employee = Users.query.get(current_user_id)

    # 2. Get expense data from the request
    data = request.get_json()
    if not data or not data.get('category') or not data.get('amount') or not data.get('expense_date'):
        return jsonify({'message': 'Missing required expense fields'}), 400

    # 3. Create the new Expense object
    new_expense = Expense(
        employee_id=employee.id,
        category=data['category'],
        amount=data['amount'],
        currency=data.get('currency', employee.company.default_currency),
        description=data.get('description'),
        expense_date=date.fromisoformat(data['expense_date']) # Converts 'YYYY-MM-DD' string to a Date
    )
    db.session.add(new_expense)
    
    # --- This is the key workflow logic ---
    # 4. Find the approval rule and kick off the workflow
    # (For a hackathon, we can simplify and assume the first rule for the company is the correct one)
    rule = ApprovalRule.query.filter_by(company_id=employee.company_id).first()
    if not rule or not rule.steps:
        return jsonify({'message': 'No approval workflow is configured for this company'}), 500
    
    # 5. Create the first approval step entry
    first_step = rule.steps[0] # Assumes steps are ordered by step_number
    initial_approval = ExpenseApproval(
        expense=new_expense,
        step_id=first_step.id,
        status='Pending'
    )
    db.session.add(initial_approval)
    # ------------------------------------

    # 6. Save everything to the database
    db.session.commit()

    return jsonify({'message': 'Expense submitted successfully and is pending approval'}), 201


# ... (all your other routes are here) ...

@bp.route('/approval-rules', methods=['POST'])
@jwt_required()
def create_approval_rule():
    # 1. Identify the logged-in user and ensure they are an Admin
    current_user_id = int(get_jwt_identity())
    admin_user = Users.query.get(current_user_id)
    if admin_user.role != 'Admin':
        return jsonify({'message': 'Admin access required'}), 403

    # 2. Get the workflow data from the request body
    data = request.get_json()
    if not data or not data.get('name') or not data.get('steps'):
        return jsonify({'message': 'Missing rule name or steps'}), 400

    # 3. Create the main ApprovalRule
    new_rule = ApprovalRule(
        name=data['name'],
        company_id=admin_user.company_id,
        description=data.get('description')
    )
    db.session.add(new_rule)

    # 4. Loop through the steps and create ApprovalStep records
    for step_data in data['steps']:
        new_step = ApprovalStep(
            rule=new_rule,
            step_number=step_data['step_number'],
            approver_role=step_data['approver_role']
        )
        db.session.add(new_step)

    # 5. Save everything to the database
    db.session.commit()

    return jsonify({'message': 'Approval workflow created successfully'}), 201

# ... (all your other routes are here) ...

@bp.route('/approvals/pending', methods=['GET'])
@jwt_required()
def get_pending_approvals():
    # 1. Identify the logged-in user and their role
    current_user_id = int(get_jwt_identity())
    approver = Users.query.get_or_404(current_user_id)
    user_role = approver.role # This could be 'Manager', 'Finance', etc.

    # 2. Find all 'Pending' approval requests that match the user's role
    # This query is now simpler and works for any role!
    pending_approvals = db.session.query(ExpenseApproval).join(ApprovalStep).filter(
        ApprovalStep.approver_role == user_role,
        ExpenseApproval.status == 'Pending'
    ).all()

    # 3. Format the data for a clean response (this part remains the same)
    results = []
    for approval in pending_approvals:
        employee = Users.query.get(approval.expense.employee_id)
        results = []
    for approval in pending_approvals:
        employee = Users.query.get(approval.expense.employee_id)
        results.append({
            'approval_id': approval.id,
            'expense_id': approval.expense.id,
            'employee_name': employee.email,
            'category': approval.expense.category,
            'amount': str(approval.expense.amount),
            'currency': approval.expense.currency,
            'description': approval.expense.description, # <-- ADD THIS LINE
            'expense_date': approval.expense.expense_date.isoformat(),
            'submitted_at': approval.expense.created_at.isoformat()
        })

    return jsonify(results)

# ... (all your other routes are here) ...

# In app/routes.py

@bp.route('/approvals/<int:approval_id>/approve', methods=['POST'])
@jwt_required()
def approve_expense(approval_id):
    # 1. Identify the current user (the approver)
    approver_id = int(get_jwt_identity())
    approver = Users.query.get_or_404(approver_id)

    # 2. Find the specific approval record
    approval = ExpenseApproval.query.get_or_404(approval_id)

    # --- NEW, MORE FLEXIBLE SECURITY CHECK ---
    # 3. Check if the approver's role matches the role required for this step
    if approver.role != approval.step.approver_role:
        return jsonify({'message': f'This expense requires approval from the {approval.step.approver_role}'}), 403
    # ---------------------------------------------

    # 4. Update the current approval step
    approval.status = 'Approved'
    approval.approver_id = approver.id
    approval.comments = request.json.get('comments')

    # 5. Check if there's a next step in the rule
    current_step = approval.step
    rule = current_step.rule
    next_step = ApprovalStep.query.filter_by(rule_id=rule.id, step_number=current_step.step_number + 1).first()

    if next_step:
        # If there is a next step, create a new pending approval for it
        new_approval = ExpenseApproval(
            expense_id=approval.expense_id,
            step_id=next_step.id,
            status='Pending'
        )
        db.session.add(new_approval)
    else:
        # If this is the final step, approve the whole expense
        approval.expense.status = 'Approved'

    db.session.commit()
    return jsonify({'message': 'Expense approved'})


@bp.route('/approvals/<int:approval_id>/reject', methods=['POST'])
@jwt_required()
def reject_expense(approval_id):
    # 1. Identify the approver
    approver_id = int(get_jwt_identity())
    approver = Users.query.get_or_404(approver_id)
    
    approval = ExpenseApproval.query.get_or_404(approval_id)
    
    # --- APPLY THE SAME FLEXIBLE SECURITY CHECK HERE ---
    if approver.role != approval.step.approver_role:
        return jsonify({'message': f'You are not authorized to reject this expense'}), 403
    # ----------------------------------------------------
    
    # 2. Update records to rejected
    approval.status = 'Rejected'
    approval.approver_id = approver.id
    approval.comments = request.json.get('comments')
    approval.expense.status = 'Rejected'

    db.session.commit()
    return jsonify({'message': 'Expense rejected'})

@bp.route('/expenses/my-history', methods=['GET'])
@jwt_required()
def get_my_expense_history():
    current_user_id = int(get_jwt_identity())
    expenses = Expense.query.filter_by(employee_id=current_user_id).order_by(Expense.created_at.desc()).all()
    
    results = []
    for expense in expenses:
        status_display = expense.status
        # If the overall status is pending, find out the current step
        if expense.status == 'Pending':
            pending_approval = ExpenseApproval.query.filter_by(expense_id=expense.id, status='Pending').first()
            if pending_approval:
                status_display = f"Pending {pending_approval.step.approver_role} Approval"

        results.append({
            'expense_id': expense.id,
            'category': expense.category,
            'amount': str(expense.amount),
            'currency': expense.currency,
            'status': status_display, # Use the new, smarter status
            'submitted_at': expense.created_at.isoformat()
        })
        
    return jsonify(results)

# In app/routes.py

# ... (all your other routes and imports are here) ...

@bp.route('/users', methods=['GET'])
@jwt_required() # Ensures a user is logged in
def get_users():
    # Step 1: Get the ID of the logged-in user from the JWT
    current_user_id = int(get_jwt_identity())
    
    # Step 2: Fetch that user from the database to check their role
    admin_user = Users.query.get_or_404(current_user_id)
    
    # Step 3: Authorize the user. Make sure they are an Admin.
    if admin_user.role != 'Admin':
        return jsonify({'message': 'Admin access required'}), 403 # 403 Forbidden

    # Step 4: Query the database for all users in the same company
    users_in_company = Users.query.filter_by(company_id=admin_user.company_id).all()

    # Step 5: Format the user data into a JSON-friendly list of dictionaries
    user_list = []
    for user in users_in_company:
        user_list.append({
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'manager_id': user.manager_id
        })

    # Step 6: Return the list as a JSON response
    return jsonify(user_list)

@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    # 1. Identify the logged-in user and ensure they are an Admin
    current_user_id = int(get_jwt_identity())
    admin_user = Users.query.get_or_404(current_user_id)
    if admin_user.role != 'Admin':
        return jsonify({'message': 'Admin access required'}), 403

    # 2. Find the user to be updated
    user_to_update = Users.query.get_or_404(user_id)

    # 3. Security check: Ensure the admin is editing a user in their own company
    if user_to_update.company_id != admin_user.company_id:
        return jsonify({'message': 'Not authorized to edit this user'}), 403

    # 4. Get the new data from the request body
    data = request.get_json()

    # 5. Update the user's fields if new data is provided
    if 'role' in data:
        user_to_update.role = data['role']
    if 'manager_id' in data:
        user_to_update.manager_id = data['manager_id']

    # 6. Save the changes to the database
    db.session.commit()

    return jsonify({'message': 'User updated successfully'})

@bp.route('/team/expenses', methods=['GET'])
@jwt_required()
def get_team_expense_history():
    # 1. Get the logged-in user
    current_user_id = int(get_jwt_identity())
    current_user = Users.query.get_or_404(current_user_id)
    
    # 2. Authorization check: user must be a Manager or CFO
    if current_user.role not in ['Manager', 'CFO']:
        return jsonify({'message': 'Access for Managers or CFO only'}), 403

    # 3. Fetch expenses based on the user's role
    team_expenses = []
    if current_user.role == 'Manager':
        # If user is a Manager, get their direct reports' expenses
        employee_ids = [user.id for user in Users.query.filter_by(manager_id=current_user.id).all()]
        if employee_ids:
            team_expenses = Expense.query.filter(Expense.employee_id.in_(employee_ids)).order_by(Expense.created_at.desc()).all()
    
    elif current_user.role == 'CFO':
        # If user is a CFO, get ALL expenses for the whole company
        company_id = current_user.company_id
        team_expenses = db.session.query(Expense).join(Users).filter(Users.company_id == company_id).order_by(Expense.created_at.desc()).all()
    
    # 4. Format the results (this part is the same)
    results = []
    for expense in team_expenses:
        status_display = expense.status
        if expense.status == 'Pending':
            pending_approval = ExpenseApproval.query.filter_by(expense_id=expense.id, status='Pending').first()
            if pending_approval:
                status_display = f"Pending {pending_approval.step.approver_role} Approval"
        
        results.append({
            'employee_email': expense.employee.email,
            'expense_date': expense.expense_date.isoformat(),
            'category': expense.category,
            'amount': str(expense.amount),
            'currency': expense.currency,
            'status': status_display
        })
    return jsonify(results)

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    # 1. Ensure the current user is an Admin
    current_user_id = int(get_jwt_identity())
    admin_user = Users.query.get_or_404(current_user_id)
    if admin_user.role != 'Admin':
        return jsonify({'message': 'Admin access required'}), 403

    # 2. Find the user to be deleted
    user_to_delete = Users.query.get_or_404(user_id)

    # 3. Security checks
    if user_to_delete.company_id != admin_user.company_id:
        return jsonify({'message': 'Not authorized to delete this user'}), 403
    if user_to_delete.id == admin_user.id:
        return jsonify({'message': 'Admin cannot delete themselves'}), 400

    # 4. Delete the user
    db.session.delete(user_to_delete)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'})