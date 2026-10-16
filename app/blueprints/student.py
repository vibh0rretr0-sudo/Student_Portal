from flask import Blueprint, render_template, session, redirect, url_for
from ..services.auth_service import student_required, get_current_student
from ..services.user_service import UserService, EnrollmentService
from ..services.course_service import CourseService

student_bp = Blueprint('student', __name__)

@student_bp.route("/dashboard")
@student_required
def dashboard():
    student = get_current_student()
    # Get real statistics from service
    stats = UserService.get_student_dashboard_stats(student["student_id"])
    courses = EnrollmentService.get_for_student_user(session["user_id"])
    username = session.get("username")
    return render_template(
        "student/dashboard.html",
        student=student,
        stats=stats,
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
    assignments = CourseService.get_assignments_for_course(course_id)
    username = session.get("username")
    return render_template(
        "student/course-detail.html",
        course=course,
        announcements=announcements,
        materials=materials,
        assignments=assignments,
        username=username,
    )

@student_bp.route("/profile")
@student_required
def profile():
    student = get_current_student()
    full = UserService.get_student_full(student["student_id"])
    username = session.get("username")
    return render_template("student/profile.html", student=student, full=full, username=username)

# Assignment Routes
@student_bp.route("/courses/<int:course_id>/assignments")
@student_required
def list_assignments(course_id):
    """List all assignments for a course."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    student = get_current_student()
    # Verify that the student is enrolled in this course
    enrollment = EnrollmentService.get_by_student_and_course(student["student_db_id"], course_id)
    if not enrollment:
        flash("You are not enrolled in this course", "error")
        return redirect(url_for("student.dashboard"))

    assignments = CourseService.get_assignments_for_course(course_id)

    # Check submission status for each assignment
    from ..models import Submission
    for assignment in assignments:
        # Check if student has submitted this assignment
        submission = Submission.query.filter_by(
            assignment_id=assignment['id'],
            student_id=student["student_id"]
        ).first()
        assignment['submission_status'] = submission is not None

    username = session.get("username")
    return render_template(
        "student/assignments.html",
        course=course,
        assignments=assignments,
        username=username
    )

@student_bp.route("/courses/<int:course_id>/assignments/<int:assignment_id>")
@student_required
def view_assignment(course_id, assignment_id):
    """View an assignment."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    student = get_current_student()
    # Verify that the student is enrolled in this course
    enrollment = EnrollmentService.get_by_student_and_course(student["student_db_id"], course_id)
    if not enrollment:
        flash("You are not enrolled in this course", "error")
        return redirect(url_for("student.dashboard"))

    assignment = CourseService.get_assignment_by_id(assignment_id)
    if not assignment or assignment['course_id'] != course_id:
        from flask import render_template
        return render_template("error.html", message="Assignment not found", code=404), 404

    # Check if student has already submitted this assignment
    from ..models import Submission
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=student["student_id"]
    ).first()
    submission_status = existing_submission is not None

    username = session.get("username")
    return render_template(
        "student/view_assignment.html",
        course=course,
        assignment=assignment,
        submission_status=submission_status,
        username=username
    )

@student_bp.route("/courses/<int:course_id>/assignments/<int:assignment_id>/submit", methods=["GET", "POST"])
@student_required
def submit_assignment(course_id, assignment_id):
    """Submit an assignment."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    student = get_current_student()
    # Verify that the student is enrolled in this course
    enrollment = EnrollmentService.get_by_student_and_course(student["student_db_id"], course_id)
    if not enrollment:
        flash("You are not enrolled in this course", "error")
        current_app.logger.warning(f'Unauthorized submission attempt: user {session.get("user_id")} not enrolled in course {course_id}')
        return redirect(url_for("student.dashboard"))

    assignment = CourseService.get_assignment_by_id(assignment_id)
    if not assignment or assignment['course_id'] != course_id:
        from flask import render_template
        return render_template("error.html", message="Assignment not found", code=404), 404

    # Check if assignment is past due
    from datetime import datetime
    if assignment['due_date'] and datetime.now() > assignment['due_date']:
        flash("This assignment is past due", "warning")

    # Check if student has already submitted this assignment
    from ..models import Submission, db
    existing_submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=student["student_id"]
    ).first()

    if existing_submission:
        flash("You have already submitted this assignment", "warning")
        return redirect(url_for("student.view_assignment", course_id=course_id, assignment_id=assignment_id))

    if request.method == "POST":
        # Handle file upload
        file_url = None
        material_type = 'pdf'
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Validate file extension
                allowed_extensions = {'pdf', 'zip', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt', 'ppt', 'pptx', 'xls', 'xlsx'}
                filename = secure_filename(file.filename)
                if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    flash("File type not allowed. Please upload a PDF, DOC, DOCX, JPG, PNG, TXT, PPT, XLS, or ZIP file.", "error")
                    current_app.logger.warning(f'Blocked submission file upload attempt: {filename} (user: {session.get("user_id")}, course: {course_id}, assignment: {assignment_id})')
                    return render_template("student/submit_assignment.html",
                                         course=course,
                                         assignment=assignment,
                                         username=session.get("username"))

                # Save file and get URL
                from werkzeug.utils import secure_filename
                import os
                from datetime import datetime

                filename = secure_filename(file.filename)
                # Add timestamp and student ID to avoid filename conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{student['student_id']}_{filename}"

                # Create course-specific upload directory for submissions
                course_upload_dir = os.path.join(current_app.config['UPLOADS_DIR'], 'submissions', str(course_id), str(assignment_id))
                os.makedirs(course_upload_dir, exist_ok=True)

                file_path = os.path.join(course_upload_dir, filename)
                file.save(file_path)

                # Store relative path for serving
                file_url = f"submissions/{course_id}/{assignment_id}/{filename}"

                # Determine file type from extension
                if filename.lower().endswith('.pdf'):
                    material_type = 'pdf'
                elif filename.lower().endswith('.zip'):
                    material_type = 'zip'
                else:
                    material_type = 'other'

        # Get optional text submission
        submission_text = request.form.get("submission_text", "").strip()

        # Validate that either file or text is provided
        if not file_url and not submission_text:
            flash("Please provide either a file submission or text submission", "error")
            current_app.logger.warning(f'Submission attempt with no content: user {session.get("user_id")}, course: {course_id}, assignment: {assignment_id}')
            return render_template("student/submit_assignment.html",
                                 course=course,
                                 assignment=assignment,
                                 username=session.get("username"))

        # Create submission record
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student["student_id"],
            file_url=file_url,
            submission_text=submission_text if submission_text else None
        )

        db.session.add(submission)
        db.session.commit()

        flash("Assignment submitted successfully!", "success")
        current_app.logger.info(f'Assignment submitted: {assignment["title"] if assignment else "Unknown"} (user: {session.get("user_id")}, course: {course_id}, assignment: {assignment_id})')
        return redirect(url_for("student.view_assignment", course_id=course_id, assignment_id=assignment_id))

    # GET request - show submission form
    username = session.get("username")
    return render_template(
        "student/submit_assignment.html",
        course=course,
        assignment=assignment,
        username=username
    )

@student_bp.route("/courses/<int:course_id>/assignments/<int:assignment_id>/submission/<int:submission_id>")
@student_required
def view_submission(course_id, assignment_id, submission_id):
    """View a submission."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    student = get_current_student()
    # Verify that the student is enrolled in this course
    enrollment = EnrollmentService.get_by_student_and_course(student["student_db_id"], course_id)
    if not enrollment:
        flash("You are not enrolled in this course", "error")
        return redirect(url_for("student.dashboard"))

    assignment = CourseService.get_assignment_by_id(assignment_id)
    if not assignment or assignment['course_id'] != course_id:
        from flask import render_template
        return render_template("error.html", message="Assignment not found", code=404), 404

    # Get the submission record
    from ..models import Submission
    submission = Submission.query.filter_by(
        id=submission_id,
        assignment_id=assignment_id,
        student_id=student["student_id"]
    ).first()

    if not submission:
        from flask import render_template
        return render_template("error.html", message="Submission not found", code=404), 404

    username = session.get("username")
    return render_template(
        "student/view_submission.html",
        course=course,
        assignment=assignment,
        submission=submission,
        username=username
    )
