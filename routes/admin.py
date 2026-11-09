
from functools import wraps
from datetime import date

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    abort
)

from flask_login import current_user, login_required
from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    SelectField,
    SelectMultipleField
)

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    request,
    current_app
)

from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo
)

from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash

from extensions import db

from models.user import User
from models.subject import Subject
from models.chapter import Chapter
from models.attendance import Attendance


# ==========================================
# ADMIN BLUEPRINT
# ==========================================

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ==========================================
# ADMIN ACCESS PROTECTION
# ==========================================

def admin_required(function):

    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):

        if current_user.role != "admin":
            abort(403)

        return function(*args, **kwargs)

    return wrapper


# ==========================================
# TEACHER FORM
# ==========================================

class TeacherForm(FlaskForm):

    name = StringField(
        "Teacher Name",
        validators=[
            DataRequired(),
            Length(min=3, max=100)
        ]
    )

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Temporary Password",
        validators=[
            DataRequired(),
            Length(min=12)
        ]
    )

    submit = SubmitField("Create Teacher Account")

    # ==========================================
# STUDENT CREATE FORM
# ==========================================

class StudentForm(FlaskForm):

    name = StringField(
        "Student Name",
        validators=[
            DataRequired(),
            Length(min=3, max=100)
        ]
    )

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    registration_number = StringField(
        "Registration Number",
        validators=[
            DataRequired(),
            Length(min=3, max=50)
        ]
    )

    password = PasswordField(
        "Temporary Password",
        validators=[
            DataRequired(),
            Length(min=8)
        ]
    )

    submit = SubmitField("Create Student")


# ==========================================
# STUDENT EDIT FORM
# ==========================================

class EditStudentForm(FlaskForm):

    name = StringField(
        "Student Name",
        validators=[
            DataRequired(),
            Length(min=3, max=100)
        ]
    )

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    registration_number = StringField(
        "Registration Number",
        validators=[
            DataRequired(),
            Length(min=3, max=50)
        ]
    )

    submit = SubmitField("Update Student")


# ==========================================
# SUBJECT FORM
# ==========================================

class SubjectForm(FlaskForm):

    name = StringField(
        "Subject Name",
        validators=[
            DataRequired(),
            Length(min=2, max=120)
        ]
    )

    code = StringField(
        "Subject Code",
        validators=[
            DataRequired(),
            Length(min=2, max=30)
        ]
    )

    description = TextAreaField("Description")

    submit = SubmitField("Add Subject")


# ==========================================
# CHAPTER FORM
# ==========================================

class ChapterForm(FlaskForm):

    title = StringField(
        "Chapter Title",
        validators=[
            DataRequired(),
            Length(min=2, max=150)
        ]
    )

    subject_id = SelectField(
        "Select Subject",
        coerce=int,
        validators=[DataRequired()]
    )

    description = TextAreaField(
        "Chapter Description"
    )

    submit = SubmitField("Add Chapter")


# ==========================================
# TEACHER SUBJECT ASSIGNMENT FORM
# ==========================================

class AssignSubjectForm(FlaskForm):

    teacher_id = SelectField(
        "Select Teacher",
        coerce=int,
        validators=[DataRequired()]
    )

    subject_ids = SelectMultipleField(
        "Select Subjects",
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField("Assign Subjects")


# ==========================================
# USER MANAGEMENT
# ==========================================

@admin_bp.route("/users")
@admin_required
def users():

    students = User.query.filter_by(
        role="student"
    ).order_by(User.created_at.desc()).all()

    teachers = User.query.filter_by(
        role="teacher"
    ).order_by(User.created_at.desc()).all()

    return render_template(
        "admin/users.html",
        students=students,
        teachers=teachers
    )

# ==========================================
# CREATE STUDENT
# ==========================================

@admin_bp.route(
    "/students/create",
    methods=["GET", "POST"]
)
@admin_required
def create_student():

    form = StudentForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()
        registration_number = (
            form.registration_number.data.strip()
        )

        existing_email = User.query.filter_by(
            email=email
        ).first()

        existing_registration = User.query.filter_by(
            registration_number=registration_number
        ).first()

        if existing_email:
            flash("This email is already registered.", "danger")

        elif existing_registration:
            flash(
                "This registration number is already registered.",
                "danger"
            )

        else:

            student = User(
                name=form.name.data.strip(),
                email=email,
                registration_number=registration_number,
                password_hash=generate_password_hash(
                    form.password.data
                ),
                role="student",
                is_active=True
            )

            db.session.add(student)
            db.session.commit()

            flash("Student created successfully!", "success")

            return redirect(url_for("admin.users"))

    return render_template(
        "admin/create_student.html",
        form=form
    )


# ==========================================
# EDIT STUDENT
# ==========================================

@admin_bp.route(
    "/students/<int:student_id>/edit",
    methods=["GET", "POST"]
)
@admin_required
def edit_student(student_id):

    student = User.query.filter_by(
        id=student_id,
        role="student"
    ).first_or_404()

    form = EditStudentForm(obj=student)

    if form.validate_on_submit():

        email = form.email.data.strip().lower()
        registration_number = (
            form.registration_number.data.strip()
        )

        duplicate_email = User.query.filter(
            User.email == email,
            User.id != student.id
        ).first()

        duplicate_registration = User.query.filter(
            User.registration_number == registration_number,
            User.id != student.id
        ).first()

        if duplicate_email:
            flash("This email is already in use.", "danger")

        elif duplicate_registration:
            flash(
                "This registration number is already in use.",
                "danger"
            )

        else:

            student.name = form.name.data.strip()
            student.email = email
            student.registration_number = registration_number

            db.session.commit()

            flash("Student information updated!", "success")

            return redirect(url_for("admin.users"))

    return render_template(
        "admin/edit_student.html",
        form=form,
        student=student
    )


# ==========================================
# ACTIVATE / DEACTIVATE STUDENT
# ==========================================

@admin_bp.route(
    "/students/<int:student_id>/status/<string:status>",
    methods=["POST"]
)
@admin_required
def change_student_status(student_id, status):

    student = User.query.filter_by(
        id=student_id,
        role="student"
    ).first_or_404()

    # CSRF protection
    form = FlaskForm()

    if not form.validate_on_submit():
        abort(400)

    if status == "deactivate":
        student.is_active = False
        message = "Student account deactivated."

    elif status == "activate":
        student.is_active = True
        message = "Student account activated."

    else:
        abort(400)

    db.session.commit()

    flash(message, "success")

    return redirect(url_for("admin.users"))

# ==========================================
# CREATE TEACHER
# ==========================================

@admin_bp.route(
    "/teachers/create",
    methods=["GET", "POST"]
)
@admin_required
def create_teacher():

    form = TeacherForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "This email is already registered.",
                "danger"
            )

        else:

            teacher = User(
                name=form.name.data.strip(),
                email=email,
                password_hash=generate_password_hash(
                    form.password.data
                ),
                role="teacher"
            )

            db.session.add(teacher)
            db.session.commit()

            flash(
                "Teacher account created successfully!",
                "success"
            )

            return redirect(url_for("admin.users"))

    return render_template(
        "admin/create_teacher.html",
        form=form
    )


# ==========================================
# VIEW ALL SUBJECTS
# ==========================================

@admin_bp.route("/subjects")
@admin_required
def subjects():

    all_subjects = Subject.query.order_by(
        Subject.name.asc()
    ).all()

    return render_template(
        "admin/subjects.html",
        subjects=all_subjects
    )


# ==========================================
# CREATE SUBJECT
# ==========================================

@admin_bp.route(
    "/subjects/create",
    methods=["GET", "POST"]
)
@admin_required
def create_subject():

    form = SubjectForm()

    if form.validate_on_submit():

        name = form.name.data.strip()
        code = form.code.data.strip().upper()

        existing_name = Subject.query.filter_by(
            name=name
        ).first()

        existing_code = Subject.query.filter_by(
            code=code
        ).first()

        if existing_name or existing_code:

            flash(
                "Subject name or code already exists.",
                "danger"
            )

        else:

            subject = Subject(
                name=name,
                code=code,
                description=(
                    form.description.data or ""
                ).strip(),
                created_by_id=current_user.id
            )

            db.session.add(subject)
            db.session.commit()

            flash(
                "Subject created successfully!",
                "success"
            )

            return redirect(url_for("admin.subjects"))

    return render_template(
        "admin/create_subject.html",
        form=form
    )


# ==========================================
# DELETE SUBJECT
# ==========================================

@admin_bp.route(
    "/subjects/<int:subject_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_subject(subject_id):

    subject = Subject.query.get_or_404(subject_id)

    # Related records check karo — data loss se bachne ke liye
    chapters_exist = Chapter.query.filter_by(
        subject_id=subject.id
    ).first()

    attendance_exist = Attendance.query.filter_by(
        subject_id=subject.id
    ).first()

    assignments_exist = bool(subject.assignments)
    students_exist = bool(subject.students)
    teachers_exist = bool(subject.teachers)

    if (
        chapters_exist
        or attendance_exist
        or assignments_exist
        or students_exist
        or teachers_exist
    ):
        flash(
            "Subject cannot be deleted because it has linked "
            "chapters, attendance, assignments, students or teachers. "
            "Remove or safely transfer linked records first.",
            "warning"
        )
        return redirect(url_for("admin.subjects"))

    try:
        subject_name = subject.name
        db.session.delete(subject)
        db.session.commit()

        flash(
            f"{subject_name} deleted successfully!",
            "success"
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Subject deletion failed.")
        flash("Subject could not be deleted.", "danger")

    return redirect(url_for("admin.subjects"))



# ==========================================
# CHAPTER MANAGEMENT
# ==========================================

@admin_bp.route("/chapters")
@admin_required
def chapters():

    all_chapters = Chapter.query.order_by(
        Chapter.created_at.desc()
    ).all()

    all_subjects = Subject.query.order_by(
        Subject.name.asc()
    ).all()

    return render_template(
        "admin/chapters.html",
        chapters=all_chapters,
        subjects=all_subjects
    )


# ==========================================
# CREATE CHAPTER
# ==========================================

@admin_bp.route(
    "/chapters/create",
    methods=["GET", "POST"]
)
@admin_required
def create_chapter():

    form = ChapterForm()

    all_subjects = Subject.query.order_by(
        Subject.name.asc()
    ).all()

    form.subject_id.choices = [
        (subject.id, subject.name)
        for subject in all_subjects
    ]

    if not all_subjects:

        flash(
            "Please create a subject first.",
            "warning"
        )

        return redirect(url_for("admin.subjects"))

    if form.validate_on_submit():

        chapter = Chapter(
            title=form.title.data.strip(),
            description=(
                form.description.data or ""
            ).strip(),
            subject_id=form.subject_id.data,
            created_by_id=current_user.id
        )

        db.session.add(chapter)
        db.session.commit()

        flash(
            "Chapter created successfully!",
            "success"
        )

        return redirect(url_for("admin.chapters"))

    return render_template(
        "admin/create_chapter.html",
        form=form
    )


# ==========================================
# TEACHER SUBJECT ASSIGNMENT
# ==========================================

@admin_bp.route(
    "/teachers/assign-subjects",
    methods=["GET", "POST"]
)
@admin_required
def assign_subjects():

    form = AssignSubjectForm()

    teachers = User.query.filter_by(
        role="teacher"
    ).order_by(User.name.asc()).all()

    subjects_list = Subject.query.order_by(
        Subject.name.asc()
    ).all()

    form.teacher_id.choices = [
        (teacher.id, teacher.name)
        for teacher in teachers
    ]

    form.subject_ids.choices = [
        (subject.id, subject.name)
        for subject in subjects_list
    ]

    if not teachers:
        flash("Please create a teacher account first.", "warning")
        return redirect(url_for("admin.users"))

    if not subjects_list:
        flash("Please create a subject first.", "warning")
        return redirect(url_for("admin.subjects"))

    if form.validate_on_submit():

        teacher = db.session.get(
            User,
            form.teacher_id.data
        )

        if not teacher or teacher.role != "teacher":
            abort(400)

        selected_subjects = Subject.query.filter(
            Subject.id.in_(form.subject_ids.data)
        ).all()

        existing_subject_ids = {
            subject.id
            for subject in teacher.assigned_subjects
        }

        new_subjects = [
            subject
            for subject in selected_subjects
            if subject.id not in existing_subject_ids
        ]

        teacher.assigned_subjects.extend(new_subjects)

        db.session.commit()

        flash(
            f"{len(new_subjects)} new subject(s) assigned successfully!",
            "success"
        )

        return redirect(
            url_for(
                "admin.assign_subjects",
                teacher_id=teacher.id
            )
        )

    # Selected teacher on GET
    selected_teacher_id = request.args.get(
        "teacher_id",
        type=int
    )

    selected_teacher = None

    if selected_teacher_id:
        selected_teacher = User.query.filter_by(
            id=selected_teacher_id,
            role="teacher"
        ).first()

    if selected_teacher:
        form.teacher_id.data = selected_teacher.id

    assigned_subjects = (
        selected_teacher.assigned_subjects
        if selected_teacher else []
    )

    return render_template(
        "admin/assign_subjects.html",
        form=form,
        teachers=teachers,
        selected_teacher=selected_teacher,
        assigned_subjects=assigned_subjects
    )


# ==========================================
# REMOVE SUBJECT FROM TEACHER
# ==========================================

@admin_bp.route(
    "/teachers/<int:teacher_id>/subjects/<int:subject_id>/remove",
    methods=["POST"]
)
@admin_required
def remove_teacher_subject(teacher_id, subject_id):

    teacher = User.query.filter_by(
        id=teacher_id,
        role="teacher"
    ).first_or_404()

    subject = Subject.query.get_or_404(subject_id)

    if subject not in teacher.assigned_subjects:
        flash(
            "This subject is not assigned to this teacher.",
            "warning"
        )
        return redirect(
            url_for(
                "admin.assign_subjects",
                teacher_id=teacher.id
            )
        )

    teacher.assigned_subjects.remove(subject)
    db.session.commit()

    flash(
        f"{subject.name} removed from {teacher.name} successfully.",
        "success"
    )

    return redirect(
        url_for(
            "admin.assign_subjects",
            teacher_id=teacher.id
        )
    )
# ==========================================
# ADMIN ATTENDANCE SUBJECT LIST
# ==========================================

@admin_bp.route("/attendance")
@admin_required
def attendance():

    all_subjects = Subject.query.order_by(
        Subject.name.asc()
    ).all()

    return render_template(
        "admin/attendance_subjects.html",
        subjects=all_subjects
    )


# ==========================================
# ADMIN SUBJECT-WISE ATTENDANCE MANAGEMENT
# ==========================================

@admin_bp.route(
    "/attendance/<int:subject_id>",
    methods=["GET", "POST"]
)
@admin_required
def subject_attendance(subject_id):

    subject = Subject.query.filter_by(
        id=subject_id
    ).first_or_404()

    students = (
        User.query
        .join(Subject.students)
        .filter(
            Subject.id == subject.id,
            User.role == "student"
        )
        .order_by(User.name.asc())
        .all()
    )

    if request.method == "POST":
        attendance_date_str = request.form.get(
            "attendance_date"
        )
    else:
        attendance_date_str = request.args.get(
            "attendance_date",
            date.today().isoformat()
        )

    try:
        selected_date = date.fromisoformat(
            attendance_date_str
        )
    except (ValueError, TypeError):
        flash("Please select a valid attendance date.", "danger")
        return redirect(
            url_for(
                "admin.subject_attendance",
                subject_id=subject.id
            )
        )

    # Load attendance regardless of whether Admin or Teacher marked it
    existing_records = Attendance.query.filter_by(
        subject_id=subject.id,
        attendance_date=selected_date
    ).all()

    attendance_records = {
        record.student_id: record
        for record in existing_records
    }

    # Save or update attendance
    if request.method == "POST":

        for student in students:

            status = request.form.get(
                f"status_{student.id}"
            )

            if status not in ["Present", "Absent", "Late"]:
                flash(
                    f"Invalid attendance status for {student.name}.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin.subject_attendance",
                        subject_id=subject.id,
                        attendance_date=selected_date.isoformat()
                    )
                )

            remarks = request.form.get(
                f"remarks_{student.id}",
                ""
            ).strip() or None

            record = attendance_records.get(student.id)

            if record:
                record.status = status
                record.remarks = remarks
                # Existing teacher_id is preserved.
            else:
                record = Attendance(
                    student_id=student.id,
                    teacher_id=current_user.id,
                    subject_id=subject.id,
                    attendance_date=selected_date,
                    status=status,
                    remarks=remarks
                )
                db.session.add(record)

        try:
            db.session.commit()
            flash("Attendance saved successfully!", "success")

        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Admin failed to save attendance."
            )
            flash(
                "Could not save attendance. Please try again.",
                "danger"
            )

        return redirect(
            url_for(
                "admin.subject_attendance",
                subject_id=subject.id,
                attendance_date=selected_date.isoformat()
            )
        )

    return render_template(
        "admin/attendance.html",
        subject=subject,
        students=students,
        attendance_records=attendance_records,
        selected_date=selected_date.isoformat()
    )


# ==========================================
# ADMIN SUBJECT-WISE ATTENDANCE HISTORY
# ==========================================

@admin_bp.route(
    "/attendance/<int:subject_id>/history"
)
@admin_required
def attendance_history(subject_id):

    subject = Subject.query.filter_by(
        id=subject_id
    ).first_or_404()

    records = (
        Attendance.query
        .filter_by(subject_id=subject.id)
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.created_at.desc()
        )
        .all()
    )

    return render_template(
        "admin/attendance_history.html",
        subject=subject,
        records=records
    )