
from datetime import datetime, date

from sqlalchemy import UniqueConstraint
from extensions import db


class Attendance(db.Model):

    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "attendance_date",
            name="unique_student_subject_attendance"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
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

    attendance_date = db.Column(
        db.Date,
        nullable=False,
        default=date.today
    )

    status = db.Column(
        db.String(20),
        nullable=False
    )

    remarks = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    student = db.relationship(
        "User",
        foreign_keys=[student_id],
        backref="attendance_records"
    )

    teacher = db.relationship(
        "User",
        foreign_keys=[teacher_id],
        backref="marked_attendance_records"
    )

    subject = db.relationship(
        "Subject",
        backref="attendance_records"
    )

    def __repr__(self):
        return f"<Attendance Student={self.student_id} Status={self.status}>"
