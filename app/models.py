# In app/models.py

from . import db
import bcrypt
from sqlalchemy.schema import UniqueConstraint

class Company(db.Model):
    """Stores company information."""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    default_currency = db.Column(db.String(3), nullable=False) # e.g., 'USD', 'INR'
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    users = db.relationship('Users', back_populates='company', cascade="all, delete-orphan")
    rules = db.relationship('ApprovalRule', backref='company', lazy=True, cascade="all, delete-orphan")

class Users(db.Model):
    """Stores all users, regardless of role."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'Admin', 'Manager', 'Employee'
    
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('Company', back_populates='users')
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    # Relationships for manager-employee hierarchy
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reports = db.relationship('Users', backref=db.backref('manager', remote_side=[id]))
    
    expenses = db.relationship('Expense', backref='employee', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Expense(db.Model):
    """Stores individual expense claims."""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    description = db.Column(db.Text, nullable=True)
    expense_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending') # 'Pending', 'Approved', 'Rejected'
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    approvals = db.relationship('ExpenseApproval', backref='expense', lazy=True, cascade="all, delete-orphan")

class ApprovalRule(db.Model):
    """Defines a template for an approval workflow."""
    __tablename__ = 'approval_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    steps = db.relationship('ApprovalStep', backref='rule', lazy=True, cascade="all, delete-orphan", order_by="ApprovalStep.step_number")

class ApprovalStep(db.Model):
    """Defines a single, numbered step in an ApprovalRule."""
    __tablename__ = 'approval_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('approval_rules.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    approver_role = db.Column(db.String(50), nullable=False) # 'Manager', 'Finance', 'Director'
    is_manager_approver = db.Column(db.Boolean, default=False, nullable=False)
    
    __table_args__ = (UniqueConstraint('rule_id', 'step_number', name='_rule_step_uc'),)

class ExpenseApproval(db.Model):
    """Tracks the status of an expense at each approval step."""
    __tablename__ = 'expense_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)
    step_id = db.Column(db.Integer, db.ForeignKey('approval_steps.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # The user who took action
    status = db.Column(db.String(20), nullable=False) # 'Pending', 'Approved', 'Rejected'
    comments = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())