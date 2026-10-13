import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, g, flash
from datetime import datetime

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEFAULT_SEMESTER = "Fall 2026"
    DEFAULT_CREDITS = 3
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "portal.db")

from database import (
    init_db, get_db,
    get_user_by_id,
    get_student_by_user_id, get_professor_by_user_id,
    get_student_enrollments, get_student_dashboard_stats,
    get_professor_courses, get_course_by_id, get_course_enrollments,
    get_course_announcements, get_course_materials,
    get_all_students, get_student_full,
    get_professor_dashboard_stats,
    create_course, update_course, delete_course,
    add_announcement, add_enrollment, remove_enrollment, set_grade,
)
from auth import (
    login_user, logout_user,
    login_required, student_required, professor_required,
    get_current_student, get_current_professor,
)

app = Flask(__name__)
app.config.from_object(Config)

if not app.config["SECRET_KEY"]:
    app.secret_key = "dev-fallback-key-replace-in-production"
else:
    app.secret_key = app.config["SECRET_KEY"]

app.config["SESSION_TYPE"] = "filesystem"


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    role = session.get("role")
    if role == "student":
        return redirect(url_for("student_dashboard"))
    elif role == "professor":
        return redirect(url_for("professor_dashboard"))
    return redirect(url_for("login"))


@app.before_request
def before_request():
    from database import get_db
    g.db = get_db()

@app.teardown_appcontext
def teardown_appcontext(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student_dashboard"))
        elif role == "professor":
            return redirect(url_for("professor_dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user, error = login_user(username, password)
        if error:
            return render_template("login.html", error=error)
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student_dashboard"))
        elif role == "professor":
            return redirect(url_for("professor_dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/student/dashboard")
@student_required
def student_dashboard():
    student = get_current_student()
    stats = get_student_dashboard_stats(session["user_id"])
    courses = get_student_enrollments(session["user_id"])
    username = session.get("username")
    return render_template(
        "student/dashboard.html",
        student=student,
        stats=stats,
        courses=courses,
        username=username,
    )


@app.route("/student/courses")
@student_required
def student_courses():
    student = get_current_student()
    courses = get_student_enrollments(session["user_id"])
    username = session.get("username")
    return render_template(
        "student/courses.html",
        student=student,
        courses=courses,
        username=username,
    )


@app.route("/student/courses/<int:course_id>")
@student_required
def student_course_detail(course_id):
    course = get_course_by_id(course_id)
    if not course:
        return render_template("error.html", message="Course not found", code=404), 404
    announcements = get_course_announcements(course_id)
    materials = get_course_materials(course_id)
    username = session.get("username")
    return render_template(
        "student/course-detail.html",
        course=course,
        announcements=announcements,
        materials=materials,
        username=username,
    )


@app.route("/student/profile")
@student_required
def student_profile():
    student = get_current_student()
    full = get_student_full(student["student_id"])
    username = session.get("username")
    return render_template("student/profile.html", student=student, full=full, username=username)


@app.route("/professor/dashboard")
@professor_required
def professor_dashboard():
    professor = get_current_professor()
    stats = get_professor_dashboard_stats(session["user_id"])
    courses = get_professor_courses(session["user_id"])
    username = session.get("username")
    return render_template(
        "professor/dashboard.html",
        professor=professor,
        stats=stats,
        courses=courses,
        username=username,
    )


@app.route("/professor/courses")
@professor_required
def professor_courses():
    professor = get_current_professor()
    courses = get_professor_courses(session["user_id"])
    username = session.get("username")
    return render_template(
        "professor/courses.html",
        professor=professor,
        courses=courses,
        username=username,
    )


@app.route("/professor/courses/new", methods=["GET", "POST"])
@professor_required
def professor_create_course():
    professor = get_current_professor()
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        try:
            credits = int(request.form.get("credits", app.config["DEFAULT_CREDITS"]))
            if credits <= 0:
                raise ValueError("Credits must be positive")
        except (ValueError, TypeError):
            flash("Invalid credits. Please enter a positive number.", "error")
            return render_template("professor/manage-course.html", professor=professor,
                                   mode="create", username=session.get("username"))

        semester = request.form.get("semester", app.config["DEFAULT_SEMESTER"]).strip()
        schedule = request.form.get("schedule", "").strip()
        room = request.form.get("room", "").strip()
        if not code or not name:
            flash("Course code and name are required", "error")
            return render_template("professor/manage-course.html", professor=professor,
                                   mode="create", username=session.get("username"))
        existing = get_db().execute("SELECT id FROM courses WHERE code = ?", (code,)).fetchone()
        if existing:
            flash(f"Course code '{code}' already exists", "error")
            return render_template("professor/manage-course.html", professor=professor,
                                   mode="create", username=session.get("username"))
        course_id = create_course(code, name, description, credits, session["user_id"], semester, schedule, room)
        if course_id:
            flash("Course created successfully!", "success")
            return redirect(url_for("professor_courses"))
        flash("Failed to create course", "error")
        return render_template("professor/manage-course.html", professor=professor,
                               mode="create", username=session.get("username"))
    return render_template("professor/manage-course.html", professor=professor,
                           mode="create", username=session.get("username"))


@app.route("/professor/courses/<int:course_id>")
@professor_required
def professor_course_detail(course_id):
    course = get_course_by_id(course_id)
    if not course:
        return render_template("error.html", message="Course not found", code=404), 404
    professor = get_current_professor()
    enrollments = get_course_enrollments(course_id)
    announcements = get_course_announcements(course_id)
    materials = get_course_materials(course_id)
    enrolled_ids = [e['student_id'] for e in enrollments]
    all_students = get_all_students()
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


@app.route("/professor/courses/<int:course_id>/edit", methods=["GET", "POST"])
@professor_required
def professor_edit_course(course_id):
    course = get_course_by_id(course_id)
    if not course:
        return render_template("error.html", message="Course not found", code=404), 404
    professor = get_current_professor()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        try:
            credits = int(request.form.get("credits", app.config["DEFAULT_CREDITS"]))
            if credits <= 0:
                raise ValueError("Credits must be positive")
        except (ValueError, TypeError):
            flash("Invalid credits. Please enter a positive number.", "error")
            return render_template("professor/manage-course.html", professor=professor,
                                   course=course, mode="edit", username=session.get("username"))

        semester = request.form.get("semester", app.config["DEFAULT_SEMESTER"]).strip()
        schedule = request.form.get("schedule", "").strip()
        room = request.form.get("room", "").strip()
        if not name:
            flash("Course name is required", "error")
            return render_template("professor/manage-course.html", professor=professor,
                                   course=course, mode="edit", username=session.get("username"))
        update_course(course_id, name, description, credits, semester, schedule, room)
        flash("Course updated successfully!", "success")
        return redirect(url_for("professor_course_detail", course_id=course_id))
    return render_template("professor/manage-course.html", professor=professor,
                           course=course, mode="edit", username=session.get("username"))


@app.route("/professor/courses/<int:course_id>/delete", methods=["POST"])
@professor_required
def professor_delete_course(course_id):
    delete_course(course_id)
    flash("Course deleted successfully.", "success")
    return redirect(url_for("professor_courses"))


@app.route("/professor/courses/<int:course_id>/announcements", methods=["POST"])
@professor_required
def professor_add_announcement(course_id):
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    if title and content:
        if add_announcement(course_id, session["user_id"], title, content):
            flash("Announcement posted successfully!", "success")
        else:
            flash("Failed to post announcement.", "error")
    else:
        flash("Both title and content are required.", "error")
    return redirect(url_for("professor_course_detail", course_id=course_id))


@app.route("/professor/students")
@professor_required
def professor_students():
    professor = get_current_professor()
    all_students = get_all_students()
    username = session.get("username")
    return render_template(
        "professor/students.html",
        professor=professor,
        students=all_students,
        username=username,
    )


@app.route("/professor/students/<student_id>")
@professor_required
def professor_student_detail(student_id):
    student = get_student_full(student_id)
    if not student:
        return render_template("error.html", message="Student not found", code=404), 404
    professor = get_current_professor()
    username = session.get("username")
    return render_template(
        "professor/student-detail.html",
        student=student,
        username=username,
    )


@app.route("/professor/courses/<int:course_id>/enroll", methods=["POST"])
@professor_required
def professor_enroll_student(course_id):
    student_id_input = request.form.get("student_id", "").strip()
    if student_id_input:
        # Verify student exists before attempting enrollment
        student = get_db().execute("SELECT id FROM students WHERE student_id = ?", (student_id_input,)).fetchone()
        if student:
            if add_enrollment(student['id'], course_id):
                flash("Student enrolled successfully!", "success")
            else:
                flash("Student is already enrolled in this course.", "error")
        else:
            flash("Student ID not found.", "error")
    else:
        flash("Student ID is required.", "error")
    return redirect(url_for("professor_course_detail", course_id=course_id))


@app.route("/professor/enrollments/<int:enrollment_id>/remove", methods=["POST"])
@professor_required
def professor_remove_enrollment(enrollment_id):
    # Verify enrollment exists before removal
    enrollment = get_db().execute("SELECT id FROM enrollments WHERE id = ?", (enrollment_id,)).fetchone()
    if enrollment:
        remove_enrollment(enrollment_id)
        flash("Student removed from course.", "success")
    else:
        flash("Enrollment record not found.", "error")
    return redirect(request.referrer or url_for("professor_dashboard"))


@app.route("/professor/enrollments/<int:enrollment_id>/grade", methods=["POST"])
@professor_required
def professor_set_grade(enrollment_id):
    grade = request.form.get("grade", "").strip().upper()
    valid_grades = ["IP", "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]
    if grade in valid_grades:
        # Verify enrollment exists before setting grade
        enrollment = get_db().execute("SELECT id FROM enrollments WHERE id = ?", (enrollment_id,)).fetchone()
        if enrollment:
            set_grade(enrollment_id, grade)
            flash("Grade updated successfully!", "success")
        else:
            flash("Enrollment record not found.", "error")
    else:
        flash("Invalid grade entered.", "error")
    return redirect(request.referrer or url_for("professor_dashboard"))


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    user, error = login_user(username, password)
    if error:
        return jsonify({"error": error}), 401
    return jsonify({
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"],
            "email": user["email"],
        }
    })


@app.route("/api/logout", methods=["POST"])
def api_logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/api/me", methods=["GET"])
@login_required
def api_me():
    user = get_user_by_id(session["user_id"])
    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
        "email": user["email"],
    })


@app.route("/materials/<path:filename>")
def serve_material(filename):
    materials_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "assets", "materials")
    return send_from_directory(materials_dir, filename)


@app.context_processor
def inject_helpers():
    def fmt_date(date_str):
        if not date_str:
            return '—'
        try:
            parts = date_str.split('T')[0].split('-')
            if len(parts) != 3:
                return date_str
            return datetime.strptime(parts[0] + '-' + parts[1] + '-' + parts[2], '%Y-%m-%d').strftime('%b %d, %Y')
        except Exception:
            return str(date_str)
    def fmt_time(date_str):
        if not date_str:
            return '—'
        try:
            parts = date_str.split('T')
            if len(parts) == 2:
                t = parts[1].split('.')[0]
                if t:
                    return t[:5]
        except Exception:
            pass
        return ''
    return {'now': datetime.now(), 'formatDate': fmt_date, 'formatTime': fmt_time}


@app.template_filter('average')
def average_filter(seq):
    seq = list(seq)
    if not seq:
        return 0
    return sum(seq) / len(seq)


@app.template_filter('sum')
def sum_filter(seq, attribute=None):
    seq = list(seq)
    if attribute:
        return sum(getattr(item, attribute) for item in seq if hasattr(item, attribute))
    return sum(seq)


@app.template_filter('selectattr')
def selectattr_filter(seq, attribute, value=None, reverse=False):
    result = [item for item in seq if hasattr(item, attribute)]
    if value is not None:
        result = [item for item in result if getattr(item, attribute) == value]
    if reverse:
        return [item for item in seq if hasattr(item, attribute) and getattr(item, attribute) != value]
    return result


@app.template_filter('rejectattr')
def rejectattr_filter(seq, attribute, value=None):
    if value is not None:
        return [item for item in seq if not hasattr(item, attribute) or getattr(item, attribute) != value]
    return [item for item in seq if not hasattr(item, attribute)]


@app.template_filter('map')
def map_filter(seq, attribute):
    return [getattr(item, attribute) for item in seq if hasattr(item, attribute)]


@app.template_filter('select')
def select_filter(seq, test):
    return [item for item in seq if test(item)]


@app.template_filter('reject')
def reject_filter(seq, test):
    return [item for item in seq if not test(item)]


@app.template_filter('list')
def list_filter(seq):
    return list(seq)


@app.template_filter('replace')
def replace_filter(value, old, new=None):
    if new is None:
        return value.replace(old, '')
    return value.replace(old, new)


GRADE_POINTS = {
    'A+': 4.0, 'A': 4.0, 'A-': 3.7,
    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
    'D+': 1.3, 'D': 1.0, 'F': 0.0,
}


@app.template_filter('get_grade_points')
def get_grade_points_filter(grade):
    return GRADE_POINTS.get(grade, 0.0)


def init_app():
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "portal.db")):
        init_db()


if __name__ == "__main__":
    init_app()
    app.run(debug=False, host="127.0.0.1", port=5000)
