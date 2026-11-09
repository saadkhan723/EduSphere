
from datetime import datetime

from extensions import db


class StudyMaterial(db.Model):

    __tablename__ = "study_materials"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    file_type = db.Column(
        db.String(10),
        nullable=False
    )

    # Google Drive integration
    drive_file_id = db.Column(
        db.String(255),
        nullable=True
    )

    drive_folder_id = db.Column(
        db.String(255),
        nullable=True
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False
    )

    chapter_id = db.Column(
        db.Integer,
        db.ForeignKey("chapters.id"),
        nullable=True
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    teacher = db.relationship("User")
    subject = db.relationship("Subject")
    chapter = db.relationship("Chapter")

    def __repr__(self):
        return f"<StudyMaterial {self.title}>"
