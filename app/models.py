"""
Database models for Student Portal.
Defines the data structure for the application.
"""

from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """User model for students and professors."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    _password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'professor'
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, lazy=True)
    professor_profile = db.relationship('Professor', backref='user', uselist=False, lazy=True)

    def set_password(self, password):
        """Hash and set password."""
        self._password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash."""
        return check_password_hash(self._password_hash, password)

    @property
    def is_student(self):
        """Check if user is a student."""
        return self.role == 'student'

    @property
    def is_professor(self):
        """Check if user is a professor."""
        return self.role == 'professor'

    def __repr__(self):
        return f'<User {self.username}: {self.full_name}>'


class Student(db.Model):
    """Student profile model."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    major = db.Column(db.String(100), nullable=True)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    current_semester = db.Column(db.Integer, default=1)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

    def __repr__(self):
        return f'<Student {self.student_id}: {self.user.full_name}>'


class Professor(db.Model):
    """Professor profile model."""
    __tablename__ = 'professors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(50), nullable=True)

    # Relationships
    courses = db.relationship('Course', backref='professor', lazy=True)

    def __repr__(self):
        return f'<Professor {self.employee_id}: {self.user.full_name}>'


class Course(db.Model):
    """Course model."""
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    credits = db.Column(db.Integer, default=3)
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'), nullable=True)
    semester = db.Column(db.String(20), default='Fall 2026')
    schedule = db.Column(db.String(50), nullable=True)
    room = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    announcements = db.relationship('Announcement', backref='course', lazy=True)
    course_materials = db.relationship('CourseMaterial', backref='course', lazy=True)

    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'


class Enrollment(db.Model):
    """Enrollment model linking students to courses."""
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    semester = db.Column(db.String(20), default='Fall 2026')
    grade = db.Column(db.String(5), nullable=True)  # e.g., 'A', 'B+', etc.
    attendance = db.Column(db.Float, default=0.0)  # Percentage
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure a student can only enroll in a course once per semester
    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', 'semester', name='_student_course_semester_uc'),)

    def __repr__(self):
        return f'<Enrollment {self.student.user.full_name} in {self.course.code}>'


class Announcement(db.Model):
    """Announcement model for course communications."""
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Announcement {self.title}>'


class CourseMaterial(db.Model):
    """Course material model for resources like lecture notes, assignments."""
    __tablename__ = 'course_materials'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    file_url = db.Column(db.String(255), nullable=True)
    material_type = db.Column(db.String(50), default='pdf')  # pdf, zip, video, etc.
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Assignment-specific fields
    is_assignment = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime, nullable=True)
    max_points = db.Column(db.Integer, default=100)

    def __repr__(self):
        if self.is_assignment:
            return f'<Assignment {self.title}>'
        return f'<CourseMaterial {self.title}>'


class Submission(db.Model):
    """Student submission model for assignments."""
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('course_materials.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    file_url = db.Column(db.String(255), nullable=True)
    submission_text = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    grade = db.Column(db.Integer, nullable=True)  # Actual points earned
    feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    assignment = db.relationship('CourseMaterial', backref='submissions')
    student = db.relationship('Student', backref='submissions')

    # Ensure a student can only submit once per assignment
    __table_args__ = (db.UniqueConstraint('assignment_id', 'student_id', name='_assignment_student_uc'),)

    def __repr__(self):
        return f'<Submission {self.student.user.full_name} to {self.assignment.title}>'