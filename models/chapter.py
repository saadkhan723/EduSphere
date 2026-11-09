
from datetime import datetime

from extensions import db


class Chapter(db.Model):

    __tablename__ = "chapters"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False
    )

    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Google Drive file information
    drive_file_id = db.Column(
        db.String(255),
        nullable=True
    )

    drive_filename = db.Column(
        db.String(255),
        nullable=True
    )

    drive_original_filename = db.Column(
        db.String(255),
        nullable=True
    )

    drive_mime_type = db.Column(
        db.String(150),
        nullable=True
    )

    subject = db.relationship(
        "Subject",
        backref=db.backref("chapters", lazy=True)
    )

    def __repr__(self):
        return f"<Chapter {self.title}>"
