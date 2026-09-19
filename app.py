
import os
import sqlite3
from flask import Flask, flash, redirect, render_template_string, request, session, url_for
import pandas as pd

app = Flask(__name__)
app.secret_key = "zaber_spinning_secret_key_2026"

DB_NAME = "company_app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users table modified with password and role (host/employee)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            emp_id TEXT PRIMARY KEY,
            name TEXT,
            designation TEXT,
            department TEXT,
            password TEXT,
            role TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS work_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            date TEXT,
            task_details TEXT,
            status TEXT
        )
    """)
    
    # Insert a Default Master Host (Admin) if not exists
    # Default ID: ADMIN-001, Password: admin123
    c.execute("SELECT * FROM users WHERE emp_id = 'ADMIN-001'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
            ("ADMIN-001", "System Admin", "Head of IT", "Management", "admin123", "host")
        )
        conn.commit()
        
    conn.close()

init_db()

# HTML Template (User Interface)
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Zaber Spinning Mills Ltd.</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 650px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin: auto; }
        h2 { color: #004085; text-align: center; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #6c757d; font-size: 14px; margin-bottom: 20px; }
        nav { text-align: center; margin-bottom: 20px; background: #e9ecef; padding: 10px; border-radius: 5px; }
        nav a { margin: 0 8px; text-decoration: none; color: #007bff; font-weight: bold; font-size: 14px; }
        form { display: flex; flex-direction: column; gap: 10px; }
        input, select, textarea { padding: 10px; font-size: 15px; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #28a745; color: white; border: none; padding: 10px; font-size: 16px; border-radius: 4px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }
        th { background-color: #004085; color: white; }
        .alert { background: #d4edda; color: #155724; padding: 10px; border-radius: 4px; margin-bottom: 10px; text-align: center; font-size: 14px; }
        .user-info { background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
    </style>
</head>
<body>
<div class="container">
    <h2>🏭 Zaber Spinning Mills Ltd.</h2>
    <div class="subtitle">Employee Work Update & Management System</div>

    {% if session.get('emp_id') %}
        <div class="user-info">
            <span>👤 <b>{{ session.get('name') }}</b> ({{ session.get('role').upper() }})</span>
            <a href="/logout" style="color: red; text-decoration: none; font-weight: bold;">Logout</a>
        </div>
        <nav>
            <a href="/">Home / Update</a>
            {% if session.get('role') == 'host' %}
                <a href="/register">Create User</a>
                <a href="/reports">All Reports</a>
            {% endif %}
        </nav>
    {% endif %}

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="alert">{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}

    {% if not session.get('emp_id') %}
        <!-- LOGIN PAGE -->
        <h3>🔐 Employee Login</h3>
        <form method="POST" action="/login">
            <input type="text" name="emp_id" placeholder="Employee ID (যেমন: ADMIN-001)" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" style="background: #007bff;">Login</button>
        </form>
        <p style="font-size: 12px; color: #666; text-align: center; margin-top: 15px;">
            ডিফল্ট হোস্ট আইডি: <b>ADMIN-001</b> | পাসওয়ার্ড: <b>admin123</b>
        </p>

    {% elif page == 'register' and session.get('role') == 'host' %}
        <!-- HOST USER CREATION PAGE -->
        <h3>➕ নতুন ইউজার অথবা হোস্ট তৈরি করুন</h3>
        <form method="POST">
            <input type="text" name="emp_id" placeholder="Employee ID (যেমন: EMP-002)" required>
            <input type="text" name="name" placeholder="Full Name" required>
            <input type="text" name="designation" placeholder="Designation (যেমন: IE Officer)" required>
            <input type="text" name="department" placeholder="Department (যেমন: IE / Spinning)" required>
            <input type="password" name="password" placeholder="Account Password" required>
            <select name="role">
                <option value="employee">Employee (সাধারণ কর্মী)</option>
                <option value="host">Host (হোস্ট / এডমিন)</option>
            </select>
            <button type="submit">Create Account</button>
        </form>

    {% elif page == 'update' %}
        <!-- WORK UPDATE PAGE -->
        <h3>📝 কাজের আপডেট সাবমিট করুন</h3>
        <form method="POST" action="/save_update">
            <input type="hidden" name="emp_id" value="{{ session.get('emp_id') }}">
            <input type="date" name="date" required>
            <textarea name="task_details" placeholder="আজকের কাজের বিবরণ বিস্তারিত লিখুন..." rows="4" required></textarea>
            <select name="status">
                <option value="Completed">Completed</option>
                <option value="In Progress">In Progress</option>
                <option value="Pending">Pending</option>
            </select>
            <button type="submit">Submit Update</button>
        </form>

    {% elif page == 'reports' and session.get('role') == 'host' %}
        <!-- REPORTS PAGE FOR HOSTS -->
        <h3>📊 সকল কর্মীর কাজের রিপোর্ট</h3>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Dept</th>
                <th>Date</th>
                <th>Task</th>
                <th>Status</th>
            </tr>
            {% for row in reports %}
            <tr>
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td>{{ row[3] }}</td>
                <td>{{ row[4] }}</td>
                <td>{{ row[5] }}</td>
                <td>{{ row[6] }}</td>
            </tr>
            {% endfor %}
        </table>
    {% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    if not session.get("emp_id"):
        return render_template_string(HTML_TEMPLATE)
    return render_template_string(HTML_TEMPLATE, page="update")

@app.route("/login", methods=["POST"])
def login():
    emp_id = request.form["emp_id"]
    password = request.form["password"]
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE emp_id = ? AND password = ?", (emp_id, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session["emp_id"] = user[0]
        session["name"] = user[1]
        session["department"] = user[3]
        session["role"] = user[5]
        flash("সফলভাবে লগইন হয়েছে!")
        return redirect(url_for("index"))
    else:
        flash("ভুল Employee ID অথবা Password!")
        return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    flash("লগআউট সফল হয়েছে।")
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("role") != "host":
        return redirect(url_for("index"))
        
    if request.method == "POST":
        emp_id = request.form["emp_id"]
        name = request.form["name"]
        designation = request.form["designation"]
        department = request.form["department"]
        password = request.form["password"]
        role = request.form["role"]
        
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                (emp_id, name, designation, department, password, role),
            )
            conn.commit()
            conn.close()
            flash("নতুন ইউজার সফলভাবে তৈরি করা হয়েছে!")
        except:
            flash("এই ID টি ইতিমধ্যে রেজিস্টার্ড করা আছে!")
        return redirect(url_for("register"))
        
    return render_template_string(HTML_TEMPLATE, page="register")

@app.route("/save_update", methods=["POST"])
def save_update():
    if not session.get("emp_id"):
        return redirect(url_for("index"))
        
    emp_id = request.form["emp_id"]
    date = request.form["date"]
    task_details = request.form["task_details"]
    status = request.form["status"]

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO work_updates (emp_id, date, task_details, status) VALUES (?, ?, ?, ?)",
        (emp_id, date, task_details, status),
    )
    conn.commit()
    conn.close()
    flash("কাজের আপডেট সফলভাবে জমা হয়েছে!")
    return redirect(url_for("index"))

@app.route("/reports")
def reports():
    if session.get("role") != "host":
        return redirect(url_for("index"))
        
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT u.emp_id, u.name, u.designation, u.department, 
               w.date, w.task_details, w.status 
        FROM work_updates w
        JOIN users u ON w.emp_id = u.emp_id
    """
    c = conn.cursor()
    c.execute(query)
    reports = c.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page="reports", reports=reports)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)