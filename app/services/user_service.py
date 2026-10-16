from ..models import db, User, Student, Professor, Enrollment, Course


class UserService:
    @staticmethod
    def get_by_id(user_id):
        """Get a user by ID."""
        return User.query.get(user_id)

    @staticmethod
    def get_by_username(username):
        """Get a user by username."""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def create_user(username, password, full_name, role="student", email=None):
        """Create a new user."""
        # Check if user already exists
        if UserService.get_by_username(username):
            return None, "Username already exists"

        # Validate inputs
        if not username or not username.strip():
            return None, "Username is required"

        if not password or len(password) < 6:
            return None, "Password must be at least 6 characters long"

        if not full_name or not full_name.strip():
            return None, "Full name is required"

        if role not in ["student", "professor"]:
            return None, "Role must be either 'student' or 'professor'"

        # Create user
        user = User(
            username=username.strip(),
            full_name=full_name.strip(),
            role=role,
            email=email.strip() if email else None
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user, None

    @staticmethod
    def get_student_full(student_id):
        """Get full student information by student ID."""
        # Find student by student_id
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return None

        # Get basic student info
        result = {
            'student_db_id': student.id,
            'student_id': student.student_id,
            'major': student.major,
            'current_semester': student.current_semester,
            'enrollment_date': student.enrollment_date,
            'full_name': student.user.full_name,
            'email': student.user.email
        }

        # Get enrollments
        result['enrollments'] = EnrollmentService.get_by_student_db_id(student.id)
        return result

    @staticmethod
    def get_student_dashboard_stats(student_id):
        """Get statistics for student dashboard."""
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return {}

        # Get enrollments
        enrollments = EnrollmentService.get_by_student_db_id(student.id)

        # Calculate statistics
        total_courses = len(enrollments)

        # Calculate GPA (if grades exist)
        grades = [e.get('grade') for e in enrollments if e.get('grade') and e.get('grade') not in ['IP', '']]
        grade_points = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        }

        gpa = None
        if grades:
            total_points = sum(grade_points.get(grade, 0.0) for grade in grades)
            gpa = round(total_points / len(grades), 2) if grades else None

        # Calculate total credits
        total_credits = sum(e.get('credits', 0) for e in enrollments)

        # Count completed courses (those with grades)
        completed_courses = len([e for e in enrollments if e.get('grade') and e.get('grade') not in ['IP', '']])

        # Count in-progress courses
        in_progress_courses = len([e for e in enrollments if e.get('grade') == 'IP'])

        return {
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'in_progress_courses': in_progress_courses,
            'gpa': gpa,
            'total_credits': total_credits,
            'current_semester': student.current_semester
        }

    @staticmethod
    def get_all_students():
        """Get all students."""
        students = Student.query.join(User).add_columns(
            Student.id.label('student_db_id'),
            Student.student_id,
            Student.major,
            Student.current_semester,
            Student.enrollment_date,
            User.full_name,
            User.email,
            User.username
        ).order_by(User.full_name).all()

        result = []
        for row in students:
            result.append({
                'student_id': row.student_id,
                'student_number': row.student_id,  # Backward compatibility
                'major': row.major,
                'current_semester': row.current_semester,
                'enrollment_date': row.enrollment_date,
                'full_name': row.full_name,
                'email': row.email,
                'username': row.username
            })

        return result


class EnrollmentService:
    @staticmethod
    def get_by_student_db_id(student_db_id):
        """Get enrollments for a student by student database ID."""
        enrollments = Enrollment.query.filter_by(student_id=student_db_id)\
            .join(Course)\
            .outerjoin(Professor)\
            .outerjoin(User, Professor.user_id == User.id)\
            .add_columns(
                Enrollment.id,
                Course.code,
                Course.name,
                Course.credits,
                Course.schedule,
                Course.room,
                User.full_name.label('professor_name'),
                Enrollment.grade,
                Enrollment.attendance
            )\
            .order_by(Course.code)\
            .all()

        result = []
        for row in enrollments:
            result.append({
                'id': row.id,
                'code': row.code,
                'name': row.name,
                'credits': row.credits,
                'schedule': row.schedule,
                'room': row.room,
                'professor_name': row.professor_name,
                'grade': row.grade,
                'attendance': row.attendance
            })

        return result

    @staticmethod
    def get_for_student_user(student_user_id):
        """Get all enrollments for a student by user ID."""
        # Get student record from user ID
        student = Student.query.filter_by(user_id=student_user_id).first()
        if not student:
            return []

        enrollments = Enrollment.query.filter_by(student_id=student.id)\
            .join(Course)\
            .join(Professor)\
            .all()

        result = []
        for enrollment in enrollments:
            course = enrollment.course
            professor = enrollment.course.professor
            user = professor.user if professor else None
            result.append({
                'course_id': course.id,
                'code': course.code,
                'name': course.name,
                'description': course.description,
                'credits': course.credits,
                'schedule': course.schedule,
                'room': course.room,
                'semester': course.semester,
                'professor_name': user.full_name if user else None,
                'professor_id': professor.employee_id if professor else None,
                'grade': enrollment.grade,
                'attendance': enrollment.attendance,
                'enrolled_at': enrollment.enrolled_at
            })

        return result

    @staticmethod
    def add(student_id, course_id, semester="Fall 2026"):
        """Add an enrollment for a student in a course."""
        # Check if enrollment already exists (prevent duplicates)
        existing = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            semester=semester
        ).first()

        if existing:
            return False  # Already enrolled

        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            semester=semester
        )

        db.session.add(enrollment)
        db.session.commit()
        return True

    @staticmethod
    def remove(enrollment_id):
        """Remove an enrollment."""
        enrollment = Enrollment.query.get(enrollment_id)
        if not enrollment:
            return False

        db.session.delete(enrollment)
        db.session.commit()
        return True

    @staticmethod
    def set_grade(enrollment_id, grade):
        """Set grade for an enrollment."""
        enrollment = Enrollment.query.get(enrollment_id)
        if not enrollment:
            return False

        enrollment.grade = grade
        db.session.commit()
        return True