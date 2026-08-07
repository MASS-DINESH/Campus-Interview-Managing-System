from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import uuid

app = Flask(__name__, static_folder='static', template_folder='templates')
# Replace with a secure random key in production or load from environment
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "replace_this_with_a_real_secret")

DB = 'users.db'
ADMIN_USERNAME = "dinesh"
ADMIN_PASSWORD = "dinesh267"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Create the table if it doesn't exist (with the new schema)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            mobile_no TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
    ''')
    
    # Create login history table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS login_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    
    # Create job requests table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS job_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            mobile_no TEXT NOT NULL,
            email TEXT NOT NULL,
            qualifying_degree TEXT NOT NULL,
            year_of_passing INTEGER NOT NULL,
            district TEXT NOT NULL,
            pin_code TEXT NOT NULL,
            register_no TEXT,
            department TEXT,
            cgpa REAL,
            tenth_percentage REAL,
            twelfth_percentage REAL,
            backlogs INTEGER DEFAULT 0,
            preferred_role TEXT,
            github_url TEXT,
            linkedin_url TEXT,
            photo_path TEXT,
            mark_sheet_10th_path TEXT,
            mark_sheet_12th_path TEXT,
            resume_path TEXT,
            college_mark_sheet_path TEXT,
            status TEXT DEFAULT 'Pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')

    # Migration for existing databases
    for col_def in [
        ('register_no', 'TEXT'),
        ('department', 'TEXT'),
        ('cgpa', 'REAL'),
        ('tenth_percentage', 'REAL'),
        ('twelfth_percentage', 'REAL'),
        ('backlogs', 'INTEGER DEFAULT 0'),
        ('preferred_role', 'TEXT'),
        ('github_url', 'TEXT'),
        ('linkedin_url', 'TEXT')
    ]:
        try:
            conn.execute(f"ALTER TABLE job_requests ADD COLUMN {col_def[0]} {col_def[1]};")
        except sqlite3.OperationalError:
            pass  # Column already exists

    
    # Create support_tickets table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            priority TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            is_read BOOLEAN DEFAULT 0,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to check if a date is recent
def is_recent(date_string, days=7):
    if not date_string:
        return False
    try:
        from datetime import datetime, timedelta
        # Handle different date formats from SQLite
        if ' ' in date_string:
            date_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        else:
            date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        return datetime.now() - date_obj < timedelta(days=days)
    except:
        return False

@app.route('/')
def index():
    # If already logged in go to profile
    if 'username' in session:
        return redirect(url_for('profile'))
    return render_template('login.html')

@app.route('/register_page')
def register_page():
    return render_template('registration.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    mobile_no = (data.get('mobile_no') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    # Validation
    if not all([username, first_name, last_name, mobile_no, email, password, confirm_password]):
        return 'All fields are required', 400
        
    if password != confirm_password:
        return 'Passwords do not match', 400

    hashed = generate_password_hash(password)
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, first_name, last_name, mobile_no, email, password) VALUES (?, ?, ?, ?, ?, ?)',
                     (username, first_name, last_name, mobile_no, email, hashed))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return 'Username or email already exists', 400
    conn.close()
    
    # Return a JSON response with redirect information
    return jsonify({
        'message': 'Registration successful', 
        'redirect': url_for('index')
    }), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return 'Missing fields', 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    if user and check_password_hash(user['password'], password):
        # Update last login
        conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
        
        # Record login history
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        conn.execute('INSERT INTO login_history (user_id, ip_address, user_agent) VALUES (?, ?, ?)',
                     (user['id'], ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        session['username'] = user['username']
        session['user_id'] = user['id']
        session['is_admin'] = (user['username'] == ADMIN_USERNAME)
        return jsonify({'message': 'Login successful', 'redirect': '/profile'}), 200

    conn.close()
    return 'Invalid credentials', 401

# Admin panel main page
@app.route('/admin_panel')
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    # Get stats for dashboard
    conn = get_db_connection()
    
    # Get total users count
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    
    # Get total job requests count
    total_jobs = conn.execute('SELECT COUNT(*) FROM job_requests').fetchone()[0]
    
    # Get pending job requests count
    pending_jobs = conn.execute('SELECT COUNT(*) FROM job_requests WHERE status = "Pending"').fetchone()[0]
    
    # Get total companies (approximate)
    total_companies = conn.execute('SELECT COUNT(DISTINCT email) FROM job_requests').fetchone()[0]
    
    # Get recent job requests
    recent_jobs = conn.execute('''
        SELECT jr.*, u.username 
        FROM job_requests jr 
        LEFT JOIN users u ON jr.user_id = u.id 
        ORDER BY jr.submitted_at DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get recent users
    recent_users = conn.execute('SELECT * FROM users ORDER BY created_at DESC LIMIT 5').fetchall()
    
    # Get recent activity
    recent_activity = conn.execute('''
        SELECT lh.*, u.username 
        FROM login_history lh 
        JOIN users u ON lh.user_id = u.id 
        ORDER BY lh.login_time DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_panel.html', 
                         username=session['username'],
                         total_users=total_users,
                         total_jobs=total_jobs,
                         pending_jobs=pending_jobs,
                         total_companies=total_companies,
                         recent_jobs=recent_jobs,
                         recent_users=recent_users,
                         recent_activity=recent_activity)

# User management page
@app.route('/admin/user_management')
def admin_user_management():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    # Get all users from database
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    
    # Calculate stats
    total_users = len(users)
    active_users = total_users  # Assuming all are active for now
    recent_users = len([u for u in users if is_recent(u['created_at'])]) if users else 0
    
    conn.close()
    
    return render_template('admin_user_management.html', 
                         username=session['username'],
                         users=users,
                         active_users=active_users,
                         recent_users=recent_users)

# Login details page
@app.route('/admin/login_details')
def admin_login_details():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    # Get login history from database
    conn = get_db_connection()
    login_history = conn.execute('''
        SELECT lh.*, u.username, u.first_name, u.last_name 
        FROM login_history lh 
        JOIN users u ON lh.user_id = u.id 
        ORDER BY lh.login_time DESC
    ''').fetchall()
    
    # Calculate stats
    total_logins = len(login_history)
    unique_users = len(set([lh['user_id'] for lh in login_history]))
    
    # Count recent logins (last 24 hours)
    recent_logins = 0
    for lh in login_history:
        if is_recent(lh['login_time'], days=1):
            recent_logins += 1
    
    unique_ips = len(set([lh['ip_address'] for lh in login_history]))
    
    conn.close()
    
    return render_template('login_details.html', 
                         username=session['username'], 
                         login_history=login_history,
                         total_logins=total_logins,
                         unique_users=unique_users,
                         recent_logins=recent_logins,
                         unique_ips=unique_ips)

# About page
@app.route('/about')
def about():
    return render_template('about.html')

# Drives Catalog Page
@app.route('/drives')
def drives():
    return render_template('drives.html')

# Interview Prep Resources Page
@app.route('/resources')
def resources():
    return render_template('resources.html')


# Job request page
@app.route('/job_request')
def job_request():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('job_request.html')

# Submit job request
@app.route('/submit_job_request', methods=['POST'])
def submit_job_request():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get form data
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    mobile_no = request.form.get('mobile_no', '').strip()
    email = request.form.get('email', '').strip()
    qualifying_degree = request.form.get('qualifying_degree', '').strip()
    year_of_passing = request.form.get('year_of_passing', '').strip()
    district = request.form.get('district', '').strip()
    pin_code = request.form.get('pin_code', '').strip()
    
    # Additional Candidate Form Fields
    register_no = request.form.get('register_no', '').strip()
    department = request.form.get('department', '').strip()
    cgpa = request.form.get('cgpa', '').strip()
    tenth_percentage = request.form.get('tenth_percentage', '').strip()
    twelfth_percentage = request.form.get('twelfth_percentage', '').strip()
    backlogs = request.form.get('backlogs', '0').strip()
    preferred_role = request.form.get('preferred_role', '').strip()
    github_url = request.form.get('github_url', '').strip()
    linkedin_url = request.form.get('linkedin_url', '').strip()

    # Validate required fields
    if not all([first_name, last_name, mobile_no, email, qualifying_degree, year_of_passing, district, pin_code]):
        return jsonify({'error': 'All core candidate fields are required'}), 400
    
    # Handle file uploads
    photo_path = save_file(request.files.get('photo'))
    mark_sheet_10th_path = save_file(request.files.get('mark_sheet_10th'))
    mark_sheet_12th_path = save_file(request.files.get('mark_sheet_12th'))
    resume_path = save_file(request.files.get('resume'))
    college_mark_sheet_path = save_file(request.files.get('college_mark_sheet'))
    
    # Validate required files
    if not all([photo_path, mark_sheet_10th_path, mark_sheet_12th_path, resume_path, college_mark_sheet_path]):
        return jsonify({'error': 'All 5 document uploads are required'}), 400
    
    # Save to database
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO job_requests 
            (user_id, first_name, last_name, mobile_no, email, qualifying_degree, year_of_passing, district, pin_code,
             register_no, department, cgpa, tenth_percentage, twelfth_percentage, backlogs, preferred_role, github_url, linkedin_url,
             photo_path, mark_sheet_10th_path, mark_sheet_12th_path, resume_path, college_mark_sheet_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], first_name, last_name, mobile_no, email, qualifying_degree, year_of_passing, district, pin_code,
              register_no, department, cgpa, tenth_percentage, twelfth_percentage, backlogs, preferred_role, github_url, linkedin_url,
              photo_path, mark_sheet_10th_path, mark_sheet_12th_path, resume_path, college_mark_sheet_path))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'Job placement request submitted successfully'}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500


def save_file(file):
    if file and file.filename and allowed_file(file.filename):
        # Generate unique filename
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

# View job requests for user
@app.route('/my_job_requests')
def my_job_requests():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    requests = conn.execute('SELECT * FROM job_requests WHERE user_id = ? ORDER BY submitted_at DESC', 
                           (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('my_job_requests.html', requests=requests)

# Admin login page
@app.route('/admin_login')
def admin_login():
    # Clear any existing session
    session.clear()
    return render_template('admin_login.html')

# Admin authentication
@app.route('/admin_auth', methods=['POST'])
def admin_auth():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return 'Missing fields', 400

    # Check admin credentials
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['username'] = username
        session['is_admin'] = True
        
        # Record admin login
        conn = get_db_connection()
        admin_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if admin_user:
            # Update last login
            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (admin_user['id'],))
            
            # Record login history
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            conn.execute('INSERT INTO login_history (user_id, ip_address, user_agent) VALUES (?, ?, ?)',
                         (admin_user['id'], ip_address, user_agent))
            
            conn.commit()
        conn.close()
        
        return jsonify({'message': 'Admin login successful', 'redirect': '/admin'}), 200

    return 'Invalid admin credentials', 401

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    # Get all users from database
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    
    # Count unread support tickets
    unread_count = conn.execute('SELECT COUNT(*) FROM support_tickets WHERE is_read = 0').fetchone()[0]
    
    conn.close()
    
    return render_template('admin.html', 
                         username=session['username'], 
                         users=users,
                         unread_count=unread_count)

# Admin job requests page
@app.route('/admin/job_requests')
def admin_job_requests():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    job_requests = conn.execute('''
        SELECT jr.*, u.username 
        FROM job_requests jr 
        LEFT JOIN users u ON jr.user_id = u.id 
        ORDER BY jr.submitted_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin_job_requests.html', 
                         username=session['username'],
                         job_requests=job_requests)

# Update job request status
@app.route('/admin/job_request/<int:request_id>', methods=['PUT'])
def update_job_request_status(request_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.get_json() or {}
    status = data.get('status', '').strip()
    
    if status not in ['Accepted', 'Declined', 'Pending']:
        return jsonify({'error': 'Invalid status'}), 400
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE job_requests SET status = ? WHERE id = ?', (status, request_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Job request status updated successfully'}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Delete job request
@app.route('/admin/job_request/<int:request_id>', methods=['DELETE'])
def delete_job_request(request_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    try:
        # Get file paths to delete them
        request_data = conn.execute('SELECT * FROM job_requests WHERE id = ?', (request_id,)).fetchone()
        
        # Delete files
        if request_data:
            for field in ['photo_path', 'mark_sheet_10th_path', 'mark_sheet_12th_path', 'resume_path', 'college_mark_sheet_path']:
                if request_data[field]:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], request_data[field])
                    if os.path.exists(filepath):
                        os.remove(filepath)
        
        # Delete from database
        conn.execute('DELETE FROM job_requests WHERE id = ?', (request_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Job request deleted successfully'}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Get job request details
@app.route('/admin/job_request/<int:request_id>', methods=['GET'])
def get_job_request_details(request_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    job_request = conn.execute('SELECT * FROM job_requests WHERE id = ?', (request_id,)).fetchone()
    conn.close()
    
    if job_request:
        req_dict = dict(job_request)
        return jsonify(req_dict), 200
    else:
        return jsonify({'error': 'Job request not found'}), 404


# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# User stats API endpoint
@app.route('/api/user/stats')
def user_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        # Get user details
        user = conn.execute('SELECT created_at, last_login FROM users WHERE id = ?', (user_id,)).fetchone()
        
        # Get job request stats
        total_requests = conn.execute('SELECT COUNT(*) FROM job_requests WHERE user_id = ?', (user_id,)).fetchone()[0]
        accepted_requests = conn.execute('SELECT COUNT(*) FROM job_requests WHERE user_id = ? AND status = "Accepted"', (user_id,)).fetchone()[0]
        pending_requests = conn.execute('SELECT COUNT(*) FROM job_requests WHERE user_id = ? AND status = "Pending"', (user_id,)).fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'member_since': user['created_at'] if user else None,
            'last_login': user['last_login'] if user else None,
            'total_requests': total_requests,
            'accepted_requests': accepted_requests,
            'pending_requests': pending_requests
        }), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Get user by ID for editing
@app.route('/admin/user/<int:user_id>', methods=['GET'])
def admin_get_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'mobile_no': user['mobile_no'],
            'email': user['email']
        }), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# Update user data
@app.route('/admin/user/<int:user_id>', methods=['PUT'])
def admin_update_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    mobile_no = (data.get('mobile_no') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or None

    if not username or not email or not first_name or not last_name or not mobile_no:
        return jsonify({'error': 'All fields are required'}), 400

    conn = get_db_connection()
    
    try:
        if password:
            # Update with new password
            hashed = generate_password_hash(password)
            conn.execute('UPDATE users SET username = ?, first_name = ?, last_name = ?, mobile_no = ?, email = ?, password = ? WHERE id = ?',
                         (username, first_name, last_name, mobile_no, email, hashed, user_id))
        else:
            # Update without changing password
            conn.execute('UPDATE users SET username = ?, first_name = ?, last_name = ?, mobile_no = ?, email = ? WHERE id = ?',
                         (username, first_name, last_name, mobile_no, email, user_id))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'User updated successfully'}), 200
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Create new user
@app.route('/admin/user', methods=['POST'])
def admin_create_user():
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    mobile_no = (data.get('mobile_no') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not username or not password or not email or not first_name or not last_name or not mobile_no:
        return jsonify({'error': 'All fields are required'}), 400

    hashed = generate_password_hash(password)
    conn = get_db_connection()
    
    try:
        conn.execute('INSERT INTO users (username, first_name, last_name, mobile_no, email, password) VALUES (?, ?, ?, ?, ?, ?)',
                     (username, first_name, last_name, mobile_no, email, hashed))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User created successfully'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username or email already exists'}), 400
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Delete user
@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Help Center Page
@app.route('/help_center')
def help_center():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('help_center.html')

# Submit Support Request
@app.route('/submit_support_request', methods=['POST'])
def submit_support_request():
    if 'username' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    subject = data.get('subject', '').strip()
    priority = data.get('priority', '').strip()
    message = data.get('message', '').strip()

    if not all([name, email, subject, priority, message]):
        return jsonify({'error': 'All fields are required'}), 400

    conn = get_db_connection()
    try:
        user_id = session.get('user_id')
        conn.execute('''
            INSERT INTO support_tickets (user_id, name, email, subject, priority, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, name, email, subject, priority, message))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'Support request submitted successfully'}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Admin Notifications Page
@app.route('/admin/notifications')
def admin_notifications():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Get all support tickets
    support_tickets = conn.execute('''
        SELECT st.*, u.username 
        FROM support_tickets st 
        LEFT JOIN users u ON st.user_id = u.id 
        ORDER BY st.submitted_at DESC
    ''').fetchall()
    
    # Calculate stats
    total_tickets = len(support_tickets)
    pending_tickets = len([t for t in support_tickets if t['status'] == 'pending'])
    urgent_tickets = len([t for t in support_tickets if t['priority'] == 'Urgent'])
    resolved_tickets = len([t for t in support_tickets if t['status'] == 'resolved'])
    unread_count = len([t for t in support_tickets if not t['is_read']])
    
    conn.close()
    
    return render_template('notifications.html', 
                         username=session['username'],
                         support_tickets=support_tickets,
                         total_tickets=total_tickets,
                         pending_tickets=pending_tickets,
                         urgent_tickets=urgent_tickets,
                         resolved_tickets=resolved_tickets,
                         unread_count=unread_count)

# Get ticket details
@app.route('/admin/ticket/<int:ticket_id>')
def get_ticket(ticket_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM support_tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()
    
    if ticket:
        return jsonify({
            'id': ticket['id'],
            'name': ticket['name'],
            'email': ticket['email'],
            'subject': ticket['subject'],
            'priority': ticket['priority'],
            'message': ticket['message'],
            'status': ticket['status'],
            'submitted_at': ticket['submitted_at']
        }), 200
    else:
        return jsonify({'error': 'Ticket not found'}), 404

# Mark ticket as read
@app.route('/admin/mark_ticket_read/<int:ticket_id>', methods=['PUT'])
def mark_ticket_read(ticket_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE support_tickets SET is_read = 1 WHERE id = ?', (ticket_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Mark all tickets as read
@app.route('/admin/mark_all_read', methods=['PUT'])
def mark_all_read():
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE support_tickets SET is_read = 1 WHERE is_read = 0')
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Resolve ticket
@app.route('/admin/resolve_ticket/<int:ticket_id>', methods=['PUT'])
def resolve_ticket(ticket_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE support_tickets SET status = "resolved" WHERE id = ?', (ticket_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Delete ticket
@app.route('/admin/delete_ticket/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Not authorized'}), 403
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM support_tickets WHERE id = ?', (ticket_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('index'))
    # Pass username to template
    return render_template('profile.html', username=session['username'])

@app.route('/profile_management')
def profile_management():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    # Get user data from database
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    if user:
        return render_template('profile_management.html', 
                             username=user['username'], 
                             email=user['email'])
    else:
        return redirect(url_for('index'))

@app.route('/delete_account', methods=['DELETE'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        # Clear the session
        session.clear()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)