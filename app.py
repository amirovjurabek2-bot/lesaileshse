import sqlite3
import pandas as pd
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, send_from_directory
import os

app = Flask(__name__)
app.secret_key = "lesailes-hse-2026-secret"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx", "doc", "docx", "xlsx"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        position TEXT,
        phone TEXT,
        medical_date TEXT
    )""")

    conn.commit()
    conn.close()
@app.route("/upload", methods=["GET", "POST"])
def upload_file():

    if request.method == "POST":

        file = request.files.get("file")

        if not file or file.filename == "":
            return "Файл танланмади"

        if file and allowed_file(file.filename):

            filename = secure_filename(file.filename)

            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            conn = sqlite3.connect("database.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO files(filename) VALUES(?)", (filename,))
            conn.commit()
            conn.close()

            return redirect("/upload")

        return "Файл формати нотўғри"

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT id, filename FROM files")
    files = cur.fetchall()

    conn.close()

    return render_template("upload.html", files=files)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename, as_attachment=True)

import random

from questions.fire import questions as fire_q
from questions.electric import questions as electric_q
from questions.sanitary import questions as sanitary_q
from questions.firstaid import questions as firstaid_q
# =========================
# DATABASE INIT
# =========================
import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # FILES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL
    )
    """)

    # EMPLOYEES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        position TEXT,
        phone TEXT,
        medical_date TEXT
    )
    """)

    # RESULTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        position TEXT,
        branch TEXT,
        test_name TEXT,
        score INTEGER,
        exam_date TEXT
    )
    """)

    # TESTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option1 TEXT,
        option2 TEXT,
        option3 TEXT,
        option4 TEXT,
        correct INTEGER,
        category TEXT
    )
    """)

    # EQUIPMENT
    cur.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        inventory TEXT,
        branch TEXT
    )
    """)

    conn.commit()
    conn.close()

def create_admin():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE username=?", ("admin",))
    if cur.fetchone() is None:
        cur.execute("""
        INSERT INTO users(username, password, role)
        VALUES (?, ?, ?)
        """, ("admin", "admin", "admin"))

    conn.commit()
    conn.close()

# =========================
# TEST SEED
# =========================
def add_test(q, o1, o2, o3, o4, correct, category):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tests
        (question, option1, option2, option3, option4, correct, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (q, o1, o2, o3, o4, correct, category))

    conn.commit()
    conn.close()


def seed_tests():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tests")
    count = cur.fetchone()[0]

    if count == 0:
        tests = [
            ("Ёнғинда нима қилиш керак?", "Қочиш", "Сув сепиш", "Электрни ўчириш", "Куллаш", 1, "fire"),
            ("Каска нима учун керак?", "Безак", "Бошни ҳимоя қилиш", "Совуқдан сақлаш", "Реклама", 2, "fire"),
            ("Электр билан ишлаганда нима керак?", "Сув", "Резина қўлқоп", "Югуриш", "Емаслик", 2, "electric"),
            ("Гигиена нима?", "Тозалик", "Уйқу", "Овқат", "Иш", 1, "sanitary"),
            ("Биринчи ёрдам нима?", "Дори", "Тез ёрдам", "Қочиш", "Ўйнаш", 2, "firstaid"),
        ]

        for t in tests:
            add_test(*t)


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT role FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["role"] = user[0]
            return redirect("/")

        return "Login xato"

    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Жами ишчилар
    cur.execute("SELECT COUNT(*) FROM employees")
    employee_count = cur.fetchone()[0]

    # Жами тестлар
    cur.execute("SELECT COUNT(*) FROM results")
    result_count = cur.fetchone()[0]

    # Тиббий кўриклар
    cur.execute("SELECT medical_date FROM employees")
    rows = cur.fetchall()

    today = datetime.today()

    warning = 0
    expired = 0

    for row in rows:

        try:
            med_date = datetime.strptime(row[0], "%Y-%m-%d")

            days = (med_date - today).days

            if days < 0:
                expired += 1

            elif days <= 30:
                warning += 1

        except:
            pass

    conn.close()

    return render_template(
    "dashboard.html",
    employee_count=employee_count,
    result_count=result_count,
    warning=warning,
    expired=expired,
    username=session["user"],
    role=session["role"]
)
# =========================
# EMPLOYEES
# =========================
@app.route("/employees")
def employees():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM employees")
    employees = cur.fetchall()

    conn.close()

    return render_template("employees.html", employees=employees)

@app.route("/users")
def users():

    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    SELECT id, username, role
    FROM users
    ORDER BY username
""")

    users = cur.fetchall()

    conn.close()

    return render_template(
        "users.html",
        users=users,
        branches=BRANCHES
    )
@app.route("/users/add", methods=["POST"])
def add_user():

    if session.get("role") != "admin":
        return redirect("/")

    username = request.form["username"].strip()
    password = request.form["password"].strip()
    role = request.form["role"]
    branch = request.form["branch"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Логин такрорланмаслиги учун
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    if cur.fetchone():
        conn.close()
        return "Бу логин аллақачон мавжуд!"

    cur.execute("""
        INSERT INTO users(username, password, role)
        VALUES (?, ?, ?)
    """, (username, password, role))

    conn.commit()
    conn.close()

    return redirect("/users")

@app.route("/users/delete/<int:id>")
def delete_user(id):

    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # admin логинини ўчиришга рухсат бермаймиз
    cur.execute("SELECT username FROM users WHERE id=?", (id,))
    user = cur.fetchone()

    if user and user[0] == "admin":
        conn.close()
        return "Admin логинини ўчириб бўлмайди."

    cur.execute("DELETE FROM users WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/users")

@app.route("/upload_excel", methods=["POST"])
def upload_excel():
    file = request.files["file"]

    df = pd.read_excel(file)

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO employees (fullname, position, phone, medical_date)
            VALUES (?, ?, ?, ?)
        """, (
            row["fullname"],
            row["position"],
            row["phone"],
            row["medical_date"]
        ))

    conn.commit()
    conn.close()

    return redirect("/employees")
@app.route("/delete/<int:id>")
def delete_employee(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM employees WHERE id = ?", (id,))
    conn.commit()

    conn.close()

    return redirect("/employees")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        fullname = request.form["fullname"]
        position = request.form["position"]
        phone = request.form["phone"]
        medical_date = request.form["medical_date"]

        cur.execute("""
            UPDATE employees
            SET fullname=?, position=?, phone=?, medical_date=?
            WHERE id=?
        """, (fullname, position, phone, medical_date, id))

        conn.commit()
        conn.close()
        return redirect("/employees")

    cur.execute("SELECT * FROM employees WHERE id=?", (id,))
    employee = cur.fetchone()

    conn.close()
    return render_template("edit.html", employee=employee)

@app.route("/add", methods=["POST"])
def add_employee():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO employees(fullname, position, phone, medical_date)
        VALUES (?,?,?,?)
    """, (
        request.form["fullname"],
        request.form["position"],
        request.form["phone"],
        request.form["medical_date"]
    ))

    conn.commit()
    conn.close()

    return redirect("/employees")
# =========================
# TEST RENDER FUNCTION
# =========================
def render_tests(category):

    flow = session.get("exam_flow", [])
    index = session.get("current_stage", 0)

    # текущий category
    if flow:
        category = flow[index]

    if category == "fire":
        tests = fire_q
    elif category == "electric":
        tests = electric_q
    elif category == "sanitary":
        tests = sanitary_q
    elif category == "firstaid":
        tests = firstaid_q
    else:
        return "Category topilmadi"

    # ⏱ 10 ta savol
    if request.method == "GET":
        if len(tests) > 10:
            tests = random.sample(tests, 10)
        session["tests"] = tests

    tests = session.get("tests", tests)

    # ⏱ TIMER CHECK
    start_time = session.get("start_time")
    if start_time:
        elapsed = datetime.now().timestamp() - start_time
        if elapsed > session.get("time_limit", 600):
            return redirect("/results")

    # POST
    if request.method == "POST":

        score = 0

        for i, q in enumerate(tests):
            answer = request.form.get(f"q{i}")

            if answer and int(answer) == q["correct"]:
                score += 1

        percent = int(score * 100 / len(tests))

        session["total_score"] += percent

        # NEXT STAGE
        index = session.get("current_stage", 0) + 1
        session["current_stage"] = index

        # LAST STAGE?
        if index >= len(session["exam_flow"]):
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO results
            (fullname, position, branch, test_name, score, exam_date)
            VALUES (?,?,?,?,?,?)
            """, (
                session["fullname"],
                session["position"],
                session["branch"],
                "FULL EXAM",
                session["total_score"],
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))

            conn.commit()
            conn.close()

            return redirect("/results")

        # NEXT CATEGORY REDIRECT
        next_cat = session["exam_flow"][index]

        if next_cat == "electric":
            return redirect("/electric_test")
        elif next_cat == "sanitary":
            return redirect("/sanitary_test")
        elif next_cat == "firstaid":
            return redirect("/firstaid_test")

    return render_template("test_page.html", tests=tests)
# =========================
# TEST ROUTES
# =========================
@app.route("/fire_test", methods=["GET", "POST"])
def fire_test():
    return render_tests("fire")


@app.route("/electric_test", methods=["GET", "POST"])
def electric_test():
    return render_tests("electric")


@app.route("/sanitary_test", methods=["GET", "POST"])
def sanitary_test():
    return render_tests("sanitary")


@app.route("/firstaid_test", methods=["GET", "POST"])
def firstaid_test():
    return render_tests("firstaid")


# =========================
# RESULTS
# =========================
@app.route("/results")
def results():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM results ORDER BY id DESC")
    results = cur.fetchall()

    conn.close()

    return render_template("results.html", results=results)


# =========================
# START APP
# =========================
from flask import request, session, render_template, redirect
from datetime import datetime

@app.route("/start_test", methods=["GET", "POST"])
def start_test():

    # login check
    if "user" not in session:
        return redirect("/login")

    # FORM юборилганда
    if request.method == "POST":

        session["exam_flow"] = ["fire", "electric", "sanitary", "firstaid"]
        session["current_stage"] = 0
        session["total_score"] = 0

        session["start_time"] = datetime.now().timestamp()
        session["time_limit"] = 10 * 60

        session["fullname"] = request.form["fullname"]
        session["position"] = request.form["position"]
        session["branch"] = request.form["branch"]

        category = request.form["category"]

        if category == "fire":
            return redirect("/fire_test")
        elif category == "electric":
            return redirect("/electric_test")
        elif category == "sanitary":
            return redirect("/sanitary_test")
        elif category == "firstaid":
            return redirect("/firstaid_test")

    # GET бўлганда
    return render_template(
        "start_test.html",
        branches=BRANCHES
    )
@app.route("/instructions")
def instructions():
    files = os.listdir("uploads")
    return render_template("instructions.html", files=files, role=session.get("role"))
@app.route("/medical")
def medical():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT fullname, position, medical_date
        FROM employees
        ORDER BY medical_date
    """)

    employees = cur.fetchall()

    conn.close()

    return render_template("medical.html", employees=employees)
@app.route("/equipment")
def equipment():

    branch = request.args.get("branch", "")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if branch == "":
        cur.execute("SELECT * FROM equipment")
    else:
        cur.execute(
            "SELECT * FROM equipment WHERE branch=?",
            (branch,)
        )

    data = cur.fetchall()

    conn.close()

    return render_template(
        "equipment.html",
        items=data,
        branches=BRANCHES,
        selected_branch=branch
    )
@app.route("/equipment/add", methods=["POST"])
def add_equipment():

    name = request.form["name"]
    inventory = request.form["inventory"]
    branch = request.form["branch"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO equipment (name, inventory, branch)
        VALUES (?, ?, ?)
    """, (name, inventory, branch))

    conn.commit()
    conn.close()

    return redirect("/equipment")
@app.route("/equipment/delete/<int:id>")
def delete_equipment(id):

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM equipment WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/equipment")
def import_equipment_from_excel(file_path):

    df = pd.read_excel(file_path)

    df.columns = df.columns.str.strip()
    df = df.fillna("")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM equipment")

    for _, row in df.iterrows():

        branch = BRANCH_MAP.get(
            str(row["Филиаллар"]).strip(),
            str(row["Филиаллар"]).strip()
        )

        cur.execute("""
            INSERT INTO equipment (name, inventory, branch)
            VALUES (?, ?, ?)
        """, (
            row["Оборудование"],
            row["Инвентар №"],
            branch
        ))

    conn.commit()
    conn.close()
BRANCH_MAP = {
    "Лес Азия": "AZIYA",
    "Лес Кукча": "KO'KCHA",
    "Лес Парус": "PARUS",
    "Лес Сергели": "SERGELI",
    "Лес МГ": "M.GORKIY",
    "Лес Алпомиш": "ALPOMISH",
    "Лес Чилонзор": "CHILONZOR",
    "Лес Фархадский": "FARXADSKIY",
    "Лес Ривиера": "RIVEIRA",
    "Лес Хамза": "HAMZA",
    "Лес Юнусобод": "YUNUSOBOD",
    "Лес Ойбек": "OYBEK",
    "Лес 40лет": "40 LET",
    "Лес Ц5": "C-5",
    "Лес Зенит": "ZENIT",
    "Лес Мега": "MEGAPLANET",
    "Лес Собир": "S.RAXIMOV",
    "Лес Некст": "NEXT",
    "Лес Чимган": "CHIMGAN",
    "Лес Сампи": "SAMPI",
    "Лес Ц1": "C-1",
    "Лес Бочка": "BOCHKA",
    "Лес Куйлюк": "QO'YLIQ"
}
BRANCHES = [
    "AZIYA",
    "KO'KCHA",
    "PARUS",
    "SERGELI",
    "M.GORKIY",
    "ALPOMISH",
    "CHILONZOR",
    "FARXADSKIY",
    "RIVEIRA",
    "HAMZA",
    "YUNUSOBOD",
    "OYBEK",
    "40 LET",
    "C-5",
    "ZENIT",
    "MEGAPLANET",
    "S.RAXIMOV",
    "NEXT",
    "CHIMGAN",
    "SAMPI",
    "C-1",
    "BOCHKA",
    "QO'YLIQ"
]

if __name__ == "__main__":
    init_db()
    create_admin()
    seed_tests()

    if os.path.exists("equipment.xlsx"):
        import_equipment_from_excel("equipment.xlsx")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
