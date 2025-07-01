from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import datetime, timedelta
from utils.helpers import calculate_experience
from utils.decorators import employee_required
from database.models import Database, User

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/dashboard')
@employee_required
def dashboard():
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get user stats
    cursor.execute("""
        SELECT COUNT(*) as pending FROM tickets WHERE assigned_to = %s AND status = 'pending'
    """, (session['user_id'],))
    pending_tickets = cursor.fetchone()['pending']
    
    cursor.execute("""
        SELECT COUNT(*) as completed FROM tickets WHERE assigned_to = %s AND status = 'completed'
    """, (session['user_id'],))
    completed_tickets = cursor.fetchone()['completed']
    
    cursor.execute("""
        SELECT COUNT(*) as raised FROM tickets WHERE raised_by = %s
    """, (session['user_id'],))
    raised_tickets = cursor.fetchone()['raised']
    
    cursor.close()
    
    return render_template('employee/dashboard.html',
                         pending_tickets=pending_tickets,
                         completed_tickets=completed_tickets,
                         raised_tickets=raised_tickets)

@employee_bp.route('/profile')
@employee_required
def profile():
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.id = %s
    """, (session['user_id'],))
    
    user = cursor.fetchone()
    cursor.close()
    
    # Calculate experience
    if user['experience_start_date']:
        experience = calculate_experience(user['experience_start_date'])
    else:
        experience = "0 days"
    
    return render_template('employee/profile.html', user=user, experience=experience)

@employee_bp.route('/availability', methods=['GET', 'POST'])
@employee_required
def availability():
    from app import mysql
    user_model = User(Database(mysql))
    if request.method == 'POST':
        is_available = request.form.get('is_available') == 'on'
        user_model.update_availability(session['user_id'], is_available)
        status = "available" if is_available else "unavailable"
        flash(f'Availability status updated to {status}!', 'success')
        return redirect(url_for('employee.availability'))
    
    # Get current availability status
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT is_available FROM users WHERE id = %s', (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    
    return render_template('employee/availability.html', user=user)

@employee_bp.route('/raise_ticket', methods=['GET', 'POST'])
@employee_required
def raise_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        
        from app import mysql
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO tickets (title, description, raised_by, assigned_to)
            VALUES (%s, %s, %s, %s)
        """, (title, description, session['user_id'], assigned_to))
        mysql.connection.commit()
        cursor.close()
        
        flash('Ticket raised successfully!', 'success')
        return redirect(url_for('employee.raise_ticket'))
    
    return render_template('employee/raise_ticket.html')

@employee_bp.route('/get_available_employees')
@employee_required
def get_available_employees():
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("""
        SELECT id, name, email FROM users 
        WHERE branch_id = %s AND role = 'employee' AND is_available = 1 AND id != %s
    """, (session['branch_id'], session['user_id']))
    
    employees = cursor.fetchall()
    cursor.close()
    
    return jsonify(employees)

@employee_bp.route('/tickets')
@employee_required
def tickets():
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("""
        SELECT t.*, u.name as raised_by_name, u.role as raised_by_role
        FROM tickets t
        JOIN users u ON t.raised_by = u.id
        WHERE t.assigned_to = %s AND t.status = 'pending'
        ORDER BY t.created_at DESC
    """, (session['user_id'],))
    
    tickets = cursor.fetchall()
    cursor.close()
    
    return render_template('employee/tickets.html', tickets=tickets)

@employee_bp.route('/complete_ticket/<int:ticket_id>')
@employee_required
def complete_ticket(ticket_id):
    from app import mysql
    cursor = mysql.connection.cursor()
    
    cursor.execute("""
        UPDATE tickets SET status = 'completed', completed_at = %s WHERE id = %s AND assigned_to = %s
    """, (datetime.now(), ticket_id, session['user_id']))
    
    # Update tickets solved count
    cursor.execute("""
        UPDATE users SET tickets_solved = tickets_solved + 1 WHERE id = %s
    """, (session['user_id'],))
    
    mysql.connection.commit()
    cursor.close()
    
    flash('Ticket marked as completed!', 'success')
    return redirect(url_for('employee.tickets'))

@employee_bp.route('/solved_tickets')
@employee_required
def solved_tickets():
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("""
        SELECT t.*, u.name as raised_by_name, u.role as raised_by_role
        FROM tickets t
        JOIN users u ON t.raised_by = u.id
        WHERE t.assigned_to = %s AND t.status = 'completed'
        ORDER BY t.completed_at DESC
    """, (session['user_id'],))
    
    tickets = cursor.fetchall()
    cursor.close()
    
    return render_template('employee/solved_tickets.html', tickets=tickets)

@employee_bp.route('/tickets_raised')
@employee_required
def tickets_raised():
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("""
        SELECT t.*, u.name as assigned_to_name
        FROM tickets t
        JOIN users u ON t.assigned_to = u.id
        WHERE t.raised_by = %s
        ORDER BY t.created_at DESC
    """, (session['user_id'],))
    
    tickets = cursor.fetchall()
    cursor.close()
    
    return render_template('employee/tickets_raised.html', tickets=tickets)

@employee_bp.route('/reset_password', methods=['GET', 'POST'])
@employee_required
def reset_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return redirect(url_for('employee.reset_password'))
        
        from app import mysql
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute('SELECT password FROM users WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        
        if user['password'] != current_password:
            flash('Current password is incorrect!', 'error')
            cursor.close()
            return redirect(url_for('employee.reset_password'))
        
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (new_password, session['user_id']))
        mysql.connection.commit()
        cursor.close()
        
        flash('Password updated successfully!', 'success')
        return redirect(url_for('employee.reset_password'))
    
    return render_template('employee/reset_password.html')

@employee_bp.route('/get_leave_notification_count')
@employee_required
def get_leave_notification_count():
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM leave_applications 
            WHERE user_id = %s 
            AND status != 'pending'
            AND (employee_notification_read = FALSE OR employee_notification_read IS NULL)
        """, (session['user_id'],))
        result = cursor.fetchone()
        count = result['count'] if result else 0
        
        cursor.close()
        return jsonify({'count': count})
    except Exception as e:
        print(f"Error getting employee notification count: {e}")
        cursor.close()
        return jsonify({'count': 0})

@employee_bp.route('/apply_leave', methods=['GET', 'POST'])
@employee_required
def apply_leave():
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form.get('reason', '')
        
        from app import mysql
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO leave_applications (user_id, start_date, end_date, reason, admin_notification_read)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (session['user_id'], start_date, end_date, reason))
        mysql.connection.commit()
        cursor.close()
        
        flash('Leave application submitted successfully!', 'success')
        return redirect(url_for('employee.apply_leave'))
    
    # Get user's leave applications and mark notifications as read
    from app import mysql
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Mark notifications as read
    cursor.execute("""
        UPDATE leave_applications 
        SET employee_notification_read = TRUE 
        WHERE user_id = %s AND (employee_notification_read = FALSE OR employee_notification_read IS NULL)
    """, (session['user_id'],))
    mysql.connection.commit()
    
    cursor.execute("""
        SELECT * FROM leave_applications 
        WHERE user_id = %s 
        ORDER BY applied_at DESC
    """, (session['user_id'],))
    leave_applications = cursor.fetchall()
    cursor.close()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('employee/apply_leave.html', 
                         leave_applications=leave_applications, 
                         today=today)
