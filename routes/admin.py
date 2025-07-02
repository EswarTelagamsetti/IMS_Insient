from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from utils.helpers import generate_password, calculate_experience
from utils.email_service import send_password_email
from utils.decorators import admin_required
import pymysql

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    from app import mysql
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute('SELECT COUNT(*) as total FROM users WHERE role != "admin"')
    total_users = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as total FROM branches')
    total_branches = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as total FROM tickets WHERE status = "pending"')
    pending_tickets = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as total FROM tickets WHERE status = "completed"')
    completed_tickets = cursor.fetchone()['total']

    cursor.close()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_branches=total_branches,
                           pending_tickets=pending_tickets,
                           completed_tickets=completed_tickets)

@admin_bp.route('/add_branch', methods=['GET', 'POST'])
@admin_required
def add_branch():
    from app import mysql
    if request.method == 'POST':
        branch_name = request.form['branch_name']
        cursor = mysql.connection.cursor()
        try:
            cursor.execute('INSERT INTO branches (name) VALUES (%s)', (branch_name,))
            mysql.connection.commit()
            flash('Branch added successfully!', 'success')
        except Exception:
            flash('Branch name already exists!', 'error')
        cursor.close()
        return redirect(url_for('admin.add_branch'))

    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()

    return render_template('admin/add_branch.html', branches=branches)

@admin_bp.route('/delete_branch/<int:branch_id>')
@admin_required
def delete_branch(branch_id):
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM branches WHERE id = %s', (branch_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Branch deleted successfully!', 'success')
    return redirect(url_for('admin.add_branch'))

@admin_bp.route('/add_participant', methods=['GET', 'POST'])
@admin_required
def add_participant():
    from app import mysql
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        branch_id = request.form['branch_id']
        work_type = request.form['work_type']
        experience = request.form['experience']
        password = generate_password()
        experience_start_date = datetime.now().date()

        if experience:
            if 'year' in experience:
                years = int(experience.split()[0])
                experience_start_date = (datetime.now() - timedelta(days=years*365)).date()
            elif 'month' in experience:
                months = int(experience.split()[0])
                experience_start_date = (datetime.now() - timedelta(days=months*30)).date()

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, role, branch_id, work_type, experience_start_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, email, password, role, branch_id, work_type, experience_start_date))
            mysql.connection.commit()
            send_password_email(email, name, password)
            flash('Participant added successfully! Password sent via email.', 'success')
        except Exception:
            flash('Email already exists!', 'error')
        cursor.close()
        return redirect(url_for('admin.add_participant'))

    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()
    return render_template('admin/add_participant.html', branches=branches)

@admin_bp.route('/assign_ticket', methods=['GET', 'POST'])
@admin_required
def assign_ticket():
    from app import mysql
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO tickets (title, description, raised_by, assigned_to)
            VALUES (%s, %s, %s, %s)
        """, (title, description, session['user_id'], assigned_to))
        mysql.connection.commit()
        cursor.close()
        flash('Ticket assigned successfully!', 'success')
        return redirect(url_for('admin.assign_ticket'))

    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()
    return render_template('admin/assign_ticket.html', branches=branches)

@admin_bp.route('/get_users')
@admin_required
def get_users():
    from app import mysql
    branch_id = request.args.get('branch_id')
    work_type = request.args.get('work_type')
    role = request.args.get('role')
    available_only = request.args.get('available_only') == 'true'

    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    query = "SELECT id, name, email, role, is_available FROM users WHERE role != 'admin'"
    params = []

    if branch_id:
        query += " AND branch_id = %s"
        params.append(branch_id)
    if work_type:
        query += " AND work_type = %s"
        params.append(work_type)
    if role:
        query += " AND role = %s"
        params.append(role)
    if available_only:
        query += " AND is_available = 1"

    cursor.execute(query, params)
    users = cursor.fetchall()
    cursor.close()
    return jsonify(users)

@admin_bp.route('/logs')
@admin_required
def logs():
    from app import mysql
    branch_id = request.args.get('branch_id')
    filter_type = request.args.get('filter', 'all')
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

    query = """
        SELECT t.*, u1.name as raised_by_name, u2.name as assigned_to_name, b.name as branch_name
        FROM tickets t
        JOIN users u1 ON t.raised_by = u1.id
        JOIN users u2 ON t.assigned_to = u2.id
        LEFT JOIN branches b ON u2.branch_id = b.id
        WHERE 1=1
    """
    params = []

    if branch_id:
        query += " AND u2.branch_id = %s"
        params.append(branch_id)
    if filter_type == 'completed':
        query += " AND t.status = 'completed'"
    elif filter_type == 'pending':
        query += " AND t.status = 'pending'"
    elif filter_type == 'this_week':
        query += " AND t.created_at >= %s"
        params.append((datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
    elif filter_type == 'last_week':
        query += " AND t.created_at >= %s AND t.created_at < %s"
        params.append((datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'))
        params.append((datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))

    query += " ORDER BY t.created_at DESC"
    cursor.execute(query, params)
    tickets = cursor.fetchall()

    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()

    return render_template('admin/logs.html', tickets=tickets, branches=branches)

@admin_bp.route('/inactive_employees')
@admin_required
def inactive_employees():
    from app import mysql
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    inactive_time = datetime.now() - timedelta(hours=48)
    cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.last_active < %s AND u.role != 'admin'
        ORDER BY u.last_active ASC
    """, (inactive_time,))
    inactive_users = cursor.fetchall()
    cursor.close()
    return render_template('admin/inactive_employees.html', inactive_users=inactive_users)

@admin_bp.route('/all_employees')
@admin_required
def all_employees():
    from app import mysql
    branch_id = request.args.get('branch_id')
    role = request.args.get('role')
    search = request.args.get('search')
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

    query = """
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.role != 'admin'
    """
    params = []

    if branch_id:
        query += " AND u.branch_id = %s"
        params.append(branch_id)
    if role:
        query += " AND u.role = %s"
        params.append(role)
    if search:
        query += " AND (u.name LIKE %s OR u.email LIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    query += " ORDER BY u.name"
    cursor.execute(query, params)
    employees = cursor.fetchall()

    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()

    return render_template('admin/all_employees.html', employees=employees, branches=branches)

@admin_bp.route('/view_activity')
@admin_required
def view_activity():
    from app import mysql
    selected_date_str = request.args.get('date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.now().date()

    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    start_range = selected_date - timedelta(days=1)
    end_range = selected_date + timedelta(days=1)

    cursor.execute("""
        SELECT al.user_id, u.name, u.role, al.status, al.timestamp
        FROM activity_logs al
        JOIN users u ON al.user_id = u.id
        WHERE al.timestamp BETWEEN %s AND %s
        ORDER BY al.user_id, al.timestamp
    """, (start_range, end_range))
    logs = cursor.fetchall()
    cursor.close()

    from collections import defaultdict
    user_sessions = defaultdict(list)

    for log in logs:
        user_sessions[log['user_id']].append(log)

    activity_data = []
    for user_id, entries in user_sessions.items():
        name = entries[0]['name']
        role = entries[0]['role']
        active_time = timedelta()
        session_start = None

        for entry in entries:
            ts = entry['timestamp']
            status = entry['status']
            if status == 1:
                if session_start is None:
                    session_start = ts
            elif status == 0 and session_start:
                session_start_clipped = max(session_start, datetime.combine(selected_date, datetime.min.time()))
                end_clipped = min(ts, datetime.combine(selected_date, datetime.max.time()))
                if session_start_clipped < end_clipped:
                    active_time += end_clipped - session_start_clipped
                session_start = None

        if session_start:
            session_start_clipped = max(session_start, datetime.combine(selected_date, datetime.min.time()))
            end_clipped = min(datetime.now(), datetime.combine(selected_date, datetime.max.time()))
            if session_start_clipped < end_clipped:
                active_time += end_clipped - session_start_clipped

        if active_time.total_seconds() > 0:
            activity_data.append({
                'name': name,
                'role': role,
                'active_hours': round(active_time.total_seconds() / 3600, 2),
                'last_active': entries[-1]['timestamp']
            })

    return render_template('admin/view_activity.html',
                           selected_date=selected_date,
                           activity_data=activity_data)

@admin_bp.route('/remove_employees', methods=['GET', 'POST'])
@admin_required
def remove_employees():
    from app import mysql
    if request.method == 'POST':
        user_id = request.form['user_id']
        cursor = mysql.connection.cursor()
        cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        mysql.connection.commit()
        cursor.close()
        flash('Employee/Intern removed successfully!', 'success')
        return redirect(url_for('admin.remove_employees'))

    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.role != 'admin'
        ORDER BY u.name
    """)
    users = cursor.fetchall()
    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()

    return render_template('admin/remove_employees.html', users=users, branches=branches)

@admin_bp.route('/leave_applications')
@admin_required
def leave_applications():
    from app import mysql
    status = request.args.get('status')
    branch_id = request.args.get('branch_id')

    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    query = """
        SELECT la.*, u.name as employee_name, u.email as employee_email, 
               b.name as branch_name
        FROM leave_applications la
        JOIN users u ON la.user_id = u.id
        LEFT JOIN branches b ON u.branch_id = b.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND la.status = %s"
        params.append(status)
    if branch_id:
        query += " AND u.branch_id = %s"
        params.append(branch_id)

    query += " ORDER BY la.applied_at DESC"
    cursor.execute(query, params)
    leave_applications = cursor.fetchall()

    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()

    cursor.execute("""
        UPDATE leave_applications 
        SET admin_notification_read = TRUE 
        WHERE status = 'pending'
    """)
    mysql.connection.commit()
    cursor.close()

    return render_template('admin/leave_applications.html',
                           leave_applications=leave_applications,
                           branches=branches)

@admin_bp.route('/get_leave_notification_count')
@admin_required
def get_leave_notification_count():
    from app import mysql
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM leave_applications 
            WHERE status = 'pending'
        """)
        result = cursor.fetchone()
        count = result['count'] if result else 0
        cursor.close()
        return jsonify({'count': count})
    except Exception as e:
        print(f"Error getting admin notification count: {e}")
        cursor.close()
        return jsonify({'count': 0})

@admin_bp.route('/review_leave/<int:leave_id>/<action>')
@admin_required
def review_leave(leave_id, action):
    from app import mysql
    if action not in ['approve', 'reject']:
        flash('Invalid action!', 'error')
        return redirect(url_for('admin.leave_applications'))

    status = 'approved' if action == 'approve' else 'rejected'
    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE leave_applications 
        SET status = %s, reviewed_at = %s, reviewed_by = %s, employee_notification_read = FALSE
        WHERE id = %s
    """, (status, datetime.now(), session['user_id'], leave_id))
    mysql.connection.commit()
    cursor.close()

    flash(f'Leave application {status} successfully!', 'success')
    return redirect(url_for('admin.leave_applications'))
