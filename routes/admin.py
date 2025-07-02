from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, g
from datetime import datetime, timedelta
from utils.helpers import generate_password, calculate_experience
from utils.email_service import send_password_email
from utils.decorators import admin_required
import pymysql

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
        cursor = g.db.cursor()

        try:
            cursor.execute('INSERT INTO branches (name) VALUES (%s)', (branch_name,))
            g.db.commit()
            flash('Branch added successfully!', 'success')
        except Exception as e:
            flash('Branch name already exists!', 'error')

        cursor.close()
        return redirect(url_for('admin.add_branch'))

    cursor = g.db.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()

    return render_template('admin/add_branch.html', branches=branches)

@admin_bp.route('/delete_branch/<int:branch_id>')
@admin_required
def delete_branch(branch_id):
    cursor = g.db.cursor()
    cursor.execute('DELETE FROM branches WHERE id = %s', (branch_id,))
    g.db.commit()
    cursor.close()

    flash('Branch deleted successfully!', 'success')
    return redirect(url_for('admin.add_branch'))

# The rest of the functions should be similarly updated:
# - Replace "from app import mysql" with nothing (handled globally in app.py)
# - Use "cursor = g.db.cursor()" for regular cursor
# - Use "cursor = g.db.cursor(pymysql.cursors.DictCursor)" for dict cursor
# - Use "g.db.commit()" instead of "mysql.connection.commit()"
# - Remove any "mysql.connection.cursor" usage

# Let me know if you want me to apply these replacements to all other routes as well