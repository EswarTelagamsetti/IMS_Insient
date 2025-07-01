from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import pymysql
pymysql.install_as_MySQLdb()  # Important for compatibility

from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

# Import routes
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.employee import employee_bp
from routes.intern import intern_bp

# Import utilities
from utils.email_service import send_password_email
from utils.helpers import calculate_experience, generate_password
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# MySQL Configuration
mysql = MySQL(app)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(employee_bp, url_prefix='/employee')
app.register_blueprint(intern_bp, url_prefix='/intern')

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session['role'] == 'employee':
            return redirect(url_for('employee.dashboard'))
        elif session['role'] == 'intern':
            return redirect(url_for('intern.dashboard'))
    return redirect(url_for('auth.login'))

@app.context_processor
def inject_user():
    return dict(session=session)

if __name__ == '__main__':
    app.run(debug=True)
