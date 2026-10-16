from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from ..services.auth_service import professor_required, get_current_professor
from ..services.course_service import CourseService, CourseEnrollmentService
from ..services.user_service import UserService

professor_bp = Blueprint('professor', __name__)

@professor_bp.route("/dashboard")
@professor_required
def dashboard():
    professor = get_current_professor()
    # Get real statistics from service
    stats = CourseService.get_professor_dashboard_stats(session["user_id"])
    courses = CourseService.get_for_professor(session["user_id"])
    username = session.get("username")
    return render_template(
        "professor/dashboard.html",
        professor=professor,
        stats=stats,
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
    assignments = CourseService.get_assignments_for_course(course_id)
    enrolled_ids = [e['student_id'] for e in enrollments]
    all_students = UserService.get_all_students()
    username = session.get("username")
    return render_template(
        "professor/course-detail.html",
        course=course,
        enrollments=enrollments,
        announcements=announcements,
        materials=materials,
        assignments=assignments,
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
        from app.services.user_service import UserService
        student = UserService.get_by_username(student_id_input)
        if student and student.is_student:
            from app.services.user_service import EnrollmentService
            # Get the student's database ID from the user record
            from app.models import Student
            student_record = Student.query.filter_by(user_id=student.id).first()
            if student_record:
                if EnrollmentService.add(student_record.id, course_id):
                    flash("Student enrolled successfully!", "success")
                else:
                    flash("Student is already enrolled in this course.", "error")
            else:
                flash("Student profile not found.", "error")
        else:
            flash("Student not found or not a student account.", "error")
    else:
        flash("Student ID is required.", "error")
    return redirect(url_for("professor.course_detail", course_id=course_id))

@professor_bp.route("/enrollments/<int:enrollment_id>/remove", methods=["POST"])
@professor_required
def remove_enrollment(enrollment_id):
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

# Assignment Management Routes
@professor_bp.route("/courses/<int:course_id>/assignments")
@professor_required
def list_assignments(course_id):
    """List all assignments for a course."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    professor = get_current_professor()
    # Verify that the professor owns this course
    if course.professor_id != professor.id:
        flash("You are not authorized to view assignments for this course.", "error")
        return redirect(url_for("professor.dashboard"))

    assignments = CourseService.get_assignments_for_course(course_id)

    # Add submission count to each assignment
    for assignment in assignments:
        assignment['submission_count'] = CourseService.get_submission_count(assignment['id'])

    username = session.get("username")
    return render_template(
        "professor/assignments.html",
        course=course,
        assignments=assignments,
        username=username
    )

@professor_bp.route("/courses/<int:course_id>/assignments/new", methods=["GET", "POST"])
@professor_required
def create_assignment(course_id):
    """Create a new assignment for a course."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    professor = get_current_professor()
    # Verify that the professor owns this course
    if course.professor_id != professor.id:
        flash("You are not authorized to create assignments for this course.", "error")
        current_app.logger.warning(f'Unauthorized assignment creation attempt by user {session.get("user_id")} for course {course_id}')
        return redirect(url_for("professor.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date_str = request.form.get("due_date", "").strip()
        max_points_str = request.form.get("max_points", "100").strip()

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
                    current_app.logger.warning(f'Blocked assignment file upload attempt: {filename} (user: {session.get("user_id")}, course: {course_id})')
                    return render_template("professor/manage_assignment.html",
                                         course=course,
                                         mode="create",
                                         username=session.get("username"))

                # Save file and get URL
                from werkzeug.utils import secure_filename
                import os
                from datetime import datetime

                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"

                # Create course-specific upload directory
                course_upload_dir = os.path.join(current_app.config['UPLOADS_DIR'], 'assignments', str(course_id))
                os.makedirs(course_upload_dir, exist_ok=True)

                file_path = os.path.join(course_upload_dir, filename)
                file.save(file_path)

                # Store relative path for serving
                file_url = f"assignments/{course_id}/{filename}"

                # Determine file type from extension
                if filename.lower().endswith('.pdf'):
                    material_type = 'pdf'
                elif filename.lower().endswith('.zip'):
                    material_type = 'zip'
                else:
                    material_type = 'other'

        # Validate inputs
        if not title:
            flash("Assignment title is required", "error")
            return render_template("professor/manage_assignment.html",
                                 course=course,
                                 mode="create",
                                 username=session.get("username"))

        try:
            max_points = int(max_points_str)
            if max_points <= 0:
                raise ValueError("Max points must be positive")
        except (ValueError, TypeError):
            flash("Max points must be a positive number", "error")
            return render_template("professor/manage_assignment.html",
                                 course=course,
                                 mode="create",
                                 username=session.get("username"))

        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Invalid due date format", "error")
                return render_template("professor/manage_assignment.html",
                                     course=course,
                                     mode="create",
                                     username=session.get("username"))

        # Create assignment using service
        assignment_id = CourseService.create_assignment(
            course_id=course_id,
            professor_user_id=session["user_id"],
            title=title,
            file_url=file_url,
            material_type=material_type,
            due_date=due_date,
            max_points=max_points
        )

        if assignment_id:
            flash("Assignment created successfully!", "success")
            current_app.logger.info(f'Assignment created: {title} (user: {session.get("user_id")}, course: {course_id})')
            return redirect(url_for("professor.list_assignments", course_id=course_id))
        else:
            flash("Failed to create assignment", "error")
            current_app.logger.error(f'Failed to create assignment: {title} (user: {session.get("user_id")}, course: {course_id})')

    # GET request - show form
    username = session.get("username")
    return render_template(
        "professor/manage_assignment.html",
        course=course,
        mode="create",
        username=username
    )

@professor_bp.route("/courses/<int:course_id>/assignments/<int:assignment_id>")
@professor_required
def view_assignment(course_id, assignment_id):
    """View an assignment."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    professor = get_current_professor()
    # Verify that the professor owns this course
    if course.professor_id != professor.id:
        flash("You are not authorized to view assignments for this course.", "error")
        return redirect(url_for("professor.dashboard"))

    assignment = CourseService.get_assignment_by_id(assignment_id)
    if not assignment or assignment['course_id'] != course_id:
        from flask import render_template
        return render_template("error.html", message="Assignment not found", code=404), 404

    # Get submission stats for this assignment
    submission_count = CourseService.get_submission_count(assignment_id)

    username = session.get("username")
    return render_template(
        "professor/view_assignment.html",
        course=course,
        assignment=assignment,
        submission_count=submission_count,
        username=username
    )

@professor_bp.route("/courses/<int:course_id>/assignments/<int:assignment_id>/edit", methods=["GET", "POST"])
@professor_required
def edit_assignment(course_id, assignment_id):
    """Edit an existing assignment."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    professor = get_current_professor()
    # Verify that the professor owns this course
    if course.professor_id != professor.id:
        flash("You are not authorized to edit assignments for this course.", "error")
        return redirect(url_for("professor.dashboard"))

    assignment = CourseService.get_assignment_by_id(assignment_id)
    if not assignment or assignment['course_id'] != course_id:
        from flask import render_template
        return render_template("error.html", message="Assignment not found", code=404), 404

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date_str = request.form.get("due_date", "").strip()
        max_points_str = request.form.get("max_points", "100").strip()

        # Handle file upload (if new file provided)
        file_url = assignment['file_url']  # Keep existing file by default
        material_type = assignment['type']  # Keep existing type by default

        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Save file and get URL
                from werkzeug.utils import secure_filename
                import os
                from datetime import datetime

                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"

                # Create course-specific upload directory
                course_upload_dir = os.path.join(current_app.config['UPLOADS_DIR'], 'assignments', str(course_id))
                os.makedirs(course_upload_dir, exist_ok=True)

                file_path = os.path.join(course_upload_dir, filename)
                file.save(file_path)

                # Store relative path for serving
                file_url = f"assignments/{course_id}/{filename}"

                # Determine file type from extension
                if filename.lower().endswith('.pdf'):
                    material_type = 'pdf'
                elif filename.lower().endswith('.zip'):
                    material_type = 'zip'
                else:
                    material_type = 'other'

        # Validate inputs
        if not title:
            flash("Assignment title is required", "error")
            return render_template("professor/manage_assignment.html",
                                 course=course,
                                 assignment=assignment,
                                 mode="edit",
                                 username=session.get("username"))

        try:
            max_points = int(max_points_str)
            if max_points <= 0:
                raise ValueError("Max points must be positive")
        except (ValueError, TypeError):
            flash("Max points must be a positive number", "error")
            return render_template("professor/manage_assignment.html",
                                 course=course,
                                 assignment=assignment,
                                 mode="edit",
                                 username=session.get("username"))

        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Invalid due date format", "error")
                return render_template("professor/manage_assignment.html",
                                     course=course,
                                     assignment=assignment,
                                     mode="edit",
                                     username=session.get("username"))

        # Update assignment using service
        success = CourseService.update_assignment(
            assignment_id=assignment_id,
            title=title,
            file_url=file_url,
            material_type=material_type,
            due_date=due_date,
            max_points=max_points
        )

        if success:
            flash("Assignment updated successfully!", "success")
            return redirect(url_for("professor.view_assignment", course_id=course_id, assignment_id=assignment_id))
        else:
            flash("Failed to update assignment", "error")

    # GET request - show form with current assignment data
    username = session.get("username")
    return render_template(
        "professor/manage_assignment.html",
        course=course,
        assignment=assignment,
        mode="edit",
        username=username
    )

@professor_bp.route("/courses/<int:course_id>/assignments/<int:assignment_id>/delete", methods=["POST"])
@professor_required
def delete_assignment(course_id, assignment_id):
    """Delete an assignment."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    professor = get_current_professor()
    # Verify that the professor owns this course
    if course.professor_id != professor.id:
        flash("You are not authorized to delete assignments for this course.", "error")
        return redirect(url_for("professor.dashboard"))

    assignment = CourseService.get_assignment_by_id(assignment_id)
    if not assignment or assignment['course_id'] != course_id:
        from flask import render_template
        return render_template("error.html", message="Assignment not found", code=404), 404

    # Delete assignment using service
    if CourseService.delete_assignment(assignment_id):
        flash("Assignment deleted successfully.", "success")
    else:
        flash("Failed to delete assignment", "error")

    return redirect(url_for("professor.list_assignments", course_id=course_id))


@professor_bp.route("/courses/<int:course_id>/materials/upload", methods=["GET", "POST"])
@professor_required
def upload_material(course_id):
    """Upload a new course material."""
    course = CourseService.get_by_id(course_id)
    if not course:
        from flask import render_template
        return render_template("error.html", message="Course not found", code=404), 404

    professor = get_current_professor()
    # Verify that the professor owns this course
    if course.professor_id != professor.id:
        flash("You are not authorized to upload materials for this course.", "error")
        current_app.logger.warning(f'Unauthorized upload attempt by user {session.get("user_id")} for course {course_id}')
        return redirect(url_for("professor.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        material_type = request.form.get("material_type", "pdf").strip()

        # Handle file upload
        file_url = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Validate file extension
                allowed_extensions = {'pdf', 'zip', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt', 'ppt', 'pptx', 'xls', 'xlsx'}
                filename = secure_filename(file.filename)
                if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    flash("File type not allowed. Please upload a PDF, DOC, DOCX, JPG, PNG, TXT, PPT, XLS, or ZIP file.", "error")
                    current_app.logger.warning(f'Blocked file upload attempt: {filename} (user: {session.get("user_id")}, course: {course_id})')
                    return render_template("professor/upload_material.html",
                                         course=course,
                                         material_type=material_type,
                                         username=session.get("username"))

                # Add timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"

                # Save file and get URL
                from werkzeug.utils import secure_filename
                import os

                # Create course-specific upload directory
                course_upload_dir = os.path.join(current_app.config['UPLOADS_DIR'], 'materials', str(course_id))
                os.makedirs(course_upload_dir, exist_ok=True)

                file_path = os.path.join(course_upload_dir, filename)
                file.save(file_path)

                # Store relative path for serving
                file_url = f"materials/{course_id}/{filename}"

                # Validate inputs
                if not title:
                    flash("Material title is required", "error")
                    return render_template("professor/upload_material.html",
                                         course=course,
                                         material_type=material_type,
                                         username=session.get("username"))

                # Upload material using service
                material_id = CourseService.upload_course_material(
                    course_id=course_id,
                    professor_user_id=session["user_id"],
                    title=title,
                    file_url=file_url,
                    material_type=material_type
                )

                if material_id:
                    flash("Material uploaded successfully!", "success")
                    current_app.logger.info(f'Material uploaded: {title} (user: {session.get("user_id")}, course: {course_id})')
                    return redirect(url_for("professor.course_detail", course_id=course_id))
                else:
                    flash("Failed to upload material", "error")
                    current_app.logger.error(f'Failed to upload material: {title} (user: {session.get("user_id")}, course: {course_id})')

        else:
            flash("Please select a file to upload", "error")

    # GET request - show form
    username = session.get("username")
    return render_template(
        "professor/upload_material.html",
        course=course,
        username=username
    )
