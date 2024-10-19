from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database connection function
def create_connection():
    conn = sqlite3.connect('student_recognition.db')
    return conn

# Function to create tables
def create_tables():
    conn = create_connection()
    c = conn.cursor()

    # Create students table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    department TEXT,
                    admission_year INTEGER,
                    gpa REAL,
                    core_course_grades REAL,
                    hackathons INTEGER,
                    papers INTEGER,
                    teacher_contributions INTEGER
                )''')

    # # Create rankings table
    # c.execute('''CREATE TABLE IF NOT EXISTS rankings (
    #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
    #                 student_id INTEGER,
    #                 ranking REAL,
    #                 FOREIGN KEY (student_id) REFERENCES students(id)
    #             )''')


    # Create rankings table
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                overall_percentage REAL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )''')

    
    conn.commit()
    conn.close()

# Function to add student data
def add_student(name, department, admission_year, gpa, core_course_grades, hackathons, papers, teacher_contributions):
    conn = create_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO students (name, department, admission_year, gpa, core_course_grades, hackathons, papers, teacher_contributions)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
              (name, department, admission_year, gpa, core_course_grades, hackathons, papers, teacher_contributions))
    conn.commit()
    conn.close()

# Function to calculate ranking
def calculate_ranking(student):
    weights = {
        'gpa': 0.4,
        'core_course_grades': 0.3,
        'hackathons': 0.1,
        'papers': 0.1,
        'teacher_contributions': 0.1
    }
    return (
        weights['gpa'] * student['gpa'] +
        weights['core_course_grades'] * student['core_course_grades'] +
        weights['hackathons'] * student['hackathons'] +
        weights['papers'] * student['papers'] +
        weights['teacher_contributions'] * student['teacher_contributions']
    )

# Function to update rankings
def update_rankings():
    conn = create_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM students')
    students = c.fetchall()
    for student in students:
        student_data = {
            'gpa': student[4],
            'core_course_grades': student[5],
            'hackathons': student[6],
            'papers': student[7],
            'teacher_contributions': student[8]
        }
        ranking = calculate_ranking(student_data)
        c.execute('INSERT OR REPLACE INTO rankings (student_id, ranking) VALUES (?, ?)', (student[0], ranking))
    conn.commit()
    conn.close()

# Home route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        department = request.form["department"]
        admission_year = request.form["admission_year"]
        gpa = request.form["gpa"]
        core_course_grades = request.form["core_course_grades"]
        hackathons = request.form["hackathons"]
        papers = request.form["papers"]
        teacher_contributions = request.form["teacher_contributions"]

        add_student(name, department, admission_year, gpa, core_course_grades, hackathons, papers, teacher_contributions)
        flash(f"Student {name} added successfully!")

    # Fetch top 3 students
    conn = create_connection()
    df = pd.read_sql_query('''SELECT students.name, rankings.ranking 
                               FROM students 
                               JOIN rankings ON students.id = rankings.student_id 
                               ORDER BY ranking DESC LIMIT 3''', conn)
    conn.close()

    return render_template("index.html", top_students=df)

# Route to update rankings
@app.route("/calculate_rankings")
def calculate_rankings():
    update_rankings()
    flash("Rankings updated Successfully!")
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Initialize the database and create tables if they don't exist
    create_tables()
    app.run(debug=True)
