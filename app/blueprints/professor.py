from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from auth import professor_required, get_current_professor
from app.services.course_service import CourseService, CourseEnrollmentService
from app.services.user_service import UserService

professor_bp = Blueprint('professor', __name__)

@professor_bp.route("/dashboard")
@professor_required
def dashboard():
    professor = get_current_professor()
    courses = CourseService.get_for_professor(session["user_id"])
    username = session.get("username")
    return render_template(
        "professor/dashboard.html",
        professor=professor,
        stats={}, # Placeholder until stat service is fully implemented
        courses=courses,
        username=username,
    )

@professor_bp.route("/courses")
@professor_required
def courses():
    professor = get_current_professor()
    courses = CourseService.get_for_professor(session["user_id"])
    username = session.get("username")
    return render_template(
        "professor/courses.html",
        professor=professor,
        courses=courses,
        username=username,
    )

@professor_bp.route("/courses/new", methods=["GET", "POST"])
@professor_required
def create_course():
    professor = get_current_professor()
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        try:
            credits = int(request.form.get("credits", "3"))
            if credits <= 0:
                raise ValueError("Credits must be positive")
        except (ValueError, TypeError):
            flash("Invalid credits. Please enter a positive number.", "error")
            return render_template("professor/manage-course.html", professor=professor, mode="create", username=session.get("username"))

        semester = request.form.get("semester", "Fall 2026").strip()
        schedule = request.form.get("schedule", "").strip()
        room = request.form.get("room", "").strip()
        if not code or not name:
            flash("Course code and name are required", "error")
            return render_template("professor/manage-course.html", professor=professor, mode="create", username=session.get("username"))

        # Using Service Layer instead of raw DB call
        course_id = CourseService.create(code, name, description, credits, session["user_id"], semester, schedule, room)
        if course_id:
            flash("Course created successfully!", "success")
            return redirect(url_for("professor.courses"))
        flash("Failed to create course", "error")
        return render_template("professor/manage-course.html", professor=professor, mode="create", username=session.get("username"))

    return render_template("professor/manage-course.html", professor=professor, mode="create", username=session.get("username"))

@professor_bp.route("/courses/<int:course_id>")
@professor_required
def course_detail(course_id):
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404
    professor = get_current_professor()
    enrollments = CourseEnrollmentService.get_for_course(course_id)
    announcements = CourseService.get_announcements(course_id)
    materials = CourseService.get_materials(course_id)
    enrolled_ids = [e['student_id'] for e in enrollments]
    all_students = UserService.get_all_students()
    username = session.get("username")
    return render_template(
        "professor/course-detail.html",
        course=course,
        enrollments=enrollments,
        announcements=announcements,
        materials=materials,
        all_students=all_students,
        enrolled_ids=enrolled_ids,
        username=username,
    )

@professor_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@professor_required
def edit_course(course_id):
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404
    professor = get_current_professor()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        try:
            credits = int(request.form.get("credits", "3"))
            if credits <= 0:
                raise ValueError("Credits must be positive")
        except (ValueError, TypeError):
            flash("Invalid credits. Please enter a positive number.", "error")
            return render_template("professor/manage-course.html", professor=professor, course=course, mode="edit", username=session.get("username"))

        semester = request.form.get("semester", "Fall 2026").strip()
        schedule = request.form.get("schedule", "").strip()
        room = request.form.get("room", "").strip()
        if not name:
            flash("Course name is required", "error")
            return render_template("professor/manage-course.html", professor=professor, course=course, mode="edit", username=session.get("username"))
        CourseService.update(course_id, name, description, credits, semester, schedule, room)
        flash("Course updated successfully!", "success")
        return redirect(url_for("professor.course_detail", course_id=course_id))
    return render_template("professor/manage-course.html", professor=professor, course=course, mode="edit", username=session.get("username"))

@professor_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@professor_required
def delete_course(course_id):
    CourseService.delete(course_id)
    flash("Course deleted successfully.", "success")
    return redirect(url_for("professor.courses"))

@professor_bp.route("/courses/<int:course_id>/announcements", methods=["POST"])
@professor_required
def add_announcement(course_id):
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    if title and content:
        if CourseService.add_announcement(course_id, session["user_id"], title, content):
            flash("Announcement posted successfully!", "success")
        else:
            flash("Failed to post announcement.", "error")
    else:
        flash("Both title and content are required.", "error")
    return redirect(url_for("professor.course_detail", course_id=course_id))

@professor_bp.route("/students")
@professor_required
def students():
    professor = get_current_professor()
    all_students = UserService.get_all_students()
    username = session.get("username")
    return render_template(
        "professor/students.html",
        professor=professor,
        students=all_students,
        username=username,
    )

@professor_bp.route("/students/<student_id>")
@professor_required
def student_detail(student_id):
    student = UserService.get_student_full(student_id)
    if not student:
        from flask import render_template
        return render_template("error.html", message="Student not found", code=404), 404
    professor = get_current_professor()
    username = session.get("username")
    return render_template(
        "professor/student-detail.html",
        student=student,
        username=username,
    )

@professor_bp.route("/courses/<int:course_id>/enroll", methods=["POST"])
@professor_required
def enroll_student(course_id):
    student_id_input = request.form.get("student_id", "").strip()
    if student_id_input:
        from app.database import get_db
        student = get_db().execute("SELECT id FROM students WHERE student_id = ?", (student_id_input,)).fetchone()
        if student:
            from app.services.user_service import EnrollmentService
            if EnrollmentService.add(student['id'], course_id):
                flash("Student enrolled successfully!", "success")
            else:
                flash("Student is already enrolled in this course.", "error")
        else:
            flash("Student ID not found.", "error")
    else:
        flash("Student ID is required.", "error")
    return redirect(url_for("professor.course_detail", course_id=course_id))

@professor_bp.route("/enrollments/<int:enrollment_id>/remove", methods=["POST"])
@professor_required
def remove_remove_enrollment(enrollment_id):
    from app.services.user_service import EnrollmentService
    EnrollmentService.remove(enrollment_id)
    flash("Student removed from course.", "success")
    return redirect(request.referrer or url_for("professor.dashboard"))

@professor_bp.route("/enrollments/<int:enrollment_id>/grade", methods=["POST"])
@professor_required
def set_grade_action(enrollment_id):
    grade = request.form.get("grade", "").strip().upper()
    valid_grades = ["IP", "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]
    if grade in valid_grades:
        from app.services.user_service import EnrollmentService
        EnrollmentService.set_grade(enrollment_id, grade)
        flash("Grade updated successfully!", "success")
    else:
        flash("Invalid grade entered.", "error")
    return redirect(request.referrer or url_for("professor.dashboard"))
