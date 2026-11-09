
from datetime import datetime

import uuid
from pathlib import Path

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    abort,
    flash,
    request,
    current_app,
    send_from_directory
)

from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SubmitField
from werkzeug.utils import secure_filename

from extensions import db

from models.quiz import Quiz
from models.question_bank import QuestionBank
from models.quiz_attempt import QuizAttempt
from models.attendance import Attendance
from models.assignment import Assignment
from models.assignment_submission import AssignmentSubmission

from services.quiz_engine import generate_random_quiz
from models.study_material import StudyMaterial

from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
from flask import send_file

from services.google_drive_service import get_drive_service
from werkzeug.exceptions import HTTPException


# ==========================================
# STUDENT BLUEPRINT
# ==========================================

student_bp = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


# ==========================================
# QUIZ FORMS
# ==========================================

class StartQuizForm(FlaskForm):
    submit = SubmitField("Start Quiz")


class SubmitQuizForm(FlaskForm):
    submit = SubmitField("Submit Quiz")


# ==========================================
# STUDENT QUIZZES
# ==========================================

@student_bp.route("/quizzes")
@login_required
def quizzes():

    if current_user.role != "student":
        abort(403)

    enrolled_subject_ids = [
        subject.id
        for subject in current_user.enrolled_subjects
    ]

    available_quizzes = Quiz.query.filter(
        Quiz.status == "published",
        Quiz.subject_id.in_(enrolled_subject_ids)
    ).order_by(
        Quiz.created_at.desc()
    ).all()

    return render_template(
        "student/quizzes.html",
        quizzes=available_quizzes,
        start_form=StartQuizForm()
    )


# ==========================================
# START QUIZ
# ==========================================

@student_bp.route(
    "/quizzes/<int:quiz_id>/start",
    methods=["POST"]
)
@login_required
def start_quiz(quiz_id):

    if current_user.role != "student":
        abort(403)

    form = StartQuizForm()

    if not form.validate_on_submit():
        abort(400)

    quiz = Quiz.query.filter_by(
        id=quiz_id,
        status="published"
    ).first_or_404()

    enrolled_subject_ids = [
        subject.id
        for subject in current_user.enrolled_subjects
    ]

    if quiz.subject_id not in enrolled_subject_ids:
        abort(403)

    try:
        selected_questions, option_orders = generate_random_quiz(quiz)

    except ValueError as error:
        flash(str(error), "warning")
        return redirect(url_for("student.quizzes"))

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=current_user.id,
        selected_question_ids=[
            question.id for question in selected_questions
        ],
        option_orders=option_orders,
        answers={},
        total_questions=len(selected_questions),
        status="in_progress"
    )

    db.session.add(attempt)
    db.session.commit()

    return redirect(
        url_for("student.attempt_quiz", attempt_id=attempt.id)
    )


# ==========================================
# ATTEMPT QUIZ
# ==========================================

@student_bp.route("/attempt/<int:attempt_id>")
@login_required
def attempt_quiz(attempt_id):

    if current_user.role != "student":
        abort(403)

    attempt = QuizAttempt.query.filter_by(
        id=attempt_id,
        student_id=current_user.id
    ).first_or_404()

    if attempt.status != "in_progress":
        return redirect(
            url_for("student.quiz_result", attempt_id=attempt.id)
        )

    questions_by_id = {
        question.id: question
        for question in QuestionBank.query.filter(
            QuestionBank.id.in_(attempt.selected_question_ids)
        ).all()
    }

    questions = [
        questions_by_id[question_id]
        for question_id in attempt.selected_question_ids
        if question_id in questions_by_id
    ]

    if len(questions) != attempt.total_questions:
        abort(500)

    return render_template(
        "student/attempt_quiz.html",
        attempt=attempt,
        questions=questions,
        option_orders=attempt.option_orders or {},
        form=SubmitQuizForm()
    )


# ==========================================
# SUBMIT QUIZ
# ==========================================

@student_bp.route(
    "/attempt/<int:attempt_id>/submit",
    methods=["POST"]
)
@login_required
def submit_quiz(attempt_id):

    if current_user.role != "student":
        abort(403)

    attempt = QuizAttempt.query.filter_by(
        id=attempt_id,
        student_id=current_user.id
    ).first_or_404()

    if attempt.status != "in_progress":
        flash("This quiz has already been submitted.", "warning")
        return redirect(
            url_for("student.quiz_result", attempt_id=attempt.id)
        )

    form = SubmitQuizForm()

    if not form.validate_on_submit():
        abort(400)

    questions = QuestionBank.query.filter(
        QuestionBank.id.in_(attempt.selected_question_ids)
    ).all()

    questions_by_id = {
        question.id: question for question in questions
    }

    if len(questions_by_id) != attempt.total_questions:
        abort(500)

    submitted_answers = {}
    correct_count = 0

    for question_id in attempt.selected_question_ids:

        question = questions_by_id[question_id]
        answer = request.form.get(f"question_{question_id}", "")

        valid_options = (attempt.option_orders or {}).get(
            str(question_id), []
        )

        if answer not in valid_options:
            answer = ""

        submitted_answers[str(question_id)] = answer

        if answer and answer == question.correct_answer:
            correct_count += 1

    attempt.answers = submitted_answers
    attempt.score = correct_count
    attempt.status = "submitted"
    attempt.submitted_at = datetime.utcnow()

    db.session.commit()

    return redirect(
        url_for("student.quiz_result", attempt_id=attempt.id)
    )


# ==========================================
# QUIZ RESULT
# ==========================================

@student_bp.route("/results/<int:attempt_id>")
@login_required
def quiz_result(attempt_id):

    if current_user.role != "student":
        abort(403)

    attempt = QuizAttempt.query.filter_by(
        id=attempt_id,
        student_id=current_user.id
    ).first_or_404()

    if attempt.status != "submitted":
        abort(403)

    questions_by_id = {
        question.id: question
        for question in QuestionBank.query.filter(
            QuestionBank.id.in_(attempt.selected_question_ids)
        ).all()
    }

    questions = [
        questions_by_id[question_id]
        for question_id in attempt.selected_question_ids
        if question_id in questions_by_id
    ]

    percentage = (
        (attempt.score / attempt.total_questions) * 100
        if attempt.total_questions else 0
    )

    return render_template(
        "student/quiz_result.html",
        attempt=attempt,
        questions=questions,
        percentage=percentage
    )


# ==========================================
# STUDENT ASSIGNMENT CONFIGURATION
# ==========================================

STUDENT_SUBMISSION_EXTENSIONS = {"pdf", "doc", "docx"}


def student_assignment_folder():

    folder = Path(current_app.root_path) / "uploads" / "assignments"
    folder.mkdir(parents=True, exist_ok=True)

    return folder


def valid_submission_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in STUDENT_SUBMISSION_EXTENSIONS
    )


# ==========================================
# MY ASSIGNMENTS
# ==========================================

@student_bp.route("/assignments")
@login_required
def assignments():

    if current_user.role != "student":
        abort(403)

    enrolled_subject_ids = [
        subject.id for subject in current_user.enrolled_subjects
    ]

    items = Assignment.query.filter(
        Assignment.subject_id.in_(enrolled_subject_ids)
    ).order_by(Assignment.due_date.asc()).all()

    submissions = {
        item.assignment_id: item
        for item in AssignmentSubmission.query.filter_by(
            student_id=current_user.id
        ).all()
    }

    return render_template(
        "student/assignments.html",
        assignments=items,
        submissions=submissions,
        now=datetime.now()
    )


# ==========================================
# ASSIGNMENT DETAILS
# ==========================================

@student_bp.route("/assignments/<int:assignment_id>")
@login_required
def assignment_detail(assignment_id):

    if current_user.role != "student":
        abort(403)

    enrolled_subject_ids = [
        subject.id for subject in current_user.enrolled_subjects
    ]

    assignment = Assignment.query.filter(
        Assignment.id == assignment_id,
        Assignment.subject_id.in_(enrolled_subject_ids)
    ).first_or_404()

    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id,
        student_id=current_user.id
    ).first()

    return render_template(
        "student/assignment_detail.html",
        assignment=assignment,
        submission=submission,
        now=datetime.now()
    )


# ==========================================
# DOWNLOAD TEACHER ATTACHMENT
# ==========================================

@student_bp.route(
    "/assignments/<int:assignment_id>/attachment"
)
@login_required
def download_assignment_file(assignment_id):

    if current_user.role != "student":
        abort(403)

    enrolled_subject_ids = [
        subject.id for subject in current_user.enrolled_subjects
    ]

    assignment = Assignment.query.filter(
        Assignment.id == assignment_id,
        Assignment.subject_id.in_(enrolled_subject_ids)
    ).first_or_404()

    if not assignment.attachment_filename:
        abort(404)

    return send_from_directory(
        student_assignment_folder(),
        assignment.attachment_filename,
        as_attachment=True,
        download_name=assignment.attachment_original_name
    )


# ==========================================
# SUBMIT / RESUBMIT ASSIGNMENT
# ==========================================

@student_bp.route(
    "/assignments/<int:assignment_id>/submit",
    methods=["POST"]
)
@login_required
def submit_assignment(assignment_id):

    if current_user.role != "student":
        abort(403)

    enrolled_subject_ids = [
        subject.id for subject in current_user.enrolled_subjects
    ]

    assignment = Assignment.query.filter(
        Assignment.id == assignment_id,
        Assignment.subject_id.in_(enrolled_subject_ids)
    ).first_or_404()

    if datetime.now() > assignment.due_date:
        flash("The assignment deadline has passed.", "danger")
        return redirect(
            url_for(
                "student.assignment_detail",
                assignment_id=assignment.id
            )
        )

    uploaded_file = request.files.get("submission_file")

    if not uploaded_file or not uploaded_file.filename:
        flash("Please select a file to submit.", "warning")
        return redirect(
            url_for(
                "student.assignment_detail",
                assignment_id=assignment.id
            )
        )

    if not valid_submission_file(uploaded_file.filename):
        flash("Only PDF, DOC and DOCX files are allowed.", "danger")
        return redirect(
            url_for(
                "student.assignment_detail",
                assignment_id=assignment.id
            )
        )

    original_filename = secure_filename(uploaded_file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{extension}"

    folder = student_assignment_folder()
    uploaded_file.save(folder / stored_filename)

    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id,
        student_id=current_user.id
    ).first()

    if submission:

        old_filename = submission.submission_filename

        submission.submission_filename = stored_filename
        submission.submission_original_name = original_filename
        submission.submitted_at = datetime.utcnow()
        submission.status = "Submitted"
        submission.marks = None
        submission.feedback = None
        submission.graded_at = None

        db.session.commit()

        if old_filename:
            old_path = folder / old_filename

            if old_path.exists():
                old_path.unlink()

    else:

        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            student_id=current_user.id,
            submission_filename=stored_filename,
            submission_original_name=original_filename,
            status="Submitted"
        )

        db.session.add(submission)
        db.session.commit()

    flash("Your assignment has been submitted successfully.", "success")

    return redirect(
        url_for(
            "student.assignment_detail",
            assignment_id=assignment.id
        )
    )



# ==========================================
# STUDENT ATTENDANCE - SUBJECT WISE
# ==========================================

@student_bp.route("/attendance")
@login_required
def attendance():

    if current_user.role != "student":
        abort(403)

    # Get student's enrolled subjects
    enrolled_subjects = current_user.enrolled_subjects

    # Get all attendance records of this student
    attendance_records = Attendance.query.filter_by(
        student_id=current_user.id
    ).order_by(
        Attendance.attendance_date.desc()
    ).all()

    # Prepare subject-wise attendance summary
    subject_summaries = []

    for subject in enrolled_subjects:

        subject_records = [
            record for record in attendance_records
            if record.subject_id == subject.id
        ]

        total_classes = len(subject_records)

        present_count = sum(
            1 for record in subject_records
            if record.status.lower() == "present"
        )

        absent_count = sum(
            1 for record in subject_records
            if record.status.lower() == "absent"
        )

        percentage = (
            (present_count / total_classes) * 100
            if total_classes else 0
        )

        subject_summaries.append({
            "subject": subject,
            "total_classes": total_classes,
            "present_count": present_count,
            "absent_count": absent_count,
            "percentage": round(percentage, 2),
            "records": subject_records
        })

    return render_template(
        "student/attendance.html",
        subject_summaries=subject_summaries
    )

# ==========================================
# STUDENT MY SUBJECTS
# ==========================================

@student_bp.route("/subjects")
@login_required
def subjects():

    if current_user.role != "student":
        abort(403)

    enrolled_subjects = current_user.enrolled_subjects

    return render_template(
        "student/subjects.html",
        subjects=enrolled_subjects
    )


# ==========================================
# STUDENT STUDY MATERIALS
# ==========================================

@student_bp.route("/subjects/<int:subject_id>/materials")
@login_required
def subject_materials(subject_id):

    if current_user.role != "student":
        abort(403)

    enrolled_subject_ids = [
        subject.id
        for subject in current_user.enrolled_subjects
    ]

    if subject_id not in enrolled_subject_ids:
        abort(403)

    materials = StudyMaterial.query.filter_by(
        subject_id=subject_id
    ).order_by(
        StudyMaterial.uploaded_at.desc()
    ).all()

    subject = next(
        (
            item for item in current_user.enrolled_subjects
            if item.id == subject_id
        ),
        None
    )

    return render_template(
        "student/materials.html",
        materials=materials,
        subject=subject
    )


# ==========================================
# DOWNLOAD STUDY MATERIAL FROM GOOGLE DRIVE
# ==========================================

@student_bp.route(
    "/materials/<int:material_id>/download"
)
@login_required
def download_study_material(material_id):

    if current_user.role != "student":
        abort(403)

    material = StudyMaterial.query.get_or_404(
        material_id
    )

    enrolled_subject_ids = [
        subject.id
        for subject in current_user.enrolled_subjects
    ]

    if material.subject_id not in enrolled_subject_ids:
        abort(403)

    if not material.drive_file_id:
        abort(404)

    try:

        service = get_drive_service()

        if service is None:
            abort(503)

        request_file = service.files().get_media(
            fileId=material.drive_file_id
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
            download_name=material.original_filename,
            mimetype=(
                "application/pdf"
                if material.file_type == "pdf"
                else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        )

    except HTTPException:
        raise

    except Exception:

        current_app.logger.exception(
            "Study material download failed."
        )

        abort(500)