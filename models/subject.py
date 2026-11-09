
from datetime import datetime
from extensions import db


class Subject(db.Model):

    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
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

    # Teacher Subject Assignment
    teachers = db.relationship(
        "User",
        secondary="teacher_subjects",
        backref="assigned_subjects"
    )

    # Student Subject Enrollment
    students = db.relationship(
        "User",
        secondary="student_subjects",
        backref="enrolled_subjects"
    )

    def __repr__(self):
        return f"<Subject {self.name}>"
