from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import pymysql
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    from app import mysql

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)

        if role == 'admin':
            cursor.execute('SELECT * FROM users WHERE email = %s AND role = %s', (email, role))
            user = cursor.fetchone()

            if user and user['password'] == password:  # Plain text for admin
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['email'] = user['email']
                session['role'] = user['role']

                cursor.execute('UPDATE users SET last_active = %s WHERE id = %s', (datetime.now(), user['id']))
                mysql.connection.commit()

                cursor.close()
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid credentials!', 'error')

        else:
            branch_name = request.form['branch']
            cursor.execute("""
                SELECT u.*, b.name as branch_name 
                FROM users u 
                JOIN branches b ON u.branch_id = b.id 
                WHERE u.email = %s AND u.role = %s AND b.name = %s
            """, (email, role, branch_name))
            user = cursor.fetchone()

            if user and user['password'] == password:  # Plain text password
                session['user_id'] = user['id']
                session['name'] = user['name']
                session['email'] = user['email']
                session['role'] = user['role']
                session['branch_id'] = user['branch_id']
                session['branch_name'] = user['branch_name']

                cursor.execute('UPDATE users SET last_active = %s WHERE id = %s', (datetime.now(), user['id']))
                mysql.connection.commit()

                cursor.close()
                if role == 'employee':
                    return redirect(url_for('employee.dashboard'))
                else:
                    return redirect(url_for('intern.dashboard'))
            else:
                flash('Invalid credentials!', 'error')

        cursor.close()

    # Get branches for dropdown
    cursor = mysql.connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute('SELECT * FROM branches ORDER BY name')
    branches = cursor.fetchall()
    cursor.close()

    return render_template('login.html', branches=branches)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
