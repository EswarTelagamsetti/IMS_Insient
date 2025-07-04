import pymysql
from datetime import datetime, timedelta

class Database:
    def __init__(self, app):
        self.app = app

    def get_connection(self):
        return pymysql.connect(
            host=self.app.config['DB_HOST'],
            user=self.app.config['DB_USER'],
            password=self.app.config['DB_PASSWORD'],
            database=self.app.config['DB_NAME'],
            cursorclass=pymysql.cursors.DictCursor
        )


class User:
    def __init__(self, db: Database):
        self.db = db

    def create_user(self, name, email, password, role, branch_id, work_type, experience_start_date):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, password, role, branch_id, work_type, experience_start_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, password, role, branch_id, work_type, experience_start_date))
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return user_id

    def get_user_by_email(self, email):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    def get_user_by_id(self, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.*, b.name as branch_name 
            FROM users u 
            LEFT JOIN branches b ON u.branch_id = b.id 
            WHERE u.id = %s
        """, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    def update_availability(self, user_id, is_available):
        now = datetime.now()
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # ✅ Ensure status is stored as 1 (True) or 0 (False)
        cursor.execute("""
            INSERT INTO activity_logs (user_id, status, timestamp)
            VALUES (%s, %s, %s)
        """, (user_id, int(is_available), now))

        # ✅ Update availability and last_active timestamp
        cursor.execute("""
            UPDATE users SET is_available = %s, last_active = %s WHERE id = %s
        """, (is_available, now, user_id))

        conn.commit()
        cursor.close()
        conn.close()

    def update_last_active(self, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_active = %s WHERE id = %s", (datetime.now(), user_id))
        conn.commit()
        cursor.close()
        conn.close()

    def get_inactive_users(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        inactive_time = datetime.now() - timedelta(hours=48)
        cursor.execute("""
            SELECT u.*, b.name as branch_name 
            FROM users u 
            LEFT JOIN branches b ON u.branch_id = b.id 
            WHERE u.last_active < %s AND u.role != 'admin'
        """, (inactive_time,))
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return users


class Branch:
    def __init__(self, db: Database):
        self.db = db

    def create_branch(self, name):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO branches (name) VALUES (%s)", (name,))
        conn.commit()
        branch_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return branch_id

    def get_all_branches(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM branches ORDER BY name")
        branches = cursor.fetchall()
        cursor.close()
        conn.close()
        return branches

    def delete_branch(self, branch_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM branches WHERE id = %s", (branch_id,))
        conn.commit()
        cursor.close()
        conn.close()


class Ticket:
    def __init__(self, db: Database):
        self.db = db

    def create_ticket(self, title, description, raised_by, assigned_to):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickets (title, description, raised_by, assigned_to)
            VALUES (%s, %s, %s, %s)
        """, (title, description, raised_by, assigned_to))
        conn.commit()
        ticket_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return ticket_id

    def get_user_tickets(self, user_id, status=None):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("""
                SELECT t.*, u1.name as raised_by_name, u2.name as assigned_to_name
                FROM tickets t
                JOIN users u1 ON t.raised_by = u1.id
                JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.assigned_to = %s AND t.status = %s
                ORDER BY t.created_at DESC
            """, (user_id, status))
        else:
            cursor.execute("""
                SELECT t.*, u1.name as raised_by_name, u2.name as assigned_to_name
                FROM tickets t
                JOIN users u1 ON t.raised_by = u1.id
                JOIN users u2 ON t.assigned_to = u2.id
                WHERE t.assigned_to = %s
                ORDER BY t.created_at DESC
            """, (user_id,))
        tickets = cursor.fetchall()
        cursor.close()
        conn.close()
        return tickets

    def complete_ticket(self, ticket_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tickets SET status = 'completed', completed_at = %s WHERE id = %s
        """, (datetime.now(), ticket_id))
        conn.commit()

        cursor.execute("""
            UPDATE users SET tickets_solved = tickets_solved + 1 
            WHERE id = (SELECT assigned_to FROM tickets WHERE id = %s)
        """, (ticket_id,))
        conn.commit()
        cursor.close()
        conn.close()
