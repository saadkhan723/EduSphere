
from datetime import datetime
from extensions import db


class AssignmentSubmission(db.Model):
    __tablename__ = "assignment_submissions"

    id = db.Column(db.Integer, primary_key=True)

    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey("assignments.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    submission_filename = db.Column(db.String(255), nullable=False)
    submission_original_name = db.Column(db.String(255), nullable=False)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Submitted"
    )

    marks = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)

    assignment = db.relationship(
        "Assignment",
        back_populates="submissions"
    )

    student = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint(
            "assignment_id",
            "student_id",
            name="unique_student_assignment_submission"
        ),
    )

    def __repr__(self):
        return f"<AssignmentSubmission {self.id}>"
