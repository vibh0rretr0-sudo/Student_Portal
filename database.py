import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "portal.db")


def get_db():
    from flask import g
    if 'db' not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        DROP TABLE IF EXISTS course_materials;
        DROP TABLE IF EXISTS announcements;
        DROP TABLE IF EXISTS enrollments;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS professors;
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'professor')),
            full_name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            student_id TEXT UNIQUE NOT NULL,
            enrollment_date DATE DEFAULT (date('now')),
            major TEXT,
            current_semester INTEGER DEFAULT 1
        );

        CREATE TABLE professors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            employee_id TEXT UNIQUE NOT NULL,
            department TEXT,
            title TEXT
        );

        CREATE TABLE courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            credits INTEGER DEFAULT 3,
            professor_id INTEGER REFERENCES professors(id) ON DELETE SET NULL,
            semester TEXT DEFAULT 'Fall 2026',
            schedule TEXT,
            room TEXT
        );

        CREATE TABLE enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            semester TEXT DEFAULT 'Fall 2026',
            grade TEXT DEFAULT 'IP',
            attendance REAL DEFAULT 0,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, course_id)
        );

        CREATE TABLE announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            professor_id INTEGER NOT NULL REFERENCES professors(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE course_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            file_url TEXT,
            type TEXT DEFAULT 'pdf',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    _seed_data(conn)
    conn.commit()
    # conn.close() removed as handled by teardown_appcontext



def _hash_password(password):
    import hashlib
    import os
    salt = os.urandom(32)
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + pw_hash.hex()

def _verify_password(password, password_hash):
    import hashlib
    salt_hex, hash_hex = password_hash.split(':')
    salt = bytes.fromhex(salt_hex)
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return pw_hash.hex() == hash_hex


def _seed_data(conn):
    c = conn.cursor()

    # Professors
    c.execute("INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, 'professor', ?, ?)",
        ("srahman", _hash_password("prof123"), "Dr. Shereen Rahman", "srahman@university.edu"))
    c.execute("INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, 'professor', ?, ?)",
        ("jmitchell", _hash_password("prof123"), "Prof. James Mitchell", "jmitchell@university.edu"))
    c.execute("INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, 'professor', ?, ?)",
        ("akumar", _hash_password("prof123"), "Dr. Anita Kumar", "akumar@university.edu"))
    c.execute("SELECT id, username FROM users WHERE role='professor'")
    prof_user_map = {row['username']: row['id'] for row in c.fetchall()}

    prof_data = [
        ("srahman", "P001", "Computer Science", "Associate Professor"),
        ("jmitchell", "P002", "Mathematics", "Professor"),
        ("akumar", "P003", "Electrical Engineering", "Assistant Professor"),
    ]
    for uname, eid, dept, title in prof_data:
        c.execute(
            "INSERT INTO professors (user_id, employee_id, department, title) VALUES (?, ?, ?, ?)",
            (prof_user_map[uname], eid, dept, title)
        )

    # Students
    students = [
        ("av Singh", "as123", "ayesha.singh@university.edu", "S001", "Computer Science", 4),
        ("rahul Mehta", "rm456", "rahul.mehta@university.edu", "S002", "Mathematics", 3),
        ("nina Patel", "np789", "nina.patel@university.edu", "S003", "Electrical Engineering", 2),
        ("carlos Rivera", "cr012", "carlos.rivera@university.edu", "S004", "Computer Science", 1),
        ("mei Tan", "mt345", "mei.tan@university.edu", "S005", "Computer Science", 4),
        ("omar Hassan", "oh678", "omar.hassan@university.edu", "S006", "Mathematics", 2),
        ("lily Chen", "lc901", "lily.chen@university.edu", "S007", "Electrical Engineering", 3),
        ("james O'Brien", "jo234", "james.obrien@university.edu", "S008", "Computer Science", 1),
    ]
    student_data = [
        ("Aav Singh", "as123", "ayesha.singh@university.edu", "S001", "Computer Science", 4),
        ("rahul Mehta", "rm456", "rahul.mehta@university.edu", "S002", "Mathematics", 3),
        ("nina Patel", "np789", "nina.patel@university.edu", "S003", "Electrical Engineering", 2),
        ("carlos Rivera", "cr012", "carlos.rivera@university.edu", "S004", "Computer Science", 1),
        ("mei Tan", "mt345", "mei.tan@university.edu", "S005", "Computer Science", 4),
        ("omar Hassan", "oh678", "omar.hassan@university.edu", "S006", "Mathematics", 2),
        ("lily Chen", "lc901", "lily.chen@university.edu", "S007", "Electrical Engineering", 3),
        ("james O'Brien", "jo234", "james.obrien@university.edu", "S008", "Computer Science", 1),
    ]
    for name, uname, email, sid, major, sem in student_data:
        c.execute(
            "INSERT INTO users (username, password_hash, role, full_name, email) VALUES (?, ?, 'student', ?, ?)",
            (uname, _hash_password(uname), name, email)
        )

    c.execute("SELECT id, username FROM users WHERE role='student'")
    student_user_map = {row['username']: row['id'] for row in c.fetchall()}

    student_data2 = [
        ("av Singh", "as123", "S001", "Computer Science", 4),
        ("rahul Mehta", "rm456", "S002", "Mathematics", 3),
        ("nina Patel", "np789", "S003", "Electrical Engineering", 2),
        ("carlos Rivera", "cr012", "S004", "Computer Science", 1),
        ("mei Tan", "mt345", "S005", "Computer Science", 4),
        ("omar Hassan", "oh678", "S006", "Mathematics", 2),
        ("lily Chen", "lc901", "S007", "Electrical Engineering", 3),
        ("james O'Brien", "jo234", "S008", "Computer Science", 1),
    ]
    for name, uname, sid, major, sem in student_data2:
        c.execute(
            "INSERT INTO students (user_id, student_id, major, current_semester) VALUES (?, ?, ?, ?)",
            (student_user_map[uname], sid, major, sem)
        )

    # Courses
    c.execute("SELECT id FROM professors WHERE employee_id='P001'")
    p1 = c.fetchone()['id']
    c.execute("SELECT id FROM professors WHERE employee_id='P002'")
    p2 = c.fetchone()['id']
    c.execute("SELECT id FROM professors WHERE employee_id='P003'")
    p3 = c.fetchone()['id']

    courses = [
        ("CS301", "Data Structures & Algorithms", "Advanced data structures, algorithm design paradigms, complexity analysis, graphs, trees, hashing, sorting, and dynamic programming.", 4, p1, "Fall 2026", "MWF 10:00-11:30", "Engineering Block A, Room 204"),
        ("CS201", "Object-Oriented Programming", "Introduction to OOP concepts using Python: classes, inheritance, polymorphism, encapsulation, design patterns, and software architecture basics.", 3, p1, "Fall 2026", "MWF 14:00-15:20", "Engineering Block A, Room 112"),
        ("MA250", "Linear Algebra", "Vector spaces, linear transformations, matrices, determinants, eigenvalues and eigenvectors, orthogonality, and applications to engineering problems.", 3, p2, "Fall 2026", "TTh 09:00-10:30", "Science Building, Room 305"),
        ("EE310", "Digital Signal Processing", "Discrete-time signals and systems, Fourier analysis, filter design, z-transform, FFT, and applications in audio and image processing.", 4, p3, "Fall 2026", "TTh 13:00-14:50", "Engineering Block B, Room 210"),
        ("CS101", "Introduction to Programming", "Fundamentals of programming: variables, control flow, functions, arrays, file I/O, and problem-solving with Python.", 3, p1, "Fall 2026", "MWF 08:00-09:20", "Engineering Block A, Room 101"),
        ("CS350", "Machine Learning Fundamentals", "Supervised and unsupervised learning, regression, classification, clustering, neural networks basics, model evaluation, and ethical AI considerations.", 4, p1, "Fall 2026", "TTh 10:00-11:50", "Engineering Block A, Room 208"),
        ("MA300", "Probability & Statistics", "Probability theory, random variables, distributions, expectation, limit theorems, hypothesis testing, confidence intervals, and regression analysis.", 3, p2, "Fall 2026", "MWF 13:00-14:20", "Science Building, Room 310"),
        ("EE220", "Circuits & Electronics", "DC and AC circuit analysis, Kirchhoff's laws, Thevenin/Norton equivalents, op-amps, diodes, BJTs, FETs, and introductory digital logic.", 4, p3, "Fall 2026", "MWF 10:00-11:30", "Engineering Block B, Room 115"),
        ("CS410", "Capstone Project I", "Team-based software engineering project: requirements gathering, system design, agile methodology, version control, testing, and project management.", 3, p1, "Fall 2026", "F 14:00-16:50", "Engineering Block A, Room 310"),
        ("MA150", "Calculus II", "Techniques of integration, infinite series, Taylor expansions, parametric equations, polar coordinates, and introduction to multivariable calculus.", 4, p2, "Fall 2026", "TTh 14:00-15:50", "Science Building, Room 205"),
    ]
    for code, name, desc, credits, prof_id, sem, schedule, room in courses:
        c.execute(
            "INSERT INTO courses (code, name, description, credits, professor_id, semester, schedule, room) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (code, name, desc, credits, prof_id, sem, schedule, room)
        )

    c.execute("SELECT id, code FROM courses")
    course_map = {row['code']: row['id'] for row in c.fetchall()}

    # Enrollments
    enrollments = [
        ("S001", "CS301"), ("S001", "CS201"), ("S001", "MA250"),
        ("S002", "MA250"), ("S002", "CS101"),
        ("S003", "EE310"), ("S003", "CS201"), ("S003", "MA250"),
        ("S004", "CS101"), ("S004", "CS201"),
        ("S005", "CS301"), ("S005", "EE310"),
        ("S006", "MA250"), ("S006", "CS101"),
        ("S007", "EE310"), ("S007", "MA250"),
        ("S008", "CS101"),
        ("S001", "CS350"),
        ("S003", "CS350"),
        ("S005", "CS410"),
        ("S007", "MA150"),
        ("S004", "EE220"),
        ("S008", "MA150"),
    ]
    for sid, code in enrollments:
        c.execute(
            "INSERT INTO enrollments (student_id, course_id) VALUES ((SELECT id FROM students WHERE student_id=?), ?)",
            (sid, course_map[code])
        )

    # Set some grades for demo
    c.execute("UPDATE enrollments SET grade='A', attendance=95 WHERE student_id=(SELECT id FROM students WHERE student_id='S001') AND course_id=(SELECT id FROM courses WHERE code='CS201')")
    c.execute("UPDATE enrollments SET grade='B+', attendance=88 WHERE student_id=(SELECT id FROM students WHERE student_id='S005') AND course_id=(SELECT id FROM courses WHERE code='CS301')")
    c.execute("UPDATE enrollments SET grade='A-', attendance=92 WHERE student_id=(SELECT id FROM students WHERE student_id='S003') AND course_id=(SELECT id FROM courses WHERE code='EE310')")
    c.execute("UPDATE enrollments SET grade='B', attendance=85 WHERE student_id=(SELECT id FROM students WHERE student_id='S001') AND course_id=(SELECT id FROM courses WHERE code='MA250')")
    c.execute("UPDATE enrollments SET grade='A-', attendance=90 WHERE student_id=(SELECT id FROM students WHERE student_id='S003') AND course_id=(SELECT id FROM courses WHERE code='CS201')")
    c.execute("UPDATE enrollments SET grade='C+', attendance=72 WHERE student_id=(SELECT id FROM students WHERE student_id='S004') AND course_id=(SELECT id FROM courses WHERE code='CS101')")
    c.execute("UPDATE enrollments SET grade='A', attendance=97 WHERE student_id=(SELECT id FROM students WHERE student_id='S007') AND course_id=(SELECT id FROM courses WHERE code='MA250')")
    c.execute("UPDATE enrollments SET grade='B+', attendance=82 WHERE student_id=(SELECT id FROM students WHERE student_id='S002') AND course_id=(SELECT id FROM courses WHERE code='MA250')")

    # Announcements
    c.execute("INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_map['CS301'], p1, "Midterm Exam Details", "The midterm exam will be held on October 20th during regular class hours. It will cover chapters 1-5. Please bring your student ID and a non-programmable calculator."))
    c.execute("INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_map['CS301'], p1, "Assignment 3 Released", "Assignment 3 on graph algorithms is now available on the course portal. The deadline is November 3rd at 11:59 PM. Start early — it's a longer assignment."))
    c.execute("INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_map['MA250'], p2, "Office Hours Change", "My office hours this week will be on Thursday instead of Tuesday, 2:00-4:00 PM in Science Building Room 310. Apologies for any inconvenience."))
    c.execute("INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_map['EE310'], p3, "Lab Equipment Update", "The signal generators in Lab 3 have been recalibrated. Please use the new calibration files posted on the portal before your next lab session."))
    c.execute("INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_map['CS350'], p1, "Dataset Available", "The training dataset for your first ML project has been uploaded. It contains 10,000 labeled samples across 5 classes. See the README for preprocessing instructions."))
    c.execute("INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_map['MA150'], p2, "Problem Set 5 Due", "Problem Set 5 on infinite series is due this Friday. Make sure to show all your work — partial credit is awarded for correct setup even if the final answer is wrong."))
    c.execute("INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_map['EE220'], p3, "Midterm Review Session", "A review session for the circuits midterm will be held on Wednesday from 4-6 PM in the main auditorium. Bring your calculator and any questions you have."))

    # Course materials
    c.execute("INSERT INTO course_materials (course_id, title, type, file_url) VALUES (?, ?, ?, ?)",
        (course_map['CS301'], "Lecture 10: Graph Traversal", "pdf", "/materials/cs301_lec10.pdf"))
    c.execute("INSERT INTO course_materials (course_id, title, type, file_url) VALUES (?, ?, ?, ?)",
        (course_map['CS301'], "Assignment 3 Starter Code", "zip", "/materials/cs301_a3.zip"))
    c.execute("INSERT INTO course_materials (course_id, title, type) VALUES (?, ?, ?)",
        (course_map['MA250'], "Determinant Cheat Sheet", "pdf"))
    c.execute("INSERT INTO course_materials (course_id, title, type) VALUES (?, ?, ?)",
        (course_map['EE310'], "Z-Transform Tables", "pdf"))
    c.execute("INSERT INTO course_materials (course_id, title, type) VALUES (?, ?, ?)",
        (course_map['CS350'], "ML Dataset v1.2", "zip"))
    c.execute("INSERT INTO course_materials (course_id, title, type) VALUES (?, ?, ?)",
        (course_map['MA150'], "Integration Techniques Summary", "pdf"))
    c.execute("INSERT INTO course_materials (course_id, title, type) VALUES (?, ?, ?)",
        (course_map['EE220'], "Lab 2: Op-Amp Circuits", "pdf"))


def get_user_by_username(username):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_student_by_user_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT s.*, u.full_name, u.email FROM students s JOIN users u ON s.user_id = u.id WHERE s.user_id = ?",
        (user_id,)
    ).fetchone()
    return dict(row) if row else None


def get_professor_by_user_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT p.*, u.full_name, u.email FROM professors p JOIN users u ON p.user_id = u.id WHERE p.user_id = ?",
        (user_id,)
    ).fetchone()
    return dict(row) if row else None


def get_student_enrollments(student_user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT
            c.id AS course_id, c.code, c.name, c.description, c.credits,
            c.schedule, c.room, c.semester,
            u_prof.full_name AS professor_name, p.employee_id AS professor_id,
            e.grade, e.attendance, e.enrolled_at,
            (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id) AS enrollment_count
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN professors p ON c.professor_id = p.id
        LEFT JOIN users u_prof ON p.user_id = u_prof.id
        JOIN students s ON e.student_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE u.id = ?
        ORDER BY c.code
    """, (student_user_id,)).fetchall()
    return [dict(r) for r in rows]


def get_course_by_id(course_id):
    conn = get_db()
    row = conn.execute("""
        SELECT c.*, u.full_name AS professor_name, u.email AS professor_email, p.employee_id AS professor_id
        FROM courses c
        LEFT JOIN professors p ON c.professor_id = p.id
        LEFT JOIN users u ON p.user_id = u.id
        WHERE c.id = ?
    """, (course_id,)).fetchone()
    return dict(row) if row else None


def get_course_announcements(course_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT a.*, u.full_name AS professor_name
        FROM announcements a
        JOIN professors p ON a.professor_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE a.course_id = ?
        ORDER BY a.created_at DESC
    """, (course_id,)).fetchall()
    return [dict(r) for r in rows]


def _get_professor_name_by_id(professor_id):
    conn = get_db()
    row = conn.execute("""
        SELECT u.full_name FROM professors p JOIN users u ON p.user_id = u.id WHERE p.id = ?
    """, (professor_id,)).fetchone()
    return row['full_name'] if row else None


def get_course_materials(course_id):
    conn = get_db()
    rows = conn.execute("SELECT * FROM course_materials WHERE course_id = ? ORDER BY uploaded_at DESC", (course_id,)).fetchall()
    return [dict(r) for r in rows]


def get_professor_courses(professor_user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*, COUNT(e.id) AS enrollment_count
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        JOIN professors p ON c.professor_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE u.id = ?
        GROUP BY c.id
        ORDER BY c.code
    """, (professor_user_id,)).fetchall()
    return [dict(r) for r in rows]


def get_course_enrollments(course_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT e.id AS id, s.id AS student_id, s.student_id, s.major, s.current_semester,
               u.full_name, u.email,
               e.grade, e.attendance, e.enrolled_at
        FROM enrollments e
        JOIN students s ON e.student_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE e.course_id = ?
        ORDER BY u.full_name
    """, (course_id,)).fetchall()
    return [dict(r) for r in rows]


def get_all_students():
    conn = get_db()
    rows = conn.execute("""
        SELECT s.id AS student_id, s.student_id, s.major, s.current_semester, s.enrollment_date,
               u.full_name, u.email, u.username
        FROM students s
        JOIN users u ON s.user_id = u.id
        ORDER BY u.full_name
    """).fetchall()
    return [dict(r) for r in rows]


def get_student_full(student_id):
    conn = get_db()
    row = conn.execute("""
        SELECT s.id AS student_db_id, s.student_id, s.major, s.current_semester, s.enrollment_date,
               u.full_name, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.student_id = ?
    """, (student_id,)).fetchone()
    if not row:
        return None
    result = dict(row)
    result['enrollments'] = get_student_enrollments_by_student_id(result['student_db_id'])
    return result


def get_student_enrollments_by_student_id(student_db_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT c.code, c.name, c.credits, c.schedule, c.room,
               u.full_name AS professor_name,
               e.grade, e.attendance
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        LEFT JOIN professors p ON c.professor_id = p.id
        LEFT JOIN users u ON p.user_id = u.id
        WHERE e.student_id = ?
        ORDER BY c.code
    """, (student_db_id,)).fetchall()
    return [dict(r) for r in rows]


def create_course(code, name, description, credits, professor_user_id, semester, schedule, room):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM professors WHERE user_id = ?", (professor_user_id,))
    prof = c.fetchone()
    if not prof:
        return None
    prof_id = prof['id']
    c.execute(
        "INSERT INTO courses (code, name, description, credits, professor_id, semester, schedule, room) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (code, name, description, credits, prof_id, semester, schedule, room)
    )
    course_id = c.lastrowid
    conn.commit()
    return course_id


def update_course(course_id, name, description, credits, semester, schedule, room):
    conn = get_db()
    conn.execute(
        "UPDATE courses SET name=?, description=?, credits=?, semester=?, schedule=?, room=? WHERE id=?",
        (name, description, credits, semester, schedule, room, course_id)
    )
    conn.commit()


def delete_course(course_id):
    conn = get_db()
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()


def add_announcement(course_id, professor_user_id, title, content):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM professors WHERE user_id = ?", (professor_user_id,))
    prof = c.fetchone()
    if not prof:
        return False
    c.execute(
        "INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
        (course_id, prof['id'], title, content)
    )
    conn.commit()
    return True


def add_enrollment(student_id, course_id, semester="Fall 2026"):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO enrollments (student_id, course_id, semester) VALUES (?, ?, ?)",
            (student_id, course_id, semester)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    return success


def remove_enrollment(enrollment_id):
    conn = get_db()
    conn.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
    conn.commit()


def set_grade(enrollment_id, grade):
    conn = get_db()
    conn.execute("UPDATE enrollments SET grade = ? WHERE id = ?", (grade, enrollment_id))
    conn.commit()


def get_professor_dashboard_stats(professor_user_id):
    conn = get_db()
    stats = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM courses WHERE professor_id = (SELECT id FROM professors WHERE user_id = ?)) AS course_count,
            (SELECT COUNT(DISTINCT e.student_id) FROM enrollments e JOIN courses c ON e.course_id = c.id WHERE c.professor_id = (SELECT id FROM professors WHERE user_id = ?)) AS total_students,
            (SELECT COUNT(*) FROM announcements WHERE professor_id = (SELECT id FROM professors WHERE user_id = ?)) AS announcement_count
    """, (professor_user_id, professor_user_id, professor_user_id)).fetchone()
    return dict(stats)


def get_student_dashboard_stats(student_user_id):
    conn = get_db()
    stats = conn.execute("""
        SELECT
            COUNT(e.id) AS course_count,
            AVG(CASE WHEN e.grade = 'IP' THEN NULL ELSE
                CASE e.grade
                    WHEN 'A+' THEN 4.0 WHEN 'A' THEN 4.0 WHEN 'A-' THEN 3.7
                    WHEN 'B+' THEN 3.3 WHEN 'B' THEN 3.0 WHEN 'B-' THEN 2.7
                    WHEN 'C+' THEN 2.3 WHEN 'C' THEN 2.0 WHEN 'C-' THEN 1.7
                    WHEN 'D+' THEN 1.3 WHEN 'D' THEN 1.0 WHEN 'F' THEN 0.0
                    ELSE NULL
                END
            END) AS gpa,
            (SELECT AVG(attendance) FROM enrollments WHERE student_id = (SELECT id FROM students WHERE user_id = ?)) AS avg_attendance
    FROM enrollments e
    JOIN students s ON e.student_id = s.id
    JOIN users u ON s.user_id = u.id
    WHERE u.id = ?
    """, (student_user_id, student_user_id)).fetchone()
    return dict(stats)
