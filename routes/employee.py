from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, g
from datetime import datetime
from utils.helpers import calculate_experience
from utils.decorators import employee_required

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/dashboard')
@employee_required
def dashboard():
    cursor = g.cursor
    cursor.execute("SELECT COUNT(*) as pending FROM tickets WHERE assigned_to = %s AND status = 'pending'", (session['user_id'],))
    pending = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) as completed FROM tickets WHERE assigned_to = %s AND status = 'completed'", (session['user_id'],))
    completed = cursor.fetchone()['completed']

    cursor.execute("SELECT COUNT(*) as raised FROM tickets WHERE raised_by = %s", (session['user_id'],))
    raised = cursor.fetchone()['raised']

    return render_template('employee/dashboard.html', pending_tickets=pending, completed_tickets=completed, raised_tickets=raised)

@employee_bp.route('/profile')
@employee_required
def profile():
    cursor = g.cursor
    cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.id = %s
    """, (session['user_id'],))
    user = cursor.fetchone()
    experience = calculate_experience(user['experience_start_date']) if user['experience_start_date'] else "0 days"
    return render_template('employee/profile.html', user=user, experience=experience)

@employee_bp.route('/availability', methods=['GET', 'POST'])
@employee_required
def availability():
    cursor = g.cursor
    if request.method == 'POST':
        is_available = request.form.get('is_available') == 'on'
        print(f"Updating availability to {is_available} for user {session['user_id']}")
        cursor.execute("UPDATE users SET is_available = %s WHERE id = %s", (is_available, session['user_id']))
        try:
            cursor.execute("""
                INSERT INTO activity_logs (user_id, status, timestamp)
                VALUES (%s, %s, %s)
            """, (session['user_id'], 1 if is_available else 0, datetime.now()))
            g.db.commit()
            print("Activity log inserted successfully.")
        except Exception as e:
            print(f"Insert failed: {e}")
            
        g.db.commit()
        flash(f'Availability status updated to {"available" if is_available else "unavailable"}!', 'success')
        return redirect(url_for('employee.availability'))

    # Fetch current availability status
    cursor.execute('SELECT is_available FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    return render_template('employee/availability.html', user=user)

@employee_bp.route('/raise_ticket', methods=['GET', 'POST'])
@employee_required
def raise_ticket():
    cursor = g.cursor
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        cursor.execute("INSERT INTO tickets (title, description, raised_by, assigned_to) VALUES (%s, %s, %s, %s)", 
                       (title, description, session['user_id'], assigned_to))
        g.db.commit()
        flash('Ticket raised successfully!', 'success')
        return redirect(url_for('employee.raise_ticket'))

    return render_template('employee/raise_ticket.html')

@employee_bp.route('/get_available_employees')
@employee_required
def get_available_employees():
    cursor = g.cursor
    cursor.execute("""
        SELECT id, name, email FROM users 
        WHERE branch_id = %s AND role = 'employee' AND is_available = 1 AND id != %s
    """, (session['branch_id'], session['user_id']))
    employees = cursor.fetchall()
    return jsonify(employees)

@employee_bp.route('/tickets')
@employee_required
def tickets():
    cursor = g.cursor
    cursor.execute("""
        SELECT t.*, u.name as raised_by_name, u.role as raised_by_role
        FROM tickets t
        JOIN users u ON t.raised_by = u.id
        WHERE t.assigned_to = %s AND t.status = 'pending'
        ORDER BY t.created_at DESC
    """, (session['user_id'],))
    tickets = cursor.fetchall()
    return render_template('employee/tickets.html', tickets=tickets)

@employee_bp.route('/complete_ticket/<int:ticket_id>')
@employee_required
def complete_ticket(ticket_id):
    cursor = g.cursor
    cursor.execute("UPDATE tickets SET status = 'completed', completed_at = %s WHERE id = %s AND assigned_to = %s", 
                   (datetime.now(), ticket_id, session['user_id']))
    cursor.execute("UPDATE users SET tickets_solved = tickets_solved + 1 WHERE id = %s", (session['user_id'],))
    g.db.commit()
    flash('Ticket marked as completed!', 'success')
    return redirect(url_for('employee.tickets'))

@employee_bp.route('/solved_tickets')
@employee_required
def solved_tickets():
    cursor = g.cursor
    cursor.execute("""
        SELECT t.*, u.name as raised_by_name, u.role as raised_by_role
        FROM tickets t
        JOIN users u ON t.raised_by = u.id
        WHERE t.assigned_to = %s AND t.status = 'completed'
        ORDER BY t.completed_at DESC
    """, (session['user_id'],))
    tickets = cursor.fetchall()
    return render_template('employee/solved_tickets.html', tickets=tickets)

@employee_bp.route('/tickets_raised')
@employee_required
def tickets_raised():
    cursor = g.cursor
    cursor.execute("""
        SELECT t.*, u.name as assigned_to_name
        FROM tickets t
        JOIN users u ON t.assigned_to = u.id
        WHERE t.raised_by = %s
        ORDER BY t.created_at DESC
    """, (session['user_id'],))
    tickets = cursor.fetchall()
    return render_template('employee/tickets_raised.html', tickets=tickets)

@employee_bp.route('/reset_password', methods=['GET', 'POST'])
@employee_required
def reset_password():
    cursor = g.cursor
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return redirect(url_for('employee.reset_password'))

        cursor.execute('SELECT password FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()

        if user['password'] != current_password:
            flash('Current password is incorrect!', 'error')
            return redirect(url_for('employee.reset_password'))

        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (new_password, session['user_id']))
        g.db.commit()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('employee.reset_password'))

    return render_template('employee/reset_password.html')

@employee_bp.route('/get_leave_notification_count')
@employee_required
def get_leave_notification_count():
    cursor = g.cursor
    try:
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM leave_applications 
            WHERE user_id = %s 
            AND status != 'pending'
            AND (employee_notification_read = FALSE OR employee_notification_read IS NULL)
        """, (session['user_id'],))
        count = cursor.fetchone()['count']
        return jsonify({'count': count})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'count': 0})

@employee_bp.route('/apply_leave', methods=['GET', 'POST'])
@employee_required
def apply_leave():
    cursor = g.cursor
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form.get('reason', '')

        cursor.execute("""
            INSERT INTO leave_applications (user_id, start_date, end_date, reason, admin_notification_read)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (session['user_id'], start_date, end_date, reason))
        g.db.commit()

        flash('Leave application submitted successfully!', 'success')
        return redirect(url_for('employee.apply_leave'))

    # Mark notifications as read
    cursor.execute("""
        UPDATE leave_applications 
        SET employee_notification_read = TRUE 
        WHERE user_id = %s AND (employee_notification_read = FALSE OR employee_notification_read IS NULL)
    """, (session['user_id'],))
    g.db.commit()

    cursor.execute("""
        SELECT * FROM leave_applications 
        WHERE user_id = %s 
        ORDER BY applied_at DESC
    """, (session['user_id'],))
    leave_applications = cursor.fetchall()

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('employee/apply_leave.html', leave_applications=leave_applications, today=today)
