
from extensions import db


student_subjects = db.Table(
    "student_subjects",

    db.Column(
        "student_id",
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
