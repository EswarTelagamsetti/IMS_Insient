from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, g
from datetime import datetime, timedelta
from utils.helpers import generate_password
from utils.email_service import send_password_email
from utils.decorators import admin_required
from collections import defaultdict

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    cursor = g.cursor

    cursor.execute('SELECT COUNT(*) as total FROM users WHERE role != "admin"')
    total_users = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as total FROM branches')
    total_branches = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as total FROM tickets WHERE status = "pending"')
    pending_tickets = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as total FROM tickets WHERE status = "completed"')
    completed_tickets = cursor.fetchone()['total']

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_branches=total_branches,
                           pending_tickets=pending_tickets,
                           completed_tickets=completed_tickets)


@admin_bp.route('/add_branch', methods=['GET', 'POST'])
@admin_required
def add_branch():
    if request.method == 'POST':
        branch_name = request.form['branch_name']
        try:
            g.cursor.execute('INSERT INTO branches (name) VALUES (%s)', (branch_name,))
            g.db.commit()
            flash('Branch added successfully!', 'success')
        except Exception:
            flash('Branch name already exists!', 'error')
        return redirect(url_for('admin.add_branch'))

    g.cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = g.cursor.fetchall()
    return render_template('admin/add_branch.html', branches=branches)


@admin_bp.route('/delete_branch/<int:branch_id>')
@admin_required
def delete_branch(branch_id):
    g.cursor.execute('DELETE FROM branches WHERE id = %s', (branch_id,))
    g.db.commit()
    flash('Branch deleted successfully!', 'success')
    return redirect(url_for('admin.add_branch'))


@admin_bp.route('/add_participant', methods=['GET', 'POST'])
@admin_required
def add_participant():
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

        try:
            g.cursor.execute("""
                INSERT INTO users (name, email, password, role, branch_id, work_type, experience_start_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, email, password, role, branch_id, work_type, experience_start_date))
            g.db.commit()
            send_password_email(email, name, password)
            flash('Participant added successfully! Password sent via email.', 'success')
        except Exception:
            flash('Email already exists!', 'error')
        return redirect(url_for('admin.add_participant'))

    g.cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = g.cursor.fetchall()
    return render_template('admin/add_participant.html', branches=branches)


@admin_bp.route('/assign_ticket', methods=['GET', 'POST'])
@admin_required
def assign_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        g.cursor.execute("""
            INSERT INTO tickets (title, description, raised_by, assigned_to)
            VALUES (%s, %s, %s, %s)
        """, (title, description, session['user_id'], assigned_to))
        g.db.commit()
        flash('Ticket assigned successfully!', 'success')
        return redirect(url_for('admin.assign_ticket'))

    g.cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = g.cursor.fetchall()
    return render_template('admin/assign_ticket.html', branches=branches)


@admin_bp.route('/get_users')
@admin_required
def get_users():
    branch_id = request.args.get('branch_id')
    work_type = request.args.get('work_type')
    role = request.args.get('role')
    available_only = request.args.get('available_only') == 'true'

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

    g.cursor.execute(query, params)
    users = g.cursor.fetchall()
    return jsonify(users)


@admin_bp.route('/logs')
@admin_required
def logs():
    branch_id = request.args.get('branch_id')
    filter_type = request.args.get('filter', 'all')

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
    g.cursor.execute(query, params)
    tickets = g.cursor.fetchall()

    g.cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = g.cursor.fetchall()

    return render_template('admin/logs.html', tickets=tickets, branches=branches)


@admin_bp.route('/inactive_employees')
@admin_required
def inactive_employees():
    inactive_time = datetime.now() - timedelta(hours=48)
    g.cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.last_active < %s AND u.role != 'admin'
        ORDER BY u.last_active ASC
    """, (inactive_time,))
    inactive_users = g.cursor.fetchall()
    return render_template('admin/inactive_employees.html', inactive_users=inactive_users)


@admin_bp.route('/all_employees')
@admin_required
def all_employees():
    branch_id = request.args.get('branch_id')
    role = request.args.get('role')
    search = request.args.get('search')

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
    g.cursor.execute(query, params)
    employees = g.cursor.fetchall()

    g.cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = g.cursor.fetchall()

    return render_template('admin/all_employees.html', employees=employees, branches=branches)


@admin_bp.route('/view_activity')
@admin_required
def view_activity():
    selected_date_str = request.args.get('date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.now().date()

    start_range = selected_date - timedelta(days=1)
    end_range = selected_date + timedelta(days=1)

    g.cursor.execute("""
        SELECT al.user_id, u.name, u.role, al.status, al.timestamp
        FROM activity_logs al
        JOIN users u ON al.user_id = u.id
        WHERE al.timestamp BETWEEN %s AND %s
        ORDER BY al.user_id, al.timestamp
    """, (start_range, end_range))

    logs = g.cursor.fetchall()
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
    if request.method == 'POST':
        user_id = request.form['user_id']
        g.cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
        g.db.commit()
        flash('Employee/Intern removed successfully!', 'success')
        return redirect(url_for('admin.remove_employees'))

    g.cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.role != 'admin'
        ORDER BY u.name
    """)
    users = g.cursor.fetchall()
    g.cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = g.cursor.fetchall()

    return render_template('admin/remove_employees.html', users=users, branches=branches)


@admin_bp.route('/leave_applications')
@admin_required
def leave_applications():
    status = request.args.get('status')
    branch_id = request.args.get('branch_id')

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
    g.cursor.execute(query, params)
    leave_applications = g.cursor.fetchall()

    g.cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = g.cursor.fetchall()

    g.cursor.execute("""
        UPDATE leave_applications 
        SET admin_notification_read = TRUE 
        WHERE status = 'pending'
    """)
    g.db.commit()

    return render_template('admin/leave_applications.html',
                           leave_applications=leave_applications,
                           branches=branches)


@admin_bp.route('/get_leave_notification_count')
@admin_required
def get_leave_notification_count():
    try:
        g.cursor.execute("""
            SELECT COUNT(*) as count 
            FROM leave_applications 
            WHERE status = 'pending'
        """)
        result = g.cursor.fetchone()
        count = result['count'] if result else 0
        return jsonify({'count': count})
    except Exception as e:
        print(f"Error getting admin notification count: {e}")
        return jsonify({'count': 0})


@admin_bp.route('/review_leave/<int:leave_id>/<action>')
@admin_required
def review_leave(leave_id, action):
    if action not in ['approve', 'reject']:
        flash('Invalid action!', 'error')
        return redirect(url_for('admin.leave_applications'))

    status = 'approved' if action == 'approve' else 'rejected'
    g.cursor.execute("""
        UPDATE leave_applications 
        SET status = %s, reviewed_at = %s, reviewed_by = %s, employee_notification_read = FALSE
        WHERE id = %s
    """, (status, datetime.now(), session['user_id'], leave_id))
    g.db.commit()

    flash(f'Leave application {status} successfully!', 'success')
    return redirect(url_for('admin.leave_applications'))

@admin_bp.route('/view_admins')
@admin_required
def view_admins():
    search = request.args.get('search')
    query = "SELECT * FROM users WHERE role = 'admin'"
    params = []

    if search:
        query += " AND (name LIKE %s OR email LIKE %s)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    query += " ORDER BY name"
    g.cursor.execute(query, params)
    admins = g.cursor.fetchall()

    return render_template('admin/view_admins.html', admins=admins)

@admin_bp.route('/remove_admins', methods=['GET', 'POST'])
@admin_required
def remove_admins():
    if request.method == 'POST':
        user_id = request.form['user_id']

        # Prevent self-deletion
        if int(user_id) == session['user_id']:
            flash("You can't remove yourself!", 'error')
            return redirect(url_for('admin.remove_admins'))

        # Double check the user is actually an admin
        g.cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'admin'", (user_id,))
        user = g.cursor.fetchone()
        if not user:
            flash('Invalid admin user or already removed.', 'error')
            return redirect(url_for('admin.remove_admins'))

        g.cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        g.db.commit()
        flash(f"Admin '{user['name']}' removed successfully!", 'success')
        return redirect(url_for('admin.remove_admins'))

    # Fetch all admins except the one currently logged in
    g.cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.role = 'admin' AND u.id != %s
        ORDER BY u.name
    """, (session['user_id'],))
    admins = g.cursor.fetchall()

    return render_template('admin/remove_admins.html', users=admins)
