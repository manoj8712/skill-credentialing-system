import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page', 'danger')
                return redirect(url_for('login'))
            if session.get('role') != role:
                flash('Unauthorized access', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator