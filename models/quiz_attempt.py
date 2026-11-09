
from datetime import datetime
from extensions import db


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quizzes.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Is attempt ke liye randomly selected MCQ IDs
    selected_question_ids = db.Column(db.JSON, nullable=False)

    # Har question ke shuffled options ka order
    option_orders = db.Column(db.JSON, nullable=True)

    # Student ke submitted answers
    answers = db.Column(db.JSON, nullable=True)

    score = db.Column(db.Float, default=0)

    total_questions = db.Column(db.Integer, nullable=False)

    status = db.Column(
        db.String(20),
        default="in_progress",
        nullable=False
    )

    started_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    submitted_at = db.Column(
        db.DateTime,
        nullable=True
    )

    quiz = db.relationship("Quiz", backref="attempts")
    student = db.relationship("User", backref="quiz_attempts")

    def __repr__(self):
        return f"<QuizAttempt {self.id}>"
