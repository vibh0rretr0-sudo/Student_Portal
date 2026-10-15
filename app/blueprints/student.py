from flask import Blueprint, render_template, session, redirect, url_for
from auth import student_required, get_current_student
from app.services.user_service import UserService, EnrollmentService
from app.services.course_service import CourseService

student_bp = Blueprint('student', __name__)

@student_bp.route("/dashboard")
@student_required
def dashboard():
    student = get_current_student()
    # Stats handled in student_dashboard_stats logic (to be moved to service)
    courses = EnrollmentService.get_for_student_user(session["user_id"])
    username = session.get("username")
    return render_template(
        "student/dashboard.html",
        student=student,
        stats={}, # Placeholder until stat service is fully implemented
        courses=courses,
        username=username,
    )

@student_bp.route("/courses")
@student_required
def courses():
    student = get_current_student()
    courses = EnrollmentService.get_for_student_user(session["user_id"])
    username = session.get("username")
    return render_template(
        "student/courses.html",
        student=student,
        courses=courses,
        username=username,
    )

@student_bp.route("/courses/<int:course_id>")
@student_required
def course_detail(course_id):
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404
    announcements = CourseService.get_announcements(course_id)
    materials = CourseService.get_materials(course_id)
    username = session.get("username")
    return render_template(
        "student/course-detail.html",
        course=course,
        announcements=announcements,
        materials=materials,
        username=username,
    )

@student_bp.route("/profile")
@student_required
def profile():
    student = get_current_student()
    full = UserService.get_student_full(student["student_id"])
    username = session.get("username")
    return render_template("student/profile.html", student=student, full=full, username=username)
