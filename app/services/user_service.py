from app.database import get_db

class UserService:
    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_username(username):
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_student_full(student_id):
        db = get_db()
        row = db.execute("""
            SELECT s.id AS student_db_id, s.student_id, s.major, s.current_semester, s.enrollment_date,
                   u.full_name, u.email
            FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE s.student_id = ?
        """, (student_id,)).fetchone()
        if not row:
            return None
        result = dict(row)
        result['enrollments'] = EnrollmentService.get_by_student_db_id(result['student_db_id'])
        return result

    @staticmethod
    def get_all_students():
        db = get_db()
        rows = db.execute("""
            SELECT s.id AS student_id, s.student_id, s.major, s.current_semester, s.enrollment_date,
                   u.full_name, u.email, u.username
            FROM students s
            JOIN users u ON s.user_id = u.id
            ORDER BY u.full_name
        """).fetchall()
        return [dict(r) for r in rows]

class EnrollmentService:
    @staticmethod
    def get_by_student_db_id(student_db_id):
        db = get_db()
        rows = db.execute("""
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

    @staticmethod
    def get_for_student_user(student_user_id):
        db = get_db()
        rows = db.execute("""
            SELECT
                c.id AS course_id, c.code, c.name, c.description, c.credits,
                c.schedule, c.room, c.semester,
                u_prof.full_name AS professor_name, p.employee_id AS professor_id,
                e.grade, e.attendance, e.enrolled_at,
                (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id) AS enrollment_count
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            LEFT JOIN professors p ON c.professor_id = p.id
            LEFT JOIN users u_prof ON p.user_id = u.id
            JOIN students s ON e.student_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE u.id = ?
            ORDER BY c.code
        """, (student_user_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add(student_id, course_id, semester="Fall 2026"):
        db = get_db()
        try:
            db.execute(
                "INSERT INTO enrollments (student_id, course_id, semester) VALUES (?, ?, ?)",
                (student_id, course_id, semester)
            )
            db.commit()
            return True
        except Exception:
            return False

    @staticmethod
    def remove(enrollment_id):
        db = get_db()
        db.execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
        db.commit()

    @staticmethod
    def set_grade(enrollment_id, grade):
        db = get_db()
        db.execute("UPDATE enrollments SET grade = ? WHERE id = ?", (grade, enrollment_id))
        db.commit()
