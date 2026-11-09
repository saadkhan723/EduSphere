
from datetime import datetime
from extensions import db


class Quiz(db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    difficulty = db.Column(db.String(20), nullable=False)

    question_count = db.Column(db.Integer, nullable=False)

    status = db.Column(
        db.String(20),
        default="draft",
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

    chapter_id = db.Column(
        db.Integer,
        db.ForeignKey("chapters.id"),
        nullable=True
    )

    material_id = db.Column(
        db.Integer,
        db.ForeignKey("study_materials.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    questions = db.relationship(
        "QuizQuestion",
        backref="quiz",
        cascade="all, delete-orphan",
        lazy=True
    )

    teacher = db.relationship("User")
    subject = db.relationship("Subject")
    chapter = db.relationship("Chapter")
    material = db.relationship("StudyMaterial")

    def __repr__(self):
        return f"<Quiz {self.title}>"


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quizzes.id"),
        nullable=False
    )

    question_text = db.Column(db.Text, nullable=False)

    options = db.Column(db.JSON, nullable=False)

    correct_answer = db.Column(db.String(1), nullable=False)

    explanation = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<QuizQuestion {self.id}>"
