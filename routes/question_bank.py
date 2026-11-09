
import csv
import io

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    request,
    Response
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    SubmitField,
    FileField
)
from wtforms.validators import DataRequired, Length

from extensions import db
from models.question_bank import QuestionBank
from models.chapter import Chapter


question_bank_bp = Blueprint(
    "question_bank",
    __name__,
    url_prefix="/teacher/question-bank"
)


# ==========================================
# MCQ FORM
# ==========================================

class QuestionForm(FlaskForm):

    subject_id = SelectField(
        "Subject",
        coerce=int,
        validators=[DataRequired()]
    )

    chapter_id = SelectField(
        "Chapter",
        coerce=int
    )

    question_text = TextAreaField(
        "Question",
        validators=[
            DataRequired(),
            Length(max=5000)
        ]
    )

    option_a = StringField(
        "Option A",
        validators=[DataRequired(), Length(max=500)]
    )

    option_b = StringField(
        "Option B",
        validators=[DataRequired(), Length(max=500)]
    )

    option_c = StringField(
        "Option C",
        validators=[DataRequired(), Length(max=500)]
    )

    option_d = StringField(
        "Option D",
        validators=[DataRequired(), Length(max=500)]
    )

    correct_answer = SelectField(
        "Correct Answer",
        choices=[
            ("A", "Option A"),
            ("B", "Option B"),
            ("C", "Option C"),
            ("D", "Option D")
        ],
        validators=[DataRequired()]
    )

    explanation = TextAreaField(
        "Explanation",
        validators=[Length(max=5000)]
    )

    difficulty = SelectField(
        "Difficulty",
        choices=[
            ("Easy", "Easy"),
            ("Medium", "Medium"),
            ("Hard", "Hard")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Save MCQ")


# ==========================================
# BULK IMPORT FORM
# ==========================================

class BulkImportForm(FlaskForm):

    subject_id = SelectField(
        "Subject",
        coerce=int,
        validators=[DataRequired()]
    )

    chapter_id = SelectField(
        "Chapter",
        coerce=int
    )

    csv_file = FileField(
        "CSV File",
        validators=[DataRequired()]
    )

    submit = SubmitField("Import MCQs")


# ==========================================
# HELPER: TEACHER SUBJECTS
# ==========================================

def get_assigned_subjects():
    return current_user.assigned_subjects


# ==========================================
# HELPER: CHAPTER CHOICES
# ==========================================

def set_chapter_choices(form, subject_id):

    form.chapter_id.choices = [(0, "No Chapter")]

    if subject_id:

        chapters = Chapter.query.filter_by(
            subject_id=subject_id
        ).order_by(
            Chapter.title
        ).all()

        form.chapter_id.choices += [
            (chapter.id, chapter.title)
            for chapter in chapters
        ]


# ==========================================
# VIEW ALL MCQs
# ==========================================

@question_bank_bp.route("/")
@login_required
def questions():

    if current_user.role != "teacher":
        abort(403)

    questions = QuestionBank.query.filter_by(
        teacher_id=current_user.id
    ).order_by(
        QuestionBank.created_at.desc()
    ).all()

    return render_template(
        "teacher/question_bank.html",
        questions=questions
    )


# ==========================================
# ADD NEW MCQ
# ==========================================

@question_bank_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_question():

    if current_user.role != "teacher":
        abort(403)

    form = QuestionForm()

    assigned_subjects = get_assigned_subjects()

    form.subject_id.choices = [
        (subject.id, subject.name)
        for subject in assigned_subjects
    ]

    if request.method == "POST":
        selected_id = request.form.get("subject_id", type=int)
    else:
        selected_id = request.args.get("subject_id", type=int)

    subject = next(
        (
            item for item in assigned_subjects
            if item.id == selected_id
        ),
        None
    )

    if subject is None and assigned_subjects:
        subject = assigned_subjects[0]

    if request.method == "GET" and subject:
        form.subject_id.data = subject.id

    set_chapter_choices(
        form,
        subject.id if subject else None
    )

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

        question = QuestionBank(
            question_text=form.question_text.data.strip(),

            options={
                "A": form.option_a.data.strip(),
                "B": form.option_b.data.strip(),
                "C": form.option_c.data.strip(),
                "D": form.option_d.data.strip()
            },

            correct_answer=form.correct_answer.data,

            explanation=(
                form.explanation.data.strip()
                if form.explanation.data
                else None
            ),

            difficulty=form.difficulty.data,
            subject_id=subject.id,
            chapter_id=chapter.id if chapter else None,
            teacher_id=current_user.id
        )

        db.session.add(question)
        db.session.commit()

        flash("MCQ saved successfully!", "success")

        return redirect(
            url_for("question_bank.questions")
        )

    return render_template(
        "teacher/add_question.html",
        form=form,
        page_title="Add New MCQ"
    )


# ==========================================
# BULK IMPORT MCQs FROM CSV
# ==========================================

@question_bank_bp.route(
    "/import",
    methods=["GET", "POST"]
)
@login_required
def bulk_import():

    if current_user.role != "teacher":
        abort(403)

    form = BulkImportForm()

    assigned_subjects = get_assigned_subjects()

    form.subject_id.choices = [
        (subject.id, subject.name)
        for subject in assigned_subjects
    ]

    if request.method == "POST":
        selected_id = request.form.get(
            "subject_id",
            type=int
        )
    else:
        selected_id = request.args.get(
            "subject_id",
            type=int
        )

    subject = next(
        (
            item for item in assigned_subjects
            if item.id == selected_id
        ),
        None
    )

    if subject is None and assigned_subjects:
        subject = assigned_subjects[0]

    if request.method == "GET" and subject:
        form.subject_id.data = subject.id

    set_chapter_choices(
        form,
        subject.id if subject else None
    )

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

        uploaded_file = form.csv_file.data

        if not uploaded_file or not uploaded_file.filename.lower().endswith(".csv"):

            flash("Please upload a valid CSV file.", "danger")

            return redirect(
                url_for("question_bank.bulk_import")
            )

        try:
            # Read CSV as UTF-8, including Excel UTF-8 BOM files.
            content = uploaded_file.read()

            if len(content) > 2 * 1024 * 1024:
                flash(
                    "CSV file is too large. Maximum size is 2 MB.",
                    "danger"
                )
                return redirect(
                    url_for("question_bank.bulk_import")
                )

            text_content = content.decode("utf-8-sig")

            reader = csv.DictReader(
                io.StringIO(text_content)
            )

            required_columns = {
                "question",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "correct_answer",
                "explanation",
                "difficulty"
            }

            if not reader.fieldnames:
                flash("CSV file is empty.", "danger")
                return redirect(
                    url_for("question_bank.bulk_import")
                )

            actual_columns = {
                column.strip().lower()
                for column in reader.fieldnames
                if column
            }

            if not required_columns.issubset(actual_columns):

                flash(
                    "CSV columns are incorrect. Please download the sample CSV.",
                    "danger"
                )

                return redirect(
                    url_for("question_bank.bulk_import")
                )

            # Map CSV headers without case sensitivity.
            header_map = {
                column.strip().lower(): column
                for column in reader.fieldnames
                if column
            }

            existing_questions = QuestionBank.query.filter_by(
                teacher_id=current_user.id,
                subject_id=subject.id
            ).all()

            existing_texts = {
                question.question_text.strip().casefold()
                for question in existing_questions
            }

            imported_count = 0
            skipped_count = 0
            errors = []
            batch_texts = set()

            for row_number, row in enumerate(reader, start=2):

                if row_number > 502:
                    errors.append(
                        "Import limit reached. Maximum 500 MCQs per file."
                    )
                    break

                data = {
                    key: (row.get(original_key) or "").strip()
                    for key, original_key in header_map.items()
                }

                question_text = data.get("question", "")
                option_a = data.get("option_a", "")
                option_b = data.get("option_b", "")
                option_c = data.get("option_c", "")
                option_d = data.get("option_d", "")
                correct_answer = data.get(
                    "correct_answer", ""
                ).upper()
                explanation = data.get("explanation", "")
                difficulty = data.get("difficulty", "").capitalize()

                if not all([
                    question_text,
                    option_a,
                    option_b,
                    option_c,
                    option_d
                ]):
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: Question or option is empty."
                    )
                    continue

                if len(question_text) > 5000:
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: Question exceeds 5000 characters."
                    )
                    continue

                if any(
                    len(option) > 500
                    for option in [
                        option_a, option_b, option_c, option_d
                    ]
                ):
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: An option exceeds 500 characters."
                    )
                    continue

                if len(explanation) > 5000:
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: Explanation exceeds 5000 characters."
                    )
                    continue

                if correct_answer not in ["A", "B", "C", "D"]:
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: Correct answer must be A, B, C or D."
                    )
                    continue

                if difficulty not in ["Easy", "Medium", "Hard"]:
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: Difficulty must be Easy, Medium or Hard."
                    )
                    continue

                normalized_text = question_text.casefold()

                if (
                    normalized_text in existing_texts
                    or normalized_text in batch_texts
                ):
                    skipped_count += 1
                    errors.append(
                        f"Row {row_number}: Duplicate question skipped."
                    )
                    continue

                question = QuestionBank(
                    question_text=question_text,

                    options={
                        "A": option_a,
                        "B": option_b,
                        "C": option_c,
                        "D": option_d
                    },

                    correct_answer=correct_answer,
                    explanation=explanation or None,
                    difficulty=difficulty,
                    subject_id=subject.id,
                    chapter_id=chapter.id if chapter else None,
                    teacher_id=current_user.id
                )

                db.session.add(question)

                batch_texts.add(normalized_text)
                imported_count += 1

            db.session.commit()

            flash(
                f"Import complete! {imported_count} MCQs imported, "
                f"{skipped_count} skipped.",
                "success"
            )

            if errors:
                flash(
                    "Some rows were skipped: " + " | ".join(errors[:15]),
                    "warning"
                )

            return redirect(
                url_for("question_bank.questions")
            )

        except UnicodeDecodeError:
            db.session.rollback()

            flash(
                "Could not read the CSV file. Please save it as UTF-8 CSV.",
                "danger"
            )

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                "Bulk MCQ import failed"
            )

            flash(
                "Import failed due to a server error. Check the terminal for details.",
                "danger"
            )

    return render_template(
        "teacher/bulk_import.html",
        form=form,
        page_title="Bulk Import MCQs"
    )


# ==========================================
# DOWNLOAD SAMPLE CSV
# ==========================================

@question_bank_bp.route("/sample-csv")
@login_required
def sample_csv():

    if current_user.role != "teacher":
        abort(403)

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "question",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "explanation",
        "difficulty"
    ])

    writer.writerow([
        "What is a firewall?",
        "A security system",
        "A programming language",
        "An operating system",
        "A web browser",
        "A",
        "A firewall monitors and controls network traffic.",
        "Easy"
    ])

    csv_content = "\ufeff" + output.getvalue()

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=edusmart_mcq_template.csv"
        }
    )


# ==========================================
# EDIT EXISTING MCQ
# ==========================================

@question_bank_bp.route(
    "/edit/<int:question_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_question(question_id):

    if current_user.role != "teacher":
        abort(403)

    question = QuestionBank.query.filter_by(
        id=question_id,
        teacher_id=current_user.id
    ).first_or_404()

    form = QuestionForm()

    assigned_subjects = get_assigned_subjects()

    form.subject_id.choices = [
        (subject.id, subject.name)
        for subject in assigned_subjects
    ]

    if request.method == "GET":

        form.subject_id.data = question.subject_id
        form.question_text.data = question.question_text

        form.option_a.data = question.options["A"]
        form.option_b.data = question.options["B"]
        form.option_c.data = question.options["C"]
        form.option_d.data = question.options["D"]

        form.correct_answer.data = question.correct_answer
        form.explanation.data = question.explanation
        form.difficulty.data = question.difficulty

    if request.method == "POST":

        selected_subject_id = request.form.get(
            "subject_id",
            type=int
        )

    else:
        selected_subject_id = question.subject_id

    subject = next(
        (
            item for item in assigned_subjects
            if item.id == selected_subject_id
        ),
        None
    )

    if subject is None:
        abort(403)

    set_chapter_choices(form, subject.id)

    if request.method == "GET":
        form.chapter_id.data = question.chapter_id or 0

    if form.validate_on_submit():

        chapter = None

        if form.chapter_id.data != 0:

            chapter = Chapter.query.filter_by(
                id=form.chapter_id.data,
                subject_id=subject.id
            ).first()

            if chapter is None:
                abort(400)

        question.question_text = form.question_text.data.strip()

        question.options = {
            "A": form.option_a.data.strip(),
            "B": form.option_b.data.strip(),
            "C": form.option_c.data.strip(),
            "D": form.option_d.data.strip()
        }

        question.correct_answer = form.correct_answer.data

        question.explanation = (
            form.explanation.data.strip()
            if form.explanation.data
            else None
        )

        question.difficulty = form.difficulty.data
        question.subject_id = subject.id
        question.chapter_id = chapter.id if chapter else None

        db.session.commit()

        flash("MCQ updated successfully!", "success")

        return redirect(
            url_for("question_bank.questions")
        )

    return render_template(
        "teacher/add_question.html",
        form=form,
        page_title="Edit MCQ"
    )


# ==========================================
# DELETE MCQ
# ==========================================

@question_bank_bp.route(
    "/delete/<int:question_id>",
    methods=["POST"]
)
@login_required
def delete_question(question_id):

    if current_user.role != "teacher":
        abort(403)

    question = QuestionBank.query.filter_by(
        id=question_id,
        teacher_id=current_user.id
    ).first_or_404()

    db.session.delete(question)
    db.session.commit()

    flash("MCQ deleted successfully!", "success")

    return redirect(
        url_for("question_bank.questions")
    )
