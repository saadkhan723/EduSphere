
import os
import uuid
from pathlib import Path
from datetime import datetime, date

from flask import (
    Blueprint, render_template, abort, redirect,
    url_for, flash, request, current_app, send_from_directory
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField,
    SubmitField, FileField, FloatField
)
from wtforms.validators import DataRequired, Optional, NumberRange
from werkzeug.utils import secure_filename

from extensions import db

from models.user import User
from models.subject import Subject
from models.chapter import Chapter
from models.assignment import Assignment
from models.assignment_submission import AssignmentSubmission
from models.quiz import Quiz
from models.quiz_attempt import QuizAttempt
from models.question_bank import QuestionBank
from models.attendance import Attendance
from io import BytesIO
from flask import send_file
from googleapiclient.http import MediaIoBaseDownload

from services.google_drive_service import (
    get_drive_service,
    get_chapters_folder_id,
    upload_file_to_drive,
    delete_drive_file
)


teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

TEACHER_ATTACHMENT_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx"}
CHAPTER_ALLOWED_EXTENSIONS = {"pdf", "pptx"}
CHAPTER_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


# ==========================================
# TEACHER AUTHORIZATION
# ==========================================

def teacher_required():
    if current_user.role != "teacher":
        abort(403)


# ==========================================
# ASSIGNMENT HELPERS
# ==========================================

def assignment_folder():
    folder = Path(current_app.root_path) / "uploads" / "assignments"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def allowed_file(filename, extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in extensions
    )


# ==========================================
# ASSIGNMENT FORMS
# ==========================================

class AssignmentForm(FlaskForm):
    title = StringField("Assignment Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    instructions = TextAreaField("Instructions", validators=[Optional()])
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    chapter_id = SelectField("Chapter", coerce=int, validators=[Optional()])
    due_date = StringField("Due Date", validators=[DataRequired()])
    attachment = FileField("Attachment (PDF, Word or PowerPoint)")
    submit = SubmitField("Create Assignment")


class GradeForm(FlaskForm):
    marks = FloatField(
        "Marks",
        validators=[DataRequired(), NumberRange(min=0)]
    )
    feedback = TextAreaField("Feedback", validators=[Optional()])
    submit = SubmitField("Save Grade")


# ==========================================
# TEACHER SUBJECTS
# ==========================================

@teacher_bp.route("/subjects")
@login_required
def subjects():
    teacher_required()

    return render_template(
        "teacher/subjects.html",
        subjects=current_user.assigned_subjects
    )



# ==========================================
# TEACHER CHAPTERS
# ==========================================

@teacher_bp.route("/chapters")
@login_required
def chapters():
    teacher_required()

    return render_template(
        "teacher/chapters.html",
        subjects=current_user.assigned_subjects
    )


# ==========================================
# VIEW INDIVIDUAL CHAPTER
# ==========================================

@teacher_bp.route("/chapters/<int:chapter_id>")
@login_required
def view_chapter(chapter_id):
    teacher_required()

    # Teacher can only access chapters of assigned subjects
    chapter = (
        Chapter.query
        .join(Subject)
        .filter(
            Chapter.id == chapter_id,
            Subject.teachers.any(id=current_user.id)
        )
        .first_or_404()
    )

    return render_template(
        "teacher/chapter_detail.html",
        chapter=chapter
    )



# ==========================================
# UPLOAD CHAPTER FILE TO GOOGLE DRIVE
# ==========================================

@teacher_bp.route(
    "/chapters/<int:chapter_id>/upload",
    methods=["POST"]
)
@login_required
def upload_chapter_file(chapter_id):
    teacher_required()

    chapter = (
        Chapter.query
        .join(Subject)
        .filter(
            Chapter.id == chapter_id,
            Subject.teachers.any(id=current_user.id)
        )
        .first_or_404()
    )

    if chapter.drive_file_id:
        flash(
            "A file already exists. Delete it before uploading another.",
            "warning"
        )
        return redirect(
            url_for("teacher.view_chapter", chapter_id=chapter.id)
        )

    uploaded_file = request.files.get("chapter_file")

    if not uploaded_file or not uploaded_file.filename:
        flash("Please select a file.", "danger")
        return redirect(
            url_for("teacher.view_chapter", chapter_id=chapter.id)
        )

    original_filename = secure_filename(uploaded_file.filename)

    if not original_filename or "." not in original_filename:
        flash("Invalid filename.", "danger")
        return redirect(
            url_for("teacher.view_chapter", chapter_id=chapter.id)
        )

    extension = original_filename.rsplit(".", 1)[1].lower()

    if extension not in CHAPTER_ALLOWED_EXTENSIONS:
        flash("Only PDF and PPTX files are allowed.", "danger")
        return redirect(
            url_for("teacher.view_chapter", chapter_id=chapter.id)
        )

    uploaded_file.stream.seek(0, os.SEEK_END)
    file_size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)

    if file_size == 0 or file_size > CHAPTER_MAX_FILE_SIZE:
        flash("File must be greater than 0 and no larger than 20 MB.", "danger")
        return redirect(
            url_for("teacher.view_chapter", chapter_id=chapter.id)
        )

    mime_types = {
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    }

    stored_filename = f"{uuid.uuid4().hex}.{extension}"
    uploaded_drive_file_id = None

    try:
        service = get_drive_service()

        if service is None:
            raise RuntimeError("Google Drive is not connected.")

        folder_id = get_chapters_folder_id(service)

        result = upload_file_to_drive(
            uploaded_file,
            stored_filename,
            mime_types[extension],
            folder_id=folder_id
        )

        uploaded_drive_file_id = result["id"]

        chapter.drive_file_id = result["id"]
        chapter.drive_filename = result["name"]
        chapter.drive_original_filename = original_filename
        chapter.drive_mime_type = mime_types[extension]

        db.session.commit()

        flash("Chapter file uploaded successfully!", "success")

    except Exception:
        db.session.rollback()

        if uploaded_drive_file_id:
            try:
                delete_drive_file(uploaded_drive_file_id)
            except Exception:
                current_app.logger.exception(
                    "Could not clean up uploaded chapter file."
                )

        current_app.logger.exception("Chapter upload failed.")
        flash("Chapter upload failed. Please try again.", "danger")

    return redirect(
        url_for("teacher.view_chapter", chapter_id=chapter.id)
    )


# ==========================================
# DOWNLOAD CHAPTER FILE
# ==========================================

@teacher_bp.route(
    "/chapters/<int:chapter_id>/download"
)
@login_required
def download_chapter_file(chapter_id):
    teacher_required()

    chapter = (
        Chapter.query
        .join(Subject)
        .filter(
            Chapter.id == chapter_id,
            Subject.teachers.any(id=current_user.id)
        )
        .first_or_404()
    )

    if not chapter.drive_file_id:
        abort(404)

    try:
        service = get_drive_service()

        if service is None:
            raise RuntimeError("Google Drive is not connected.")

        request_file = service.files().get_media(
            fileId=chapter.drive_file_id
        )

        file_buffer = BytesIO()
        downloader = MediaIoBaseDownload(
            file_buffer,
            request_file
        )

        done = False

        while not done:
            _, done = downloader.next_chunk()

        file_buffer.seek(0)

        return send_file(
            file_buffer,
            as_attachment=True,
            download_name=(
                chapter.drive_original_filename
                or chapter.drive_filename
            ),
            mimetype=(
                chapter.drive_mime_type
                or "application/octet-stream"
            )
        )

    except Exception:
        current_app.logger.exception("Chapter download failed.")
        flash("Could not download chapter file.", "danger")

        return redirect(
            url_for("teacher.view_chapter", chapter_id=chapter.id)
        )


# ==========================================
# DELETE CHAPTER FILE
# ==========================================

@teacher_bp.route(
    "/chapters/<int:chapter_id>/delete",
    methods=["POST"]
)
@login_required
def delete_chapter_file(chapter_id):
    teacher_required()

    chapter = (
        Chapter.query
        .join(Subject)
        .filter(
            Chapter.id == chapter_id,
            Subject.teachers.any(id=current_user.id)
        )
        .first_or_404()
    )

    if not chapter.drive_file_id:
        flash("No uploaded file exists.", "warning")
        return redirect(
            url_for("teacher.view_chapter", chapter_id=chapter.id)
        )

    try:
        delete_drive_file(chapter.drive_file_id)

        chapter.drive_file_id = None
        chapter.drive_filename = None
        chapter.drive_original_filename = None
        chapter.drive_mime_type = None

        db.session.commit()

        flash("Chapter file deleted successfully.", "success")

    except Exception:
        db.session.rollback()

        current_app.logger.exception("Chapter file deletion failed.")
        flash("Could not delete chapter file.", "danger")

    return redirect(
        url_for("teacher.view_chapter", chapter_id=chapter.id)
    )


# ==========================================
# ASSIGNMENT LIST
# ==========================================

@teacher_bp.route("/assignments")
@login_required
def assignments():
    teacher_required()

    items = Assignment.query.filter_by(
        teacher_id=current_user.id
    ).order_by(Assignment.created_at.desc()).all()

    return render_template(
        "teacher/assignments.html",
        assignments=items
    )


# ==========================================
# CREATE ASSIGNMENT
# ==========================================

@teacher_bp.route("/assignments/create", methods=["GET", "POST"])
@login_required
def create_assignment():
    teacher_required()

    form = AssignmentForm()

    teacher_subjects = current_user.assigned_subjects

    form.subject_id.choices = [
        (subject.id, subject.name)
        for subject in teacher_subjects
    ]

    form.chapter_id.choices = [(0, "No chapter")]

    if form.subject_id.data:
        chapters = Chapter.query.filter_by(
            subject_id=form.subject_id.data
        ).all()

        form.chapter_id.choices += [
            (chapter.id, chapter.title)
            for chapter in chapters
        ]

    if form.validate_on_submit():

        subject = Subject.query.filter(
            Subject.id == form.subject_id.data,
            Subject.teachers.any(id=current_user.id)
        ).first()

        if not subject:
            abort(403)

        chapter_id = form.chapter_id.data or None

        if chapter_id:
            chapter = Chapter.query.filter_by(
                id=chapter_id,
                subject_id=subject.id
            ).first()

            if not chapter:
                abort(400)

        try:
            due_date = datetime.fromisoformat(form.due_date.data)

        except (ValueError, TypeError):
            flash("Please enter a valid due date.", "danger")

            return render_template(
                "teacher/create_assignment.html",
                form=form
            )

        if due_date <= datetime.now():
            flash("Due date must be in the future.", "danger")

            return render_template(
                "teacher/create_assignment.html",
                form=form
            )

        uploaded_file = form.attachment.data

        stored_filename = None
        original_filename = None

        if uploaded_file and uploaded_file.filename:

            if not allowed_file(
                uploaded_file.filename,
                TEACHER_ATTACHMENT_EXTENSIONS
            ):
                flash(
                    "Allowed attachments: PDF, DOC, DOCX, PPT, PPTX.",
                    "danger"
                )

                return render_template(
                    "teacher/create_assignment.html",
                    form=form
                )

            original_filename = secure_filename(
                uploaded_file.filename
            )

            extension = original_filename.rsplit(".", 1)[1].lower()

            stored_filename = f"{uuid.uuid4().hex}.{extension}"

            uploaded_file.save(
                assignment_folder() / stored_filename
            )

        assignment = Assignment(
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            instructions=form.instructions.data,
            subject_id=subject.id,
            chapter_id=chapter_id,
            teacher_id=current_user.id,
            due_date=due_date,
            attachment_filename=stored_filename,
            attachment_original_name=original_filename
        )

        db.session.add(assignment)
        db.session.commit()

        flash("Assignment created successfully.", "success")

        return redirect(url_for("teacher.assignments"))

    return render_template(
        "teacher/create_assignment.html",
        form=form
    )


# ==========================================
# VIEW SUBMISSIONS
# ==========================================

@teacher_bp.route("/assignments/<int:assignment_id>/submissions")
@login_required
def assignment_submissions(assignment_id):
    teacher_required()

    assignment = Assignment.query.filter_by(
        id=assignment_id,
        teacher_id=current_user.id
    ).first_or_404()

    submissions = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id
    ).order_by(
        AssignmentSubmission.submitted_at.desc()
    ).all()

    return render_template(
        "teacher/assignment_submissions.html",
        assignment=assignment,
        submissions=submissions
    )


# ==========================================
# GRADE SUBMISSION
# ==========================================

@teacher_bp.route(
    "/submissions/<int:submission_id>/grade",
    methods=["GET", "POST"]
)
@login_required
def grade_submission(submission_id):
    teacher_required()

    submission = AssignmentSubmission.query.join(
        Assignment
    ).filter(
        AssignmentSubmission.id == submission_id,
        Assignment.teacher_id == current_user.id
    ).first_or_404()

    form = GradeForm()

    if form.validate_on_submit():

        if form.marks.data < 0:
            abort(400)

        submission.marks = form.marks.data
        submission.feedback = form.feedback.data
        submission.status = "Graded"
        submission.graded_at = datetime.utcnow()

        db.session.commit()

        flash("Grade and feedback saved.", "success")

        return redirect(
            url_for(
                "teacher.assignment_submissions",
                assignment_id=submission.assignment_id
            )
        )

    if request.method == "GET":
        form.marks.data = submission.marks
        form.feedback.data = submission.feedback

    return render_template(
        "teacher/grade_submission.html",
        form=form,
        submission=submission
    )


# ==========================================
# DOWNLOAD TEACHER ATTACHMENT
# ==========================================

@teacher_bp.route("/assignments/<int:assignment_id>/attachment")
@login_required
def download_assignment_attachment(assignment_id):
    teacher_required()

    assignment = Assignment.query.filter_by(
        id=assignment_id,
        teacher_id=current_user.id
    ).first_or_404()

    if not assignment.attachment_filename:
        abort(404)

    return send_from_directory(
        assignment_folder(),
        assignment.attachment_filename,
        as_attachment=True,
        download_name=assignment.attachment_original_name
    )


# ==========================================
# DOWNLOAD STUDENT SUBMISSION
# ==========================================

@teacher_bp.route("/submissions/<int:submission_id>/download")
@login_required
def download_submission(submission_id):
    teacher_required()

    submission = AssignmentSubmission.query.join(
        Assignment
    ).filter(
        AssignmentSubmission.id == submission_id,
        Assignment.teacher_id == current_user.id
    ).first_or_404()

    return send_from_directory(
        assignment_folder(),
        submission.submission_filename,
        as_attachment=True,
        download_name=submission.submission_original_name
    )


# ==========================================
# TEACHER QUIZ RESULTS
# ==========================================

@teacher_bp.route("/quiz-results")
@login_required
def quiz_results():
    teacher_required()

    results = (
        QuizAttempt.query
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            Quiz.teacher_id == current_user.id,
            QuizAttempt.submitted_at.isnot(None)
        )
        .order_by(QuizAttempt.submitted_at.desc())
        .all()
    )

    return render_template(
        "teacher/quiz_results.html",
        results=results
    )


# ==========================================
# INDIVIDUAL STUDENT QUIZ RESULT DETAILS
# ==========================================

@teacher_bp.route("/quiz-results/<int:attempt_id>")
@login_required
def quiz_result_detail(attempt_id):
    teacher_required()

    attempt = (
        QuizAttempt.query
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            QuizAttempt.id == attempt_id,
            Quiz.teacher_id == current_user.id,
            QuizAttempt.status == "submitted"
        )
        .first_or_404()
    )

    questions_by_id = {
        question.id: question
        for question in QuestionBank.query.filter(
            QuestionBank.id.in_(attempt.selected_question_ids)
        ).all()
    }

    result_items = []
    answers = attempt.answers or {}
    option_orders = attempt.option_orders or {}

    for number, question_id in enumerate(
        attempt.selected_question_ids,
        start=1
    ):

        question = questions_by_id.get(question_id)

        if question is None:
            continue

        selected_answer = answers.get(str(question_id), "")
        correct_answer = question.correct_answer

        order = option_orders.get(str(question_id), [])

        if not order:
            order = list((question.options or {}).keys())

        options = []

        for option_key in order:
            if option_key in (question.options or {}):
                options.append({
                    "key": option_key,
                    "text": question.options[option_key]
                })

        result_items.append({
            "number": number,
            "question": question.question_text,
            "options": options,
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "is_correct": (
                selected_answer == correct_answer
                and bool(selected_answer)
            ),
            "explanation": question.explanation
        })

    percentage = (
        (attempt.score / attempt.total_questions) * 100
        if attempt.total_questions else 0
    )

    correct_count = sum(
        1 for item in result_items
        if item["is_correct"]
    )

    return render_template(
        "teacher/quiz_result_detail.html",
        attempt=attempt,
        result_items=result_items,
        percentage=percentage,
        correct_count=correct_count,
        incorrect_count=len(result_items) - correct_count
    )


# ==========================================
# TEACHER ATTENDANCE SUBJECT LIST
# ==========================================

@teacher_bp.route("/attendance")
@login_required
def attendance():
    teacher_required()

    teacher_subjects = current_user.assigned_subjects

    return render_template(
        "teacher/attendance_subjects.html",
        subjects=teacher_subjects
    )


# ==========================================
# SUBJECT-WISE ATTENDANCE MANAGEMENT
# ==========================================

@teacher_bp.route(
    "/attendance/<int:subject_id>",
    methods=["GET", "POST"]
)
@login_required
def subject_attendance(subject_id):
    teacher_required()

    # Verify that this subject belongs to the current teacher
    subject = Subject.query.filter(
        Subject.id == subject_id,
        Subject.teachers.any(id=current_user.id)
    ).first_or_404()

    # Get only students enrolled in this subject
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
        attendance_date_str = request.form.get("attendance_date")
    else:
        attendance_date_str = request.args.get(
            "attendance_date",
            date.today().isoformat()
        )

    try:
        selected_date = date.fromisoformat(attendance_date_str)
    except (ValueError, TypeError):
        flash("Please select a valid attendance date.", "danger")
        return redirect(
            url_for(
                "teacher.subject_attendance",
                subject_id=subject.id
            )
        )

    # Load existing attendance for this subject and date
    existing_records = Attendance.query.filter_by(
        subject_id=subject.id,
        teacher_id=current_user.id,
        attendance_date=selected_date
    ).all()

    attendance_records = {
        record.student_id: record
        for record in existing_records
    }

    # Save attendance
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
                        "teacher.subject_attendance",
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
                "Failed to save attendance."
            )

            flash(
                "Could not save attendance. Please try again.",
                "danger"
            )

        return redirect(
            url_for(
                "teacher.subject_attendance",
                subject_id=subject.id,
                attendance_date=selected_date.isoformat()
            )
        )

    return render_template(
        "teacher/attendance.html",
        subject=subject,
        students=students,
        attendance_records=attendance_records,
        selected_date=selected_date.isoformat()
    )


# ==========================================
# SUBJECT-WISE ATTENDANCE HISTORY
# ==========================================

@teacher_bp.route(
    "/attendance/<int:subject_id>/history"
)
@login_required
def attendance_history(subject_id):
    teacher_required()

    # Verify subject ownership
    subject = Subject.query.filter(
        Subject.id == subject_id,
        Subject.teachers.any(id=current_user.id)
    ).first_or_404()

    records = (
        Attendance.query
        .filter_by(
            subject_id=subject.id,
            teacher_id=current_user.id
        )
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.created_at.desc()
        )
        .all()
    )

    return render_template(
        "teacher/attendance_history.html",
        subject=subject,
        records=records
    )
