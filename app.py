from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from database import db
from blockchain import Blockchain
from auth import hash_password, verify_password, login_required, role_required
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

blockchain = Blockchain(db)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'student':
            return redirect(url_for('student_dashboard'))
        elif session['role'] == 'faculty':
            return redirect(url_for('faculty_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'student')

        if not all([username, email, password, full_name]):
            flash('All fields are required', 'danger')
            return redirect(url_for('register'))

        if db.get_user_by_email(email):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        if db.get_user_by_username(username):
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))

        hashed_pw = hash_password(password)

        user_data = {
            'username': username,
            'email': email,
            'password': hashed_pw,
            'full_name': full_name,
            'role': role
        }

        db.create_user(user_data)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required', 'danger')
            return redirect(url_for('login'))

        user = db.get_user_by_email(email)

        if user and verify_password(password, user['password']):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']

            flash(f'Welcome back, {user["full_name"]}!', 'success')

            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'faculty':
                return redirect(url_for('faculty_dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    student_id = session['user_id']
    skills = db.get_student_skills(student_id)
    credentials = db.get_student_credentials(student_id)
    user = db.get_user_by_id(student_id)

    approved_count = len([s for s in skills if s['status'] == 'approved'])
    pending_count = len([s for s in skills if s['status'] == 'pending'])
    rejected_count = len([s for s in skills if s['status'] == 'rejected'])

    return render_template('student_dashboard.html',
                         skills=skills,
                         credentials=credentials,
                         credibility_score=user.get('credibility_score', 0),
                         approved_count=approved_count,
                         pending_count=pending_count,
                         rejected_count=rejected_count)

@app.route('/student/submit-skill', methods=['GET', 'POST'])
@role_required('student')
def submit_skill():
    if request.method == 'POST':
        skill_name = request.form.get('skill_name', '').strip()
        category = request.form.get('category', '')
        proof_type = request.form.get('proof_type', '')
        proof_url = request.form.get('proof_url', '').strip()
        description = request.form.get('description', '').strip()

        if not skill_name or not category or not proof_type:
            flash('Skill name, category, and proof type are required', 'danger')
            return redirect(url_for('submit_skill'))

        file_path = ''
        if 'proof_file' in request.files:
            file = request.files['proof_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

        skill_data = {
            'student_id': session['user_id'],
            'student_name': session['full_name'],
            'skill_name': skill_name,
            'category': category,
            'proof_type': proof_type,
            'proof_url': proof_url if proof_url else file_path,
            'description': description
        }

        db.submit_skill(skill_data)
        flash('Skill submitted for verification!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('submit_skill.html')

@app.route('/faculty/dashboard')
@role_required('faculty')
def faculty_dashboard():
    pending_skills = db.get_pending_skills()
    return render_template('faculty_dashboard.html', pending_skills=pending_skills)

@app.route('/faculty/verify-skill/<skill_id>', methods=['POST'])
@role_required('faculty')
def verify_skill(skill_id):
    action = request.form.get('action')
    comments = request.form.get('comments', '').strip()
    rating = int(request.form.get('rating', 3))

    skill = db.get_skill_by_id(skill_id)

    if not skill:
        flash('Skill not found', 'danger')
        return redirect(url_for('faculty_dashboard'))

    if action == 'approve':
        db.update_skill_status(skill_id, 'approved', session['user_id'], comments, rating)

        credential_hash = blockchain.create_credential_hash(
            skill['student_id'],
            skill['skill_name'],
            skill['proof_url'],
            session['user_id']
        )

        credential_data = {
            'student_id': skill['student_id'],
            'skill_name': skill['skill_name'],
            'category': skill['category'],
            'proof_url': skill['proof_url'],
            'faculty_id': session['user_id'],
            'faculty_name': session['full_name'],
            'credential_hash': credential_hash,
            'rating': rating
        }

        db.add_credential(credential_data)
        blockchain.add_credential_block(credential_data)

        new_score = blockchain.calculate_credibility_score(skill['student_id'])
        db.update_credibility_score(skill['student_id'], new_score)

        flash('Skill approved and credential created!', 'success')

    elif action == 'reject':
        db.update_skill_status(skill_id, 'rejected', session['user_id'], comments, rating)

        new_score = blockchain.calculate_credibility_score(skill['student_id'])
        db.update_credibility_score(skill['student_id'], new_score)

        flash('Skill rejected', 'warning')

    return redirect(url_for('faculty_dashboard'))

@app.route('/profile/<username>')
def public_profile(username):
    user = db.get_user_by_username(username)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

    credentials = db.get_student_credentials(str(user['_id']))
    skills = db.get_student_skills(str(user['_id']))
    approved_skills = [s for s in skills if s['status'] == 'approved']

    profile_url = request.url

    return render_template('public_profile.html',
                         user=user,
                         credentials=credentials,
                         skills=approved_skills,
                         profile_url=profile_url)

@app.route('/verify/<credential_hash>')
def verify_credential(credential_hash):
    result = blockchain.verify_credential(credential_hash)
    return jsonify(result)

@app.route('/blockchain/verify')
@login_required
def verify_blockchain():
    result = blockchain.verify_chain_integrity()
    return jsonify(result)

if __name__ == '__main__':
    print("="*80)
    print("SKILL CREDENTIALING SYSTEM - STARTING")
    print("="*80)
    print()
    print("✓ Database: mongodb://localhost:27017/skill_credentialing")
    print("✓ Server: http://localhost:5000")
    print("✓ Ready to use!")
    print()
    print("="*80)
    app.run(debug=True, host='0.0.0.0', port=5000)