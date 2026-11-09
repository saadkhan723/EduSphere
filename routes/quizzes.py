
from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, abort, request
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

from extensions import db
from models.quiz import Quiz
from models.study_material import StudyMaterial
from models.chapter import Chapter
from models.question_bank import QuestionBank


quizzes_bp = Blueprint(
    "quizzes",
    __name__,
    url_prefix="/teacher/quizzes"
)


class QuizForm(FlaskForm):

    title = StringField(
        "Quiz Title",
        validators=[DataRequired(), Length(max=200)]
    )

    subject_id = SelectField(
        "Select Subject",
        coerce=int,
        validators=[DataRequired()]
    )

    chapter_id = SelectField("Select Chapter", coerce=int)

    material_id = SelectField("Select Study Material", coerce=int)

    question_count = SelectField(
        "Number of Questions",
        choices=[
            (10, "10 Questions"),
            (20, "20 Questions"),
            (30, "30 Questions"),
            (50, "50 Questions")
        ],
        coerce=int,
        validators=[DataRequired()]
    )

    difficulty = SelectField(
        "Difficulty",
        choices=[
            ("Easy", "Easy"),
            ("Medium", "Medium"),
            ("Hard", "Hard"),
            ("Mixed", "Mixed")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Create Quiz")


def get_available_questions_count(quiz):
    """Count eligible MCQs belonging to this quiz's teacher."""

    query = QuestionBank.query.filter_by(
        teacher_id=quiz.teacher_id,
        subject_id=quiz.subject_id
    )

    if quiz.chapter_id:
        query = query.filter_by(
            chapter_id=quiz.chapter_id
        )

    if quiz.difficulty != "Mixed":
        query = query.filter_by(
            difficulty=quiz.difficulty
        )

    return query.count()


@quizzes_bp.route("/", methods=["GET", "POST"])
@login_required
def create_quiz():

    if current_user.role != "teacher":
        abort(403)

    form = QuizForm()
    assigned_subjects = current_user.assigned_subjects

    form.subject_id.choices = [
        (subject.id, subject.name)
        for subject in assigned_subjects
    ]

    if request.method == "POST":
        selected_subject_id = request.form.get(
            "subject_id", type=int
        )
    else:
        selected_subject_id = request.args.get(
            "subject_id", type=int
        )

    selected_subject = next(
        (
            subject for subject in assigned_subjects
            if subject.id == selected_subject_id
        ),
        None
    )

    if selected_subject is None and assigned_subjects:
        selected_subject = assigned_subjects[0]

    if request.method == "GET" and selected_subject:
        form.subject_id.data = selected_subject.id

    form.chapter_id.choices = [(0, "No Chapter")]
    form.material_id.choices = [(0, "No Study Material")]

    if selected_subject:

        chapters = Chapter.query.filter_by(
            subject_id=selected_subject.id
        ).order_by(Chapter.title).all()

        materials = StudyMaterial.query.filter_by(
            subject_id=selected_subject.id,
            teacher_id=current_user.id
        ).order_by(StudyMaterial.title).all()

        form.chapter_id.choices += [
            (chapter.id, chapter.title)
            for chapter in chapters
        ]

        form.material_id.choices += [
            (material.id, material.title)
            for material in materials
        ]

    if not assigned_subjects:
        flash(
            "No subjects have been assigned to your account.",
            "warning"
        )

    if form.validate_on_submit():

        subject = next(
            (
                item for item in assigned_subjects
                if item.id == form.subject_id.data
            ),
            None
        )

        if subject is None:
            abort(403)

        chapter = None

        if form.chapter_id.data != 0:
            chapter = Chapter.query.filter_by(
                id=form.chapter_id.data,
                subject_id=subject.id
            ).first()

            if chapter is None:
                abort(400)

        material = None

        if form.material_id.data != 0:
            material = StudyMaterial.query.filter_by(
                id=form.material_id.data,
                subject_id=subject.id,
                teacher_id=current_user.id
            ).first()

            if material is None:
                abort(400)

        quiz = Quiz(
            title=form.title.data.strip(),
            difficulty=form.difficulty.data,
            question_count=form.question_count.data,
            teacher_id=current_user.id,
            subject_id=subject.id,
            chapter_id=chapter.id if chapter else None,
            material_id=material.id if material else None,
            status="draft"
        )

        db.session.add(quiz)
        db.session.commit()

        flash(
            "Quiz draft created successfully. "
            "Add enough MCQs and publish it when ready.",
            "success"
        )

        return redirect(url_for("quizzes.create_quiz"))

    # Current teacher ke quizzes retrieve karein
    quizzes = Quiz.query.filter_by(
        teacher_id=current_user.id
    ).order_by(
        Quiz.created_at.desc()
    ).all()

    return render_template(
        "teacher/create_quiz.html",
        form=form,
        quizzes=quizzes
    )


@quizzes_bp.route("/<int:quiz_id>/publish", methods=["POST"])
@login_required
def publish_quiz(quiz_id):

    if current_user.role != "teacher":
        abort(403)

    quiz = Quiz.query.filter_by(
        id=quiz_id,
        teacher_id=current_user.id
    ).first_or_404()

    available_count = get_available_questions_count(quiz)

    if available_count < quiz.question_count:
        flash(
            f"Cannot publish this quiz. It requires "
            f"{quiz.question_count} MCQs, but only "
            f"{available_count} eligible MCQs are available.",
            "danger"
        )

        return redirect(url_for("quizzes.create_quiz"))

    quiz.status = "published"
    db.session.commit()

    flash("Quiz published successfully!", "success")

    return redirect(url_for("quizzes.create_quiz"))


@quizzes_bp.route("/<int:quiz_id>/unpublish", methods=["POST"])
@login_required
def unpublish_quiz(quiz_id):

    if current_user.role != "teacher":
        abort(403)

    quiz = Quiz.query.filter_by(
        id=quiz_id,
        teacher_id=current_user.id
    ).first_or_404()

    quiz.status = "draft"
    db.session.commit()

    flash("Quiz unpublished successfully.", "success")

    return redirect(url_for("quizzes.create_quiz"))
