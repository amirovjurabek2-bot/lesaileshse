import pandas as pd
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "lesailes_hse_2026"


def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        position TEXT,
        phone TEXT,
        medical_date TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == '12345':

            session['user'] = username

            return redirect('/')

    return render_template('login.html')


@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


@app.route('/')
def home():

    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()

    employees = []

    today = datetime.today()

    for row in rows:

        status = "normal"

        try:
            med_date = datetime.strptime(row[4], "%Y-%m-%d")

            days_left = (med_date - today).days

            if days_left < 0:
                status = "danger"

            elif days_left <= 30:
                status = "warning"

        except:
            pass

        employees.append({
            "id": row[0],
            "fullname": row[1],
            "position": row[2],
            "phone": row[3],
            "medical_date": row[4],
            "status": status
        })

    conn.close()

    return render_template(
        'index.html',
        employees=employees
    )


@app.route('/add', methods=['POST'])
def add_employee():

    if 'user' not in session:
        return redirect('/login')

    fullname = request.form['fullname']
    position = request.form['position']
    phone = request.form['phone']
    medical_date = request.form['medical_date']

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO employees
    (fullname, position, phone, medical_date)
    VALUES (?, ?, ?, ?)
    """, (
        fullname,
        position,
        phone,
        medical_date
    ))

    conn.commit()
    conn.close()

    return redirect('/')


@app.route('/test')
def test():

    if 'user' not in session:
        return redirect('/login')

    return render_template('test.html')


@app.route('/import')
def import_excel():

    file = 'employees.xlsx'

    df = pd.read_excel(file)

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    for _, row in df.iterrows():

        cur.execute("""
        INSERT INTO employees
        (fullname, position, phone, medical_date)
        VALUES (?, ?, ?, ?)
        """, (
            str(row['fullname']),
            str(row['position']),
            str(row['phone']),
            str(row['medical_date'])
        ))

    conn.commit()
    conn.close()

    return "Excel маълумотлари юкланди!"


if __name__ == '__main__':
    app.run(debug=True)