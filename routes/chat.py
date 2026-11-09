
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, request, flash
from flask_login import login_required, current_user
from sqlalchemy import and_, or_

from extensions import db
from models.user import User
from models.subject import Subject
from models.message import Message


chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def can_chat(user1, user2):
    """Allow messaging only between a teacher and an enrolled student."""

    if user1.id == user2.id:
        return False

    if user1.role == "teacher" and user2.role == "student":
        teacher, student = user1, user2

    elif user1.role == "student" and user2.role == "teacher":
        teacher, student = user2, user1

    else:
        return False

    return Subject.query.filter(
        Subject.teachers.any(id=teacher.id),
        Subject.students.any(id=student.id)
    ).first() is not None


@chat_bp.route("/")
@login_required
def inbox():

    if current_user.role not in ("teacher", "student"):
        abort(403)

    if current_user.role == "teacher":
        subjects = Subject.query.filter(
            Subject.teachers.any(id=current_user.id)
        ).all()

        contact_ids = {
            student.id
            for subject in subjects
            for student in subject.students
        }

    else:
        subjects = Subject.query.filter(
            Subject.students.any(id=current_user.id)
        ).all()

        contact_ids = {
            teacher.id
            for subject in subjects
            for teacher in subject.teachers
        }

    contacts = (
        User.query.filter(User.id.in_(contact_ids))
        .order_by(User.name.asc())
        .all()
        if contact_ids else []
    )

    unread_counts = {}

    for contact in contacts:
        unread_counts[contact.id] = Message.query.filter_by(
            sender_id=contact.id,
            recipient_id=current_user.id,
            is_read=False
        ).count()

    return render_template(
        "chat/inbox.html",
        contacts=contacts,
        unread_counts=unread_counts
    )


@chat_bp.route("/<int:user_id>", methods=["GET", "POST"])
@login_required
def room(user_id):

    if current_user.role not in ("teacher", "student"):
        abort(403)

    other_user = db.session.get(User, user_id)

    if not other_user or not can_chat(current_user, other_user):
        abort(403)

    if request.method == "POST":

        body = request.form.get("message", "").strip()

        if not body:
            flash("Message cannot be empty.", "warning")

        elif len(body) > 5000:
            flash("Message cannot exceed 5000 characters.", "danger")

        else:
            message = Message(
                sender_id=current_user.id,
                recipient_id=other_user.id,
                body=body
            )

            db.session.add(message)
            db.session.commit()

            flash("Message sent successfully.", "success")

        return redirect(url_for("chat.room", user_id=other_user.id))

    # Mark received messages as read
    unread_messages = Message.query.filter_by(
        sender_id=other_user.id,
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for message in unread_messages:
        message.is_read = True
        message.read_at = datetime.utcnow()

    db.session.commit()

    messages = Message.query.filter(
        or_(
            and_(
                Message.sender_id == current_user.id,
                Message.recipient_id == other_user.id
            ),
            and_(
                Message.sender_id == other_user.id,
                Message.recipient_id == current_user.id
            )
        )
    ).order_by(Message.created_at.asc()).all()

    return render_template(
        "chat/room.html",
        other_user=other_user,
        messages=messages
    )
