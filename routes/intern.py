from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pymysql
from utils.helpers import calculate_experience
from utils.decorators import intern_required

intern_bp = Blueprint('intern', __name__)

@intern_bp.route('/dashboard')
@intern_required
def dashboard():
    from app import mysql
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) as pending FROM tickets WHERE assigned_to = %s AND status = 'pending'", (session['user_id'],))
    pending = cursor.fetchone()['pending']

    cursor.execute("SELECT COUNT(*) as completed FROM tickets WHERE assigned_to = %s AND status = 'completed'", (session['user_id'],))
    completed = cursor.fetchone()['completed']

    cursor.close()
    return render_template('intern/dashboard.html', pending_works=pending, completed_works=completed)

@intern_bp.route('/profile')
@intern_required
def profile():
    from app import mysql
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT u.*, b.name as branch_name 
        FROM users u 
        LEFT JOIN branches b ON u.branch_id = b.id 
        WHERE u.id = %s
    """, (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()

    experience = calculate_experience(user['experience_start_date']) if user['experience_start_date'] else "0 days"
    return render_template('intern/profile.html', user=user, experience=experience)

@intern_bp.route('/works')
@intern_required
def works():
    from app import mysql
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT t.*, u.name as raised_by_name
        FROM tickets t
        JOIN users u ON t.raised_by = u.id
        WHERE t.assigned_to = %s AND t.status = 'pending'
        ORDER BY t.created_at DESC
    """, (session['user_id'],))
    works = cursor.fetchall()
    cursor.close()

    return render_template('intern/works.html', works=works)

@intern_bp.route('/complete_work/<int:work_id>')
@intern_required
def complete_work(work_id):
    from app import mysql
    cursor = mysql.connection.cursor()

    cursor.execute("""
        UPDATE tickets SET status = 'completed', completed_at = %s WHERE id = %s AND assigned_to = %s
    """, (datetime.now(), work_id, session['user_id']))

    cursor.execute("UPDATE users SET tickets_solved = tickets_solved + 1 WHERE id = %s", (session['user_id'],))
    mysql.connection.commit()
    cursor.close()

    flash('Work marked as completed!', 'success')
    return redirect(url_for('intern.works'))

@intern_bp.route('/completed_works')
@intern_required
def completed_works():
    from app import mysql
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT t.*, u.name as raised_by_name
        FROM tickets t
        JOIN users u ON t.raised_by = u.id
        WHERE t.assigned_to = %s AND t.status = 'completed'
        ORDER BY t.completed_at DESC
    """, (session['user_id'],))
    works = cursor.fetchall()
    cursor.close()

    return render_template('intern/completed_works.html', works=works)

@intern_bp.route('/reset_password', methods=['GET', 'POST'])
@intern_required
def reset_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return redirect(url_for('intern.reset_password'))

        from app import mysql
        cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT password FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()

        if user['password'] != current_password:
            flash('Current password is incorrect!', 'error')
            cursor.close()
            return redirect(url_for('intern.reset_password'))

        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, session['user_id']))
        mysql.connection.commit()
        cursor.close()

        flash('Password updated successfully!', 'success')
        return redirect(url_for('intern.reset_password'))

    return render_template('intern/reset_password.html')

@intern_bp.before_request
def update_intern_availability():
    if 'user_id' in session and session.get('role') == 'intern':
        from app import mysql
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE users SET is_available = TRUE, last_active = %s WHERE id = %s", (datetime.now(), session['user_id']))
        mysql.connection.commit()
        cursor.close()
