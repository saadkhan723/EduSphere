
import uuid

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    abort
)

from flask_login import login_required, current_user
from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    SelectField,
    FileField,
    SubmitField
)

from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename

from extensions import db

from models.study_material import StudyMaterial
from models.chapter import Chapter

from services.google_drive_service import (
    get_drive_service,
    get_study_materials_folder_id,
    upload_file_to_drive,
    delete_drive_file
)


materials_bp = Blueprint(
    "materials",
    __name__,
    url_prefix="/teacher/materials"
)


class MaterialUploadForm(FlaskForm):

    title = StringField(
        "Material Title",
        validators=[DataRequired()]
    )

    subject_id = SelectField(
        "Select Subject",
        coerce=int,
        validators=[DataRequired()]
    )

    chapter_id = SelectField(
        "Select Chapter",
        coerce=int
    )

    file = FileField(
        "Select PDF or PPTX File",
        validators=[DataRequired()]
    )

    submit = SubmitField("Upload Material")


ALLOWED_EXTENSIONS = {"pdf", "pptx"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@materials_bp.route("/", methods=["GET", "POST"])
@login_required
def materials():

    # Only teachers can access this page.
    if current_user.role != "teacher":
        abort(403)

    form = MaterialUploadForm()

    assigned_subjects = current_user.assigned_subjects

    # Load subjects assigned to this teacher.
    form.subject_id.choices = [
        (subject.id, subject.name)
        for subject in assigned_subjects
    ]

    form.chapter_id.choices = [
        (0, "No chapter")
    ]

    # Load teacher's previously uploaded materials.
    uploaded_materials = StudyMaterial.query.filter_by(
        teacher_id=current_user.id
    ).order_by(
        StudyMaterial.uploaded_at.desc()
    ).all()

    if not assigned_subjects:

        flash(
            "No subjects have been assigned to your account.",
            "warning"
        )

        return render_template(
            "teacher/materials.html",
            form=form,
            materials=uploaded_materials
        )

    if form.validate_on_submit():

        # Verify selected subject belongs to this teacher.
        subject = next(
            (
                item for item in assigned_subjects
                if item.id == form.subject_id.data
            ),
            None
        )

        if subject is None:
            abort(403)

        # Validate selected chapter.
        chapter_id = form.chapter_id.data
        chapter = None

        if chapter_id:

            chapter = Chapter.query.filter_by(
                id=chapter_id,
                subject_id=subject.id
            ).first()

            if chapter is None:
                abort(400)

        uploaded_file = form.file.data

        if not uploaded_file or not uploaded_file.filename:

            flash(
                "Please select a file.",
                "danger"
            )

        elif not allowed_file(uploaded_file.filename):

            flash(
                "Only PDF and PPTX files are allowed.",
                "danger"
            )

        else:

            original_filename = secure_filename(
                uploaded_file.filename
            )

            extension = original_filename.rsplit(
                ".",
                1
            )[1].lower()

            stored_filename = (
                f"{uuid.uuid4().hex}.{extension}"
            )

            mime_types = {
                "pdf": "application/pdf",

                "pptx": (
                    "application/vnd.openxmlformats-officedocument."
                    "presentationml.presentation"
                )
            }

            drive_file = None

            try:

                # Step 1: Check Google Drive connection.
                drive_service = get_drive_service()

                if drive_service is None:
                    raise RuntimeError(
                        "Google Drive is not connected."
                    )

                # Step 2: Get Study Materials folder ID.
                folder_id = get_study_materials_folder_id(
                    drive_service
                )

                # Step 3: Upload file to Google Drive.
                drive_file = upload_file_to_drive(
                    uploaded_file=uploaded_file,
                    filename=original_filename,
                    mime_type=mime_types[extension],
                    folder_id=folder_id
                )

                # Step 4: Save file metadata in SQLite.
                material = StudyMaterial(
                    title=form.title.data.strip(),
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    file_type=extension,
                    teacher_id=current_user.id,
                    subject_id=subject.id,
                    chapter_id=chapter.id if chapter else None,
                    drive_file_id=drive_file["id"],
                    drive_folder_id=folder_id
                )

                db.session.add(material)
                db.session.commit()

                flash(
                    "Study material uploaded to Google Drive successfully!",
                    "success"
                )

                return redirect(
                    url_for("materials.materials")
                )

            except Exception:

                # Roll back database changes.
                db.session.rollback()

                # Delete uploaded Drive file if DB saving failed.
                if drive_file and drive_file.get("id"):

                    try:

                        delete_drive_file(
                            drive_file["id"]
                        )

                    except Exception:

                        current_app.logger.exception(
                            "Could not delete orphaned Google Drive file."
                        )

                current_app.logger.exception(
                    "Study material upload failed."
                )

                flash(
                    "Upload failed. Please check Google Drive connection and try again.",
                    "danger"
                )

    return render_template(
        "teacher/materials.html",
        form=form,
        materials=uploaded_materials
    )
