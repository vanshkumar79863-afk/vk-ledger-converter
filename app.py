"""
===========================================
VK LEDGUR CONVERTER - PYTHON FLASK APP ( my python backend )
===========================================
Complete web application for ledger management
Technology: Flask + SQLite + HTML/CSS/JavaScript
Author: Vansh Kumar, BCA Student, PCTE Ludhiana
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
import os
import json
from functools import wraps
import io

# =====================================
# FLASK APP INITIALIZATION
# =====================================

app = Flask(__name__)
app.secret_key = 'vk_ledgur_secret_key_2026'  # Secret key for sessions

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# =====================================
# DATABASE SETUP
# =====================================

DATABASE = 'vk_ledger.db'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with tables"""
    db = get_db()
    cursor = db.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create ledgers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ledgers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ledger_name TEXT NOT NULL,
            account_name TEXT,
            account_number TEXT,
            sheet_number TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create ledger_entries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ledger_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            details TEXT,
            reference TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            FOREIGN KEY (ledger_id) REFERENCES ledgers(id)
        )
    ''')
    
    db.commit()
    db.close()

# Initialize database on startup
init_db()

# =====================================
# HELPER FUNCTIONS
# =====================================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_by_id(user_id):
    """Get user by ID"""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    return user

def get_user_ledgers(user_id, status=None):
    """Get all ledgers for user"""
    db = get_db()
    if status:
        ledgers = db.execute(
            'SELECT * FROM ledgers WHERE user_id = ? AND status = ? ORDER BY updated_at DESC',
            (user_id, status)
        ).fetchall()
    else:
        ledgers = db.execute(
            'SELECT * FROM ledgers WHERE user_id = ? ORDER BY updated_at DESC',
            (user_id,)
        ).fetchall()
    db.close()
    return ledgers

def get_ledger_entries(ledger_id):
    """Get all entries for ledger"""
    db = get_db()
    entries = db.execute(
        'SELECT * FROM ledger_entries WHERE ledger_id = ? ORDER BY entry_date ASC',
        (ledger_id,)
    ).fetchall()
    db.close()
    return entries

def calculate_balance(entries):
    """Calculate running balance for entries"""
    balance = 0
    calculated_entries = []

    for entry in entries:
        balance += (entry['debit'] - entry['credit'])

        # Convert SQLite Row into a normal dictionary
        entry_dict = dict(entry)

        # Now we can safely add/update the balance
        entry_dict['balance'] = balance

        calculated_entries.append(entry_dict)

    return calculated_entries

def user_owns_ledger(ledger_id, user_id):
    """Check if user owns ledger (security)"""
    db = get_db()
    ledger = db.execute(
        'SELECT user_id FROM ledgers WHERE id = ?',
        (ledger_id,)
    ).fetchone()
    db.close()
    if not ledger:
        return False
    return ledger['user_id'] == user_id

def format_currency(amount):
    """Format amount as currency"""
    return f"₹ {amount:,.2f}"

# =====================================
# ROUTES - AUTHENTICATION
# =====================================

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        # Validation
        if not full_name or len(full_name) < 3:
            errors.append("Full name must be at least 3 characters")
        
        if not username or len(username) < 3 or len(username) > 50:
            errors.append("Username must be 3-50 characters")
        
        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if not errors:
            db = get_db()
            
            # Check if username exists
            existing_user = db.execute(
                'SELECT id FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            
            if existing_user:
                errors.append("Username already taken")
            else:
                # Insert new user
                hashed_password = generate_password_hash(password)
                try:
                    db.execute(
                        'INSERT INTO users (full_name, username, password) VALUES (?, ?, ?)',
                        (full_name, username, hashed_password)
                    )
                    db.commit()
                    db.close()
                    return redirect(url_for('login'))
                except Exception as e:
                    errors.append(f"Registration failed: {str(e)}")
            
            db.close()
        
        return render_template('signup.html', errors=errors)
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        errors = []
        
        if not username or not password:
            errors.append("Username and password required")
        
        if not errors:
            db = get_db()
            user = db.execute(
                'SELECT * FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            db.close()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            else:
                errors.append("Invalid username or password")
        
        return render_template('login.html', errors=errors)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))

# =====================================
# ROUTES - DASHBOARD & MAIN
# =====================================

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_id = session['user_id']
    
    db = get_db()
    
    # Get statistics
    saved_count = db.execute(
        'SELECT COUNT(*) as count FROM ledgers WHERE user_id = ? AND status = "saved"',
        (user_id,)
    ).fetchone()['count']
    
    draft_count = db.execute(
        'SELECT COUNT(*) as count FROM ledgers WHERE user_id = ? AND status = "draft"',
        (user_id,)
    ).fetchone()['count']
    
    # Get recent ledgers
    recent_ledgers = db.execute(
        'SELECT * FROM ledgers WHERE user_id = ? ORDER BY updated_at DESC LIMIT 5',
        (user_id,)
    ).fetchall()
    
    db.close()
    
    return render_template('dashboard.html',
                         username=session.get('username'),
                         saved_count=saved_count,
                         draft_count=draft_count,
                         total_count=saved_count + draft_count,
                         recent_ledgers=recent_ledgers)

# =====================================
# ROUTES - LEDGER MANAGEMENT
# =====================================

@app.route('/create_ledger', methods=['GET', 'POST'])
@login_required
def create_ledger():
    """Create new ledger"""
    if request.method == 'POST':
        ledger_name = request.form.get('ledger_name', '').strip()
        account_name = request.form.get('account_name', '').strip()
        account_number = request.form.get('account_number', '').strip()
        sheet_number = request.form.get('sheet_number', '').strip()
        
        if not ledger_name:
            return render_template('create_ledger.html', error='Ledger name required')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO ledgers (user_id, ledger_name, account_name, account_number, sheet_number) VALUES (?, ?, ?, ?, ?)',
            (session['user_id'], ledger_name, account_name, account_number, sheet_number)
        )
        db.commit()
        ledger_id = cursor.lastrowid
        db.close()
        
        return redirect(url_for('editor', ledger_id=ledger_id))
    
    return render_template('create_ledger.html')

@app.route('/ledger/<int:ledger_id>/editor')
@login_required
def editor(ledger_id):
    """Edit ledger entries"""
    if not user_owns_ledger(ledger_id, session['user_id']):
        return "Unauthorized", 403
    
    db = get_db()
    ledger = db.execute(
        'SELECT * FROM ledgers WHERE id = ?',
        (ledger_id,)
    ).fetchone()
    db.close()
    
    if not ledger:
        return "Ledger not found", 404
    
    entries = get_ledger_entries(ledger_id)
    entries = calculate_balance(entries)
    
    return render_template('editor.html', ledger=ledger, entries=entries)

@app.route('/ledger/<int:ledger_id>/view')
@login_required
def view_ledger(ledger_id):
    """View ledger"""
    if not user_owns_ledger(ledger_id, session['user_id']):
        return "Unauthorized", 403
    
    db = get_db()
    ledger = db.execute(
        'SELECT * FROM ledgers WHERE id = ?',
        (ledger_id,)
    ).fetchone()
    db.close()
    
    if not ledger:
        return "Ledger not found", 404
    
    entries = get_ledger_entries(ledger_id)
    entries = calculate_balance(entries)
    
    return render_template('view_ledger.html', ledger=ledger, entries=entries)

@app.route('/ledger/<int:ledger_id>/delete', methods=['POST'])
@login_required
def delete_ledger(ledger_id):
    """Delete ledger"""
    if not user_owns_ledger(ledger_id, session['user_id']):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    db = get_db()
    db.execute('DELETE FROM ledger_entries WHERE ledger_id = ?', (ledger_id,))
    db.execute('DELETE FROM ledgers WHERE id = ?', (ledger_id,))
    db.commit()
    db.close()
    
    return jsonify({'success': True})

@app.route('/ledger/<int:ledger_id>/save', methods=['POST'])
@login_required
def save_ledger(ledger_id):
    """Save ledger"""
    if not user_owns_ledger(ledger_id, session['user_id']):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    db = get_db()
    db.execute(
        'UPDATE ledgers SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        ('saved', ledger_id)
    )
    db.commit()
    db.close()
    
    return jsonify({'success': True})

# =====================================
# ROUTES - ENTRIES (API)
# =====================================

@app.route('/api/ledger/<int:ledger_id>/entries', methods=['GET', 'POST'])
@login_required
def entries_api(ledger_id):
    """Get or add entries via API"""
    if not user_owns_ledger(ledger_id, session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.get_json()
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO ledger_entries (ledger_id, entry_date, details, reference, debit, credit) VALUES (?, ?, ?, ?, ?, ?)',
            (ledger_id, data['entry_date'], data['details'], data.get('reference', ''), 
             float(data.get('debit', 0)), float(data.get('credit', 0)))
        )
        db.commit()
        
        # Recalculate all balances
        entries = db.execute(
            'SELECT * FROM ledger_entries WHERE ledger_id = ? ORDER BY entry_date ASC',
            (ledger_id,)
        ).fetchall()
        
        balance = 0
        for entry in entries:
            balance += (entry['debit'] - entry['credit'])
            db.execute(
                'UPDATE ledger_entries SET balance = ? WHERE id = ?',
                (balance, entry['id'])
            )
        
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'entry_id': cursor.lastrowid})
    
    entries = get_ledger_entries(ledger_id)
    entries = calculate_balance(entries)
    
    return jsonify([{
        'id': e['id'],
        'entry_date': e['entry_date'],
        'details': e['details'],
        'reference': e['reference'],
        'debit': e['debit'],
        'credit': e['credit'],
        'balance': e['balance']
    } for e in entries])

@app.route('/api/entry/<int:entry_id>', methods=['PUT', 'DELETE'])
@login_required
def entry_detail(entry_id):
    """Update or delete entry"""
    db = get_db()
    entry = db.execute('SELECT ledger_id FROM ledger_entries WHERE id = ?', (entry_id,)).fetchone()
    
    if not entry or not user_owns_ledger(entry['ledger_id'], session['user_id']):
        return jsonify({'error': 'Unauthorized'}), 403
    
    ledger_id = entry['ledger_id']
    
    if request.method == 'PUT':
        data = request.get_json()
        db.execute(
            'UPDATE ledger_entries SET debit = ?, credit = ? WHERE id = ?',
            (float(data.get('debit', 0)), float(data.get('credit', 0)), entry_id)
        )
        db.commit()
        
        # Recalculate balances
        entries = db.execute(
            'SELECT * FROM ledger_entries WHERE ledger_id = ? ORDER BY entry_date ASC',
            (ledger_id,)
        ).fetchall()
        
        balance = 0
        for e in entries:
            balance += (e['debit'] - e['credit'])
            db.execute(
                'UPDATE ledger_entries SET balance = ? WHERE id = ?',
                (balance, e['id'])
            )
        
        db.commit()
        db.close()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.execute('DELETE FROM ledger_entries WHERE id = ?', (entry_id,))
        db.commit()
        
        # Recalculate balances
        entries = db.execute(
            'SELECT * FROM ledger_entries WHERE ledger_id = ? ORDER BY entry_date ASC',
            (ledger_id,)
        ).fetchall()
        
        balance = 0
        for e in entries:
            balance += (e['debit'] - e['credit'])
            db.execute(
                'UPDATE ledger_entries SET balance = ? WHERE id = ?',
                (balance, e['id'])
            )
        
        db.commit()
        db.close()
        return jsonify({'success': True})

# =====================================
# ROUTES - LIST PAGES
# =====================================

@app.route('/saved')
@login_required
def saved_ledgers():
    """View saved ledgers"""
    ledgers = get_user_ledgers(session['user_id'], 'saved')
    return render_template('saved_ledgers.html', ledgers=ledgers)

@app.route('/drafts')
@login_required
def drafts():
    """View draft ledgers"""
    ledgers = get_user_ledgers(session['user_id'], 'draft')
    return render_template('drafts.html', ledgers=ledgers)

@app.route('/profile')
@login_required
def profile():
    """User profile"""
    user = get_user_by_id(session['user_id'])
    db = get_db()
    stats = db.execute(
        '''SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'saved' THEN 1 ELSE 0 END) as saved,
            SUM(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) as draft
        FROM ledgers WHERE user_id = ?''',
        (session['user_id'],)
    ).fetchone()
    db.close()
    
    return render_template('profile.html', user=user, stats=stats)

# =====================================
# ROUTES - EXPORT/DOWNLOAD
# =====================================

@app.route('/ledger/<int:ledger_id>/export/pdf')
@login_required
def export_pdf(ledger_id):
    """Export ledger as PDF"""
    if not user_owns_ledger(ledger_id, session['user_id']):
        return "Unauthorized", 403
    
    db = get_db()
    ledger = db.execute('SELECT * FROM ledgers WHERE id = ?', (ledger_id,)).fetchone()
    db.close()
    
    if not ledger:
        return "Ledger not found", 404
    
    entries = get_ledger_entries(ledger_id)
    entries = calculate_balance(entries)
    
    # Generate HTML for PDF
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #001F3F; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #001F3F; color: white; }}
            .header {{ margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{ledger['ledger_name']}</h1>
            <p><strong>Account:</strong> {ledger['account_name']}</p>
            <p><strong>Account Number:</strong> {ledger['account_number']}</p>
            <p><strong>Sheet Number:</strong> {ledger['sheet_number']}</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Details</th>
                    <th>Reference</th>
                    <th>Debit</th>
                    <th>Credit</th>
                    <th>Balance</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for entry in entries:
        html_content += f"""
                <tr>
                    <td>{entry['entry_date']}</td>
                    <td>{entry['details']}</td>
                    <td>{entry['reference']}</td>
                    <td>{entry['debit']:,.2f}</td>
                    <td>{entry['credit']:,.2f}</td>
                    <td>{entry['balance']:,.2f}</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # Return as file (simple HTML download - can be printed to PDF)
    return send_file(
        io.BytesIO(html_content.encode()),
        mimetype='text/html',
        as_attachment=True,
        download_name=f'ledger_{ledger_id}.html'
    )

@app.route('/ledger/<int:ledger_id>/export/csv')
@login_required
def export_csv(ledger_id):
    """Export ledger as CSV"""
    if not user_owns_ledger(ledger_id, session['user_id']):
        return "Unauthorized", 403
    
    db = get_db()
    ledger = db.execute('SELECT * FROM ledgers WHERE id = ?', (ledger_id,)).fetchone()
    db.close()
    
    if not ledger:
        return "Ledger not found", 404
    
    entries = get_ledger_entries(ledger_id)
    entries = calculate_balance(entries)
    
    # Generate CSV
    csv_content = f"Ledger: {ledger['ledger_name']}\n"
    csv_content += f"Account: {ledger['account_name']}\n"
    csv_content += f"Account Number: {ledger['account_number']}\n"
    csv_content += f"Sheet Number: {ledger['sheet_number']}\n\n"
    csv_content += "Date,Details,Reference,Debit,Credit,Balance\n"
    
    for entry in entries:
        csv_content += f"{entry['entry_date']},{entry['details']},{entry['reference']},{entry['debit']},{entry['credit']},{entry['balance']}\n"
    
    return send_file(
        io.BytesIO(csv_content.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'ledger_{ledger_id}.csv'
    )

# =====================================
# ERROR HANDLERS
# =====================================

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# =====================================
# RUN APP
# =====================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
