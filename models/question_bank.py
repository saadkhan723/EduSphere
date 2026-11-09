
from datetime import datetime
from extensions import db


class QuestionBank(db.Model):
    __tablename__ = "question_bank"

    id = db.Column(db.Integer, primary_key=True)

    question_text = db.Column(db.Text, nullable=False)

    # Four MCQ options stored as JSON
    options = db.Column(db.JSON, nullable=False)

    # Correct option: A, B, C, or D
    correct_answer = db.Column(db.String(1), nullable=False)

    explanation = db.Column(db.Text, nullable=True)

    difficulty = db.Column(db.String(20), nullable=False)

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

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    subject = db.relationship("Subject")
    chapter = db.relationship("Chapter")
    teacher = db.relationship("User")

    def __repr__(self):
        return f"<QuestionBank {self.id}>"
