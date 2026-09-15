from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-123'

# MySQL Configuration - UPDATE THESE VALUES
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # CHANGE THIS
app.config['MYSQL_DB'] = 'placement_db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql = MySQL(app)

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin):
    def __init__(self, id, username, email, full_name, role, **kwargs):
        self.id = id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    if user:
        return User(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            role=user['role']
        )
    return None

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password'], password):
            user_obj = User(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                full_name=user['full_name'],
                role=user['role']
            )
            login_user(user_obj)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form.get('phone', '')
        department = request.form.get('department', '')
        graduation_year = request.form.get('graduation_year', None)
        cgpa = request.form.get('cgpa', None)
        
        # Check if user exists
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        if cur.fetchone():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        # Insert user
        cur.execute("""
            INSERT INTO users (username, email, password, full_name, phone, department, graduation_year, cgpa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, email, hashed_password, full_name, phone, department, graduation_year, cgpa))
        mysql.connection.commit()
        cur.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    
    if current_user.role == 'admin':
        # Admin dashboard data
        cur.execute("SELECT COUNT(*) as total FROM users WHERE role = 'student'")
        total_students = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM companies")
        total_companies = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM jobs WHERE status = 'open'")
        total_jobs = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM applications")
        total_applications = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM placements")
        total_placements = cur.fetchone()['total']
        
        cur.close()
        
        return render_template('admin.html', 
                             total_students=total_students,
                             total_companies=total_companies,
                             total_jobs=total_jobs,
                             total_applications=total_applications,
                             total_placements=total_placements)
    else:
        # Student dashboard data
        cur.execute("""
            SELECT j.*, c.name as company_name 
            FROM jobs j 
            JOIN companies c ON j.company_id = c.id 
            WHERE j.status = 'open' 
            ORDER BY j.created_at DESC 
            LIMIT 5
        """)
        recent_jobs = cur.fetchall()
        
        cur.execute("""
            SELECT a.*, j.title, c.name as company_name 
            FROM applications a 
            JOIN jobs j ON a.job_id = j.id 
            JOIN companies c ON j.company_id = c.id 
            WHERE a.student_id = %s 
            ORDER BY a.applied_at DESC
        """, (current_user.id,))
        my_applications = cur.fetchall()
        
        cur.close()
        
        return render_template('dashboard.html', 
                             recent_jobs=recent_jobs,
                             my_applications=my_applications)

@app.route('/companies')
@login_required
def companies():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM companies ORDER BY name")
    companies = cur.fetchall()
    cur.close()
    return render_template('companies.html', companies=companies)

@app.route('/jobs')
@login_required
def jobs():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT j.*, c.name as company_name 
        FROM jobs j 
        JOIN companies c ON j.company_id = c.id 
        WHERE j.status = 'open' 
        ORDER BY j.created_at DESC
    """)
    jobs = cur.fetchall()
    cur.close()
    return render_template('jobs.html', jobs=jobs)

@app.route('/jobs/<int:job_id>')
@login_required
def job_detail(job_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT j.*, c.name as company_name, c.description as company_description 
        FROM jobs j 
        JOIN companies c ON j.company_id = c.id 
        WHERE j.id = %s
    """, (job_id,))
    job = cur.fetchone()
    
    # Check if user has already applied
    cur.execute("SELECT * FROM applications WHERE job_id = %s AND student_id = %s", 
                (job_id, current_user.id))
    has_applied = cur.fetchone() is not None
    cur.close()
    
    return render_template('job_detail.html', job=job, has_applied=has_applied)

@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'student':
        flash('Only students can apply for jobs', 'danger')
        return redirect(url_for('jobs'))
    
    cover_letter = request.form.get('cover_letter', '')
    
    cur = mysql.connection.cursor()
    
    # Check if already applied
    cur.execute("SELECT * FROM applications WHERE job_id = %s AND student_id = %s", 
                (job_id, current_user.id))
    if cur.fetchone():
        flash('You have already applied for this job', 'warning')
        return redirect(url_for('job_detail', job_id=job_id))
    
    # Insert application
    cur.execute("""
        INSERT INTO applications (job_id, student_id, cover_letter) 
        VALUES (%s, %s, %s)
    """, (job_id, current_user.id, cover_letter))
    mysql.connection.commit()
    cur.close()
    
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('applications'))

@app.route('/applications')
@login_required
def applications():
    cur = mysql.connection.cursor()
    
    if current_user.role == 'admin':
        # Admin sees all applications
        cur.execute("""
            SELECT a.*, u.full_name, u.email, u.department, u.cgpa,
                   j.title, c.name as company_name
            FROM applications a
            JOIN users u ON a.student_id = u.id
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            ORDER BY a.applied_at DESC
        """)
    else:
        # Student sees only their applications
        cur.execute("""
            SELECT a.*, j.title, c.name as company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            WHERE a.student_id = %s
            ORDER BY a.applied_at DESC
        """, (current_user.id,))
    
    applications = cur.fetchall()
    cur.close()
    
    return render_template('applications.html', applications=applications)

@app.route('/update_application/<int:app_id>', methods=['POST'])
@login_required
@admin_required
def update_application(app_id):
    status = request.form['status']
    
    cur = mysql.connection.cursor()
    cur.execute("UPDATE applications SET status = %s WHERE id = %s", (status, app_id))
    mysql.connection.commit()
    cur.close()
    
    flash('Application status updated!', 'success')
    return redirect(url_for('applications'))

# Admin Routes
@app.route('/admin/companies/add', methods=['POST'])
@login_required
@admin_required
def add_company():
    name = request.form['name']
    description = request.form.get('description', '')
    industry = request.form.get('industry', '')
    website = request.form.get('website', '')
    contact_email = request.form.get('contact_email', '')
    contact_phone = request.form.get('contact_phone', '')
    location = request.form.get('location', '')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO companies (name, description, industry, website, contact_email, contact_phone, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, description, industry, website, contact_email, contact_phone, location))
    mysql.connection.commit()
    cur.close()
    
    flash('Company added successfully!', 'success')
    return redirect(url_for('companies'))

@app.route('/admin/jobs/add', methods=['POST'])
@login_required
@admin_required
def add_job():
    company_id = request.form['company_id']
    title = request.form['title']
    description = request.form.get('description', '')
    job_type = request.form.get('job_type', 'full-time')
    location = request.form.get('location', '')
    salary_range = request.form.get('salary_range', '')
    positions = request.form.get('positions', 1)
    eligibility_criteria = request.form.get('eligibility_criteria', '')
    deadline = request.form.get('deadline', None)
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO jobs (company_id, title, description, job_type, location, salary_range, positions, eligibility_criteria, deadline)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (company_id, title, description, job_type, location, salary_range, positions, eligibility_criteria, deadline))
    mysql.connection.commit()
    cur.close()
    
    flash('Job posted successfully!', 'success')
    return redirect(url_for('jobs'))

@app.route('/admin/placements/add', methods=['POST'])
@login_required
@admin_required
def add_placement():
    student_id = request.form['student_id']
    job_id = request.form['job_id']
    company_id = request.form['company_id']
    package = request.form['package']
    placement_date = request.form['placement_date']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO placements (student_id, job_id, company_id, package, placement_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (student_id, job_id, company_id, package, placement_date))
    mysql.connection.commit()
    cur.close()
    
    flash('Placement record added!', 'success')
    return redirect(url_for('dashboard'))

# API Routes for AJAX
@app.route('/api/stats')
@login_required
@admin_required
def get_stats():
    cur = mysql.connection.cursor()
    
    # Get placement statistics
    cur.execute("""
        SELECT c.name, COUNT(p.id) as placement_count
        FROM placements p
        JOIN companies c ON p.company_id = c.id
        GROUP BY c.name
        ORDER BY placement_count DESC
    """)
    company_stats = cur.fetchall()
    
    # Get monthly applications
    cur.execute("""
        SELECT DATE_FORMAT(applied_at, '%Y-%m') as month, COUNT(*) as count
        FROM applications
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """)
    monthly_stats = cur.fetchall()
    
    cur.close()
    
    return jsonify({
        'company_stats': company_stats,
        'monthly_stats': monthly_stats
    })

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(debug=True, port=5000)