from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
import pymysql
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Register Blueprints
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.employee import employee_bp
from routes.intern import intern_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(employee_bp, url_prefix='/employee')
app.register_blueprint(intern_bp, url_prefix='/intern')

# ---------- Database Setup using PyMySQL ----------
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.before_request
def before_request():
    g.db = get_db_connection()
    g.cursor = g.db.cursor()

@app.teardown_request
def teardown_request(exception):
    db = g.pop('db', None)
    cursor = g.pop('cursor', None)
    if cursor:
        cursor.close()
    if db:
        db.close()

# ---------- Routes ----------
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

# ---------- Run App ----------
if __name__ == '__main__':
    app.run(debug=True)
