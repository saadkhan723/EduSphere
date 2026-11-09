
from datetime import datetime

from extensions import db


class Message(db.Model):

    __tablename__ = "messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    recipient_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    body = db.Column(
        db.Text,
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    read_at = db.Column(
        db.DateTime,
        nullable=True
    )

    sender = db.relationship(
        "User",
        foreign_keys=[sender_id]
    )

    recipient = db.relationship(
        "User",
        foreign_keys=[recipient_id]
    )

    def __repr__(self):
        return f"<Message {self.id}: {self.sender_id} -> {self.recipient_id}>"
