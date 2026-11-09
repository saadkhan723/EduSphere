
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired
from extensions import db
from models.user import User
from models.subject import Subject


student_enrollment_bp = Blueprint(
    "student_enrollment",
    __name__,
    url_prefix="/admin"
)


class StudentEnrollmentForm(FlaskForm):
    student = SelectField(
        "Select Student",
        coerce=int,
        validators=[DataRequired()]
    )

    subjects = SelectMultipleField(
        "Assign Subjects",
        coerce=int
    )

    submit = SubmitField("Save Assignments")


@student_enrollment_bp.route(
    "/student-enrollments",
    methods=["GET", "POST"]
)
@login_required
def student_enrollments():

    if current_user.role != "admin":
        abort(403)

    form = StudentEnrollmentForm()

    students = User.query.filter_by(
        role="student"
    ).order_by(User.name).all()

    subjects = Subject.query.order_by(
        Subject.name
    ).all()

    form.student.choices = [
        (student.id, f"{student.name} ({student.email})")
        for student in students
    ]

    form.subjects.choices = [
        (subject.id, f"{subject.name} ({subject.code})")
        for subject in subjects
    ]

    if form.validate_on_submit():

        student = User.query.filter_by(
            id=form.student.data,
            role="student"
        ).first_or_404()

        selected_subjects = Subject.query.filter(
            Subject.id.in_(form.subjects.data)
        ).all() if form.subjects.data else []

        student.enrolled_subjects = selected_subjects

        db.session.commit()

        flash(
            f"Subjects successfully assigned to {student.name}.",
            "success"
        )

        return redirect(
            url_for("student_enrollment.student_enrollments")
        )

    assigned_students = User.query.filter_by(
        role="student"
    ).order_by(User.name).all()

    return render_template(
        "admin/student_enrollments.html",
        form=form,
        students=assigned_students
    )
