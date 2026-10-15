from app.database import get_db

class CourseService:
    @staticmethod
    def get_by_id(course_id):
        db = get_db()
        row = db.execute("""
            SELECT c.*, u.full_name AS professor_name, u.email AS professor_email, p.employee_id AS professor_id
            FROM courses c
            LEFT JOIN professors p ON c.professor_id = p.id
            LEFT JOIN users u ON p.user_id = u.id
            WHERE c.id = ?
        """, (course_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_for_professor(professor_user_id):
        db = get_db()
        rows = db.execute("""
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

    @staticmethod
    def create(code, name, description, credits, professor_user_id, semester, schedule, room):
        db = get_db()
        # Get professor internal id
        prof = db.execute("SELECT id FROM professors WHERE user_id = ?", (professor_user_id,)).fetchone()
        if not prof:
            return None

        cursor = db.execute(
            "INSERT INTO courses (code, name, description, credits, professor_id, semester, schedule, room) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (code, name, description, credits, prof['id'], semester, schedule, room)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update(course_id, name, description, credits, semester, schedule, room):
        db = get_db()
        db.execute(
            "UPDATE courses SET name=?, description=?, credits=?, semester=?, schedule=?, room=? WHERE id=?",
            (name, description, credits, semester, schedule, room, course_id)
        )
        db.commit()

    @staticmethod
    def delete(course_id):
        db = get_db()
        db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        db.commit()

    @staticmethod
    def get_announcements(course_id):
        db = get_db()
        rows = db.execute("""
            SELECT a.*, u.full_name AS professor_name
            FROM announcements a
            JOIN professors p ON a.professor_id = p.id
            JOIN users u ON p.user_id = u.id
            WHERE a.course_id = ?
            ORDER BY a.created_at DESC
        """, (course_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_materials(course_id):
        db = get_db()
        rows = db.execute("SELECT * FROM course_materials WHERE course_id = ? ORDER BY uploaded_at DESC", (course_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_announcement(course_id, professor_user_id, title, content):
        db = get_db()
        prof = db.execute("SELECT id FROM professors WHERE user_id = ?", (professor_user_id,)).fetchone()
        if not prof:
            return False
        db.execute(
            "INSERT INTO announcements (course_id, professor_id, title, content) VALUES (?, ?, ?, ?)",
            (course_id, prof['id'], title, content)
        )
        db.commit()
        return True

class CourseEnrollmentService:
    @staticmethod
    def get_for_course(course_id):
        db = get_db()
        rows = db.execute("""
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
