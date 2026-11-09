
from extensions import db


teacher_subjects = db.Table(
    "teacher_subjects",

    db.Column(
        "teacher_id",
        db.Integer,
        db.ForeignKey("users.id"),
        primary_key=True
    ),

    db.Column(
        "subject_id",
        db.Integer,
        db.ForeignKey("subjects.id"),
        primary_key=True
    )
)
