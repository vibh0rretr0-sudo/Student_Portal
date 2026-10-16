from ..models import db, Course, Professor, User, Enrollment, Announcement, CourseMaterial, Student


class CourseService:
    @staticmethod
    def get_by_id(course_id):
        """Get a course by its ID."""
        course = Course.query.get(course_id)
        if not course:
            return None

        # Get professor info if available
        professor_name = None
        professor_email = None
        professor_id = None

        if course.professor:
            professor_name = course.professor.user.full_name
            professor_email = course.professor.user.email
            professor_id = course.professor.employee_id

        return {
            'id': course.id,
            'code': course.code,
            'name': course.name,
            'description': course.description,
            'credits': course.credits,
            'professor_id': course.professor_id,
            'semester': course.semester,
            'schedule': course.schedule,
            'room': course.room,
            'professor_name': professor_name,
            'professor_email': professor_email,
            'professor_id': professor_id
        }

    @staticmethod
    def get_for_professor(professor_user_id):
        """Get all courses for a professor by user ID."""
        # Join to get professor record from user
        professor = Professor.query.join(User).filter(User.id == professor_user_id).first()
        if not professor:
            return []

        courses = Course.query.filter_by(professor_id=professor.id).all()
        result = []

        for course in courses:
            # Get enrollment count
            enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()

            course_dict = {
                'id': course.id,
                'code': course.code,
                'name': course.name,
                'description': course.description,
                'credits': course.credits,
                'professor_id': course.professor_id,
                'semester': course.semester,
                'schedule': course.schedule,
                'room': course.room,
                'professor_name': professor.user.full_name,
                'professor_email': professor.user.email,
                'professor_id': professor.employee_id,
                'enrollment_count': enrollment_count
            }
            result.append(course_dict)

        return result

    @staticmethod
    def get_professor_dashboard_stats(professor_user_id):
        """Get statistics for professor dashboard."""
        professor = Professor.query.join(User).filter(User.id == professor_user_id).first()
        if not professor:
            return {}

        # Get courses taught by this professor
        courses = Course.query.filter_by(professor_id=professor.id).all()
        total_courses = len(courses)

        if total_courses == 0:
            return {
                'total_courses': 0,
                'total_students': 0,
                'avg_students_per_course': 0,
                'current_semester_courses': 0
            }

        # Get total students across all courses
        total_students = 0
        current_semester_courses = 0

        for course in courses:
            # Count students in this course
            course_students = Enrollment.query.filter_by(course_id=course.id).count()
            total_students += course_students

            # Count current semester courses
            if course.semester == getattr(professor, 'current_semester', 'Fall 2026'):  # Default if not set
                current_semester_courses += 1

        # Calculate average students per course
        avg_students_per_course = round(total_students / total_courses, 1) if total_courses > 0 else 0

        return {
            'total_courses': total_courses,
            'total_students': total_students,
            'avg_students_per_course': avg_students_per_course,
            'current_semester_courses': current_semester_courses
        }

    @staticmethod
    def create(code, name, description, credits, professor_user_id, semester, schedule, room):
        """Create a new course."""
        # Get professor record from user ID
        professor = Professor.query.join(User).filter(User.id == professor_user_id).first()
        if not professor:
            return None

        course = Course(
            code=code,
            name=name,
            description=description,
            credits=credits,
            professor_id=professor.id,
            semester=semester,
            schedule=schedule,
            room=room
        )

        db.session.add(course)
        db.session.commit()
        return course.id

    @staticmethod
    def update(course_id, name, description, credits, semester, schedule, room):
        """Update an existing course."""
        course = Course.query.get(course_id)
        if not course:
            return False

        course.name = name
        course.description = description
        course.credits = credits
        course.semester = semester
        course.schedule = schedule
        course.room = room

        db.session.commit()
        return True

    @staticmethod
    def delete(course_id):
        """Delete a course."""
        course = Course.query.get(course_id)
        if not course:
            return False

        db.session.delete(course)
        db.session.commit()
        return True

    @staticmethod
    def get_announcements(course_id):
        """Get all announcements for a course."""
        announcements = Announcement.query.filter_by(course_id=course_id)\
            .join(Professor)\
            .join(User, Professor.user)\
            .order_by(Announcement.created_at.desc())\
            .all()

        result = []
        for announcement in announcements:
            result.append({
                'id': announcement.id,
                'course_id': announcement.course_id,
                'professor_id': announcement.professor_id,
                'title': announcement.title,
                'content': announcement.content,
                'created_at': announcement.created_at,
                'professor_name': announcement.professor.user.full_name
            })

        return result

    @staticmethod
    def get_materials(course_id):
        """Get all course materials for a course."""
        materials = CourseMaterial.query.filter_by(course_id=course_id)\
            .order_by(CourseMaterial.uploaded_at.desc())\
            .all()

        result = []
        for material in materials:
            result.append({
                'id': material.id,
                'course_id': material.course_id,
                'title': material.title,
                'file_url': material.file_url,
                'type': material.material_type,
                'uploaded_at': material.uploaded_at
            })

        return result

    @staticmethod
    def add_announcement(course_id, professor_user_id, title, content):
        """Add a new announcement to a course."""
        # Get professor record from user ID
        professor = Professor.query.join(User).filter(User.id == professor_user_id).first()
        if not professor:
            return False

        announcement = Announcement(
            course_id=course_id,
            professor_id=professor.id,
            title=title,
            content=content
        )

        db.session.add(announcement)
        db.session.commit()
        return True

    @staticmethod
    def create_assignment(course_id, professor_user_id, title, file_url, material_type, due_date, max_points):
        """Create a new assignment for a course."""
        # Get professor record from user ID
        professor = Professor.query.join(User).filter(User.id == professor_user_id).first()
        if not professor:
            return None

        assignment = CourseMaterial(
            course_id=course_id,
            title=title,
            file_url=file_url,
            material_type=material_type,
            is_assignment=True,
            due_date=due_date,
            max_points=max_points
        )

        db.session.add(assignment)
        db.session.commit()
        return assignment.id

    @staticmethod
    def upload_course_material(course_id, professor_user_id, title, file_url, material_type):
        """Upload a new course material (non-assignment) for a course."""
        # Get professor record from user ID
        professor = Professor.query.join(User).filter(User.id == professor_user_id).first()
        if not professor:
            return None

        material = CourseMaterial(
            course_id=course_id,
            title=title,
            file_url=file_url,
            material_type=material_type,
            is_assignment=False
        )

        db.session.add(material)
        db.session.commit()
        return material.id

    @staticmethod
    def get_assignments_for_course(course_id):
        """Get all assignments for a course."""
        assignments = CourseMaterial.query.filter_by(
            course_id=course_id,
            is_assignment=True
        ).order_by(CourseMaterial.uploaded_at.desc()).all()

        result = []
        for assignment in assignments:
            result.append({
                'id': assignment.id,
                'course_id': assignment.course_id,
                'title': assignment.title,
                'file_url': assignment.file_url,
                'type': assignment.material_type,
                'uploaded_at': assignment.uploaded_at,
                'due_date': assignment.due_date,
                'max_points': assignment.max_points
            })

        return result

    @staticmethod
    def get_assignment_by_id(assignment_id):
        """Get an assignment by its ID."""
        assignment = CourseMaterial.query.filter_by(
            id=assignment_id,
            is_assignment=True
        ).first()

        if not assignment:
            return None

        return {
            'id': assignment.id,
            'course_id': assignment.course_id,
            'title': assignment.title,
            'file_url': assignment.file_url,
            'type': assignment.material_type,
            'uploaded_at': assignment.uploaded_at,
            'due_date': assignment.due_date,
            'max_points': assignment.max_points
        }

    @staticmethod
    def update_assignment(assignment_id, title, file_url, material_type, due_date, max_points):
        """Update an existing assignment."""
        assignment = CourseMaterial.query.filter_by(
            id=assignment_id,
            is_assignment=True
        ).first()
        if not assignment:
            return False

        assignment.title = title
        assignment.file_url = file_url
        assignment.material_type = material_type
        assignment.due_date = due_date
        assignment.max_points = max_points

        db.session.commit()
        return True

    @staticmethod
    def delete_assignment(assignment_id):
        """Delete an assignment."""
        assignment = CourseMaterial.query.filter_by(
            id=assignment_id,
            is_assignment=True
        ).first()
        if not assignment:
            return False

        db.session.delete(assignment)
        db.session.commit()
        return True

    @staticmethod
    def get_submission_count(assignment_id):
        """Get the number of submissions for an assignment."""
        from ..models import Submission
        return Submission.query.filter_by(assignment_id=assignment_id).count()


class CourseEnrollmentService:
    @staticmethod
    def get_for_course(course_id):
        """Get all enrollments for a course with student info."""
        enrollments = Enrollment.query.filter_by(course_id=course_id)\
            .join(Student)\
            .order_by(Student.user_id)\
            .all()

        result = []
        for enrollment in enrollments:
            student = enrollment.student
            user = student.user
            result.append({
                'id': enrollment.id,
                'student_id': student.student_id,
                'student_number': student.student_id,  # Keeping the field name for backward compatibility
                'major': student.major,
                'current_semester': student.current_semester,
                'full_name': user.full_name,
                'email': user.email,
                'grade': enrollment.grade,
                'attendance': enrollment.attendance
            })

        return result