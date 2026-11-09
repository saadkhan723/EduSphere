
import random

from models.question_bank import QuestionBank


def generate_random_quiz(quiz):
    """
    Select random MCQs for a quiz and shuffle their options.
    """

    query = QuestionBank.query.filter_by(
        teacher_id=quiz.teacher_id,
        subject_id=quiz.subject_id
    )

    # Agar quiz kisi specific chapter ka hai
    if quiz.chapter_id:
        query = query.filter_by(
            chapter_id=quiz.chapter_id
        )

    # Mixed difficulty mein tamam levels se questions aayenge
    if quiz.difficulty != "Mixed":
        query = query.filter_by(
            difficulty=quiz.difficulty
        )

    available_questions = query.all()

    # Check karein ke required questions available hain
    if len(available_questions) < quiz.question_count:
        raise ValueError(
            f"Not enough MCQs. Required: {quiz.question_count}, "
            f"Available: {len(available_questions)}"
        )

    # Random questions select karein
    selected_questions = random.sample(
        available_questions,
        quiz.question_count
    )

    # Har question ke options ka random order
    option_orders = {}

    for question in selected_questions:
        option_keys = list(question.options.keys())
        random.shuffle(option_keys)

        option_orders[str(question.id)] = option_keys

    return selected_questions, option_orders
