
import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from functools import wraps

from flask import Flask, render_template, abort, redirect, url_for
from flask_login import current_user, login_required

from config import Config
from extensions import db, login_manager, csrf


# ==========================================
# DATABASE MODELS
# ==========================================

from models.user import User
from models.subject import Subject
from models.chapter import Chapter

from models import teacher_subject
from models import student_subject

from models.study_material import StudyMaterial
from models.quiz import Quiz, QuizQuestion
from models.question_bank import QuestionBank
from models.quiz_attempt import QuizAttempt

from models.assignment import Assignment
from models.assignment_submission import AssignmentSubmission
from models.attendance import Attendance
from models.message import Message

from routes.google_drive import google_drive_bp
from flask_migrate import Migrate


# ==========================================
# APPLICATION ROUTES
# ==========================================

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.teacher import teacher_bp
from routes.materials import materials_bp
from routes.quizzes import quizzes_bp
from routes.question_bank import question_bank_bp
from routes.student_enrollment import student_enrollment_bp
from routes.student import student_bp
from routes.chat import chat_bp


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

app = Flask(__name__)
app.config.from_object(Config)

# SECRET_KEY should be configured in Config/.env.
# Do not expose or hardcode production secrets here.


# ==========================================
# INITIALIZE EXTENSIONS
# ==========================================

db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)

migrate = Migrate(app, db)

login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


# ==========================================
# REGISTER BLUEPRINTS
# ==========================================

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(materials_bp)
app.register_blueprint(quizzes_bp)
app.register_blueprint(question_bank_bp)
app.register_blueprint(student_enrollment_bp)
app.register_blueprint(student_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(google_drive_bp)


# ==========================================
# GLOBAL UNREAD MESSAGE NOTIFICATION
# ==========================================

@app.context_processor
def inject_unread_message_count():

    unread_message_count = 0

    if (
        current_user.is_authenticated
        and current_user.role in ("teacher", "student")
    ):

        unread_message_count = Message.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).count()

    return {
        "unread_message_count": unread_message_count
    }


# ==========================================
# USER SESSION MANAGEMENT
# ==========================================

@login_manager.user_loader
def load_user(user_id):

    try:
        return db.session.get(User, int(user_id))

    except (ValueError, TypeError):
        return None


# ==========================================
# ROLE-BASED ACCESS PROTECTION
# ==========================================

def role_required(*roles):

    def decorator(function):

        @wraps(function)
        @login_required
        def wrapper(*args, **kwargs):

            if current_user.role not in roles:
                abort(403)

            return function(*args, **kwargs)

        return wrapper

    return decorator


# ==========================================
# HOMEPAGE
# ==========================================

@app.route("/")
def home():
    return render_template("home.html")


# ==========================================
# ABOUT US PAGE
# ==========================================

@app.route("/about")
def about():
    return render_template("about.html")


# ==========================================
# FEATURE INFORMATION
# ==========================================

FEATURES = {

    # ADMIN FEATURES

    "users": {
        "title": "User Management",
        "description": "Manage teachers and students.",
        "role": "admin"
    },

    "subjects": {
        "title": "Subject Management",
        "description": "Create and manage academic subjects.",
        "role": "admin"
    },

    "assign_subjects": {
        "title": "Teacher Subject Assignment",
        "description": "Assign academic subjects to teachers.",
        "role": "admin"
    },

    "student-enrollments": {
        "title": "Student Subject Assignment",
        "description": "Assign academic subjects to students.",
        "role": "admin"
    },

    # Admin and Teacher can open the Chapters feature.
    # Each role is redirected to its own protected page.

    "chapters": {
        "title": "Chapter Management",
        "description": "View and manage subject chapters.",
        "role": "admin",
        "roles": ["admin", "teacher"]
    },

    "overview": {
        "title": "System Overview",
        "description": "Monitor the education platform.",
        "role": "admin"
    },


    # TEACHER FEATURES

    "teacher-subjects": {
        "title": "My Subjects",
        "description": "View your assigned subjects and chapters.",
        "role": "teacher"
    },

    "attendance": {
        "title": "Attendance Management",
        "description": "Manage daily student attendance.",
        "role": "teacher"
    },

    "quizzes": {
        "title": "Quiz Generator",
        "description": "Create and manage MCQ quizzes.",
        "role": "teacher"
    },

    "materials": {
        "title": "Study Materials",
        "description": "Manage slides and documents.",
        "role": "teacher"
    },

    "teacher-assignments": {
        "title": "Assignments",
        "description": "Create assignments and review student submissions.",
        "role": "teacher"
    },


    # STUDENT FEATURES

    "my-subjects": {
        "title": "My Subjects",
        "description": "View your enrolled subjects.",
        "role": "student"
    },

    "my-quizzes": {
        "title": "My Quizzes",
        "description": "Attempt available MCQ quizzes.",
        "role": "student"
    },

    "my-attendance": {
        "title": "My Attendance",
        "description": "Check your attendance record.",
        "role": "student"
    },

    "my-assignments": {
        "title": "My Assignments",
        "description": "View, download and submit your assignments.",
        "role": "student"
    }
}


# ==========================================
# FEATURE PAGE
# ==========================================

@app.route("/feature/<slug>")
@login_required
def open_feature(slug):

    feature = FEATURES.get(slug)

    if feature is None:
        abort(404)

    # Check allowed roles.
    # Features without "roles" use their original single role.

    allowed_roles = feature.get(
        "roles",
        [feature["role"]]
    )

    if current_user.role not in allowed_roles:
        abort(403)

    # ======================================
    # ADMIN PAGE REDIRECTS
    # ======================================

    if slug == "users":
        return redirect(url_for("admin.users"))

    if slug == "subjects":
        return redirect(url_for("admin.subjects"))

    if slug == "chapters":

        if current_user.role == "admin":
            return redirect(url_for("admin.chapters"))

        if current_user.role == "teacher":
            return redirect(url_for("teacher.chapters"))

    if slug == "assign_subjects":
        return redirect(url_for("admin.assign_subjects"))

    if slug == "student-enrollments":
        return redirect(
            url_for("student_enrollment.student_enrollments")
        )

    # ======================================
    # TEACHER PAGE REDIRECTS
    # ======================================

    if slug == "teacher-subjects":
        return redirect(url_for("teacher.subjects"))

    if slug == "quizzes":
        return redirect(url_for("quizzes.create_quiz"))

    if slug == "materials":
        return redirect(url_for("materials.materials"))

    if slug == "teacher-assignments":
        return redirect(url_for("teacher.assignments"))

    if slug == "attendance":
        return redirect(url_for("teacher.attendance"))

    # ======================================
    # STUDENT PAGE REDIRECTS
    # ======================================

    if slug == "my-quizzes":
        return redirect(url_for("student.quizzes"))

    if slug == "my-assignments":
        return redirect(url_for("student.assignments"))

    if slug == "my-attendance":
        return redirect(url_for("student.attendance"))

    if slug == "my-subjects":
        return redirect(url_for("student.subjects"))

    abort(404)


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin")
@role_required("admin")
def admin_dashboard():

    cards = [

        {
            "title": "User Management",
            "description": "Manage teachers and students.",
            "status": "Management",
            "slug": "users"
        },

        {
            "title": "Subject Management",
            "description": "Create and manage academic subjects.",
            "status": "Subjects",
            "slug": "subjects"
        },

        {
            "title": "Teacher Subject Assignment",
            "description": "Assign academic subjects to teachers.",
            "status": "Assignment",
            "slug": "assign_subjects"
        },

        {
            "title": "Student Subject Assignment",
            "description": "Assign academic subjects to students.",
            "status": "Enrollment",
            "slug": "student-enrollments"
        },

        {
            "title": "Chapter Management",
            "description": "Create and manage subject chapters.",
            "status": "Chapters",
            "slug": "chapters"
        },

        {
            "title": "System Overview",
            "description": "Monitor the education platform.",
            "status": "Overview",
            "slug": "overview"
        }
    ]

    return render_template(
        "admin/dashboard.html",
        role="Admin",
        cards=cards
    )


# ==========================================
# TEACHER DASHBOARD
# ==========================================

@app.route("/teacher")
@role_required("teacher")
def teacher_dashboard():

    cards = [

        {
            "title": "My Subjects",
            "description": "View your assigned subjects and chapters.",
            "status": "My Subjects",
            "slug": "teacher-subjects"
        },

        {
            "title": "Attendance",
            "description": "Manage daily student attendance.",
            "status": "Attendance",
            "slug": "attendance"
        },

        {
            "title": "Quiz Generator",
            "description": "Create and manage MCQ quizzes.",
            "status": "Quizzes",
            "slug": "quizzes"
        },

        {
            "title": "Study Materials",
            "description": "Upload and manage slides and documents.",
            "status": "Materials",
            "slug": "materials"
        },

        {
            "title": "Assignments",
            "description": "Create assignments and review student submissions.",
            "status": "Assignments",
            "slug": "teacher-assignments"
        }
    ]

    # RECENT QUIZ SUBMISSIONS

    recent_quiz_results = (
        QuizAttempt.query
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            Quiz.teacher_id == current_user.id,
            QuizAttempt.status == "submitted",
            QuizAttempt.submitted_at.isnot(None)
        )
        .order_by(
            QuizAttempt.submitted_at.desc()
        )
        .limit(10)
        .all()
    )

    return render_template(
        "teacher/dashboard.html",
        role="Teacher",
        cards=cards,
        recent_quiz_results=recent_quiz_results
    )


# ==========================================
# STUDENT DASHBOARD
# ==========================================

@app.route("/student")
@role_required("student")
def student_dashboard():

    cards = [

        {
            "title": "My Subjects",
            "description": "View your enrolled subjects.",
            "status": "Learning",
            "slug": "my-subjects"
        },

        {
            "title": "My Quizzes",
            "description": "Attempt available MCQ quizzes.",
            "status": "Assessment",
            "slug": "my-quizzes"
        },

        {
            "title": "My Attendance",
            "description": "Check your attendance record.",
            "status": "Attendance",
            "slug": "my-attendance"
        },

        {
            "title": "My Assignments",
            "description": "View and submit your assigned work.",
            "status": "Assignments",
            "slug": "my-assignments"
        }
    ]

    return render_template(
        "student/dashboard.html",
        role="Student",
        cards=cards
    )


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


# ==========================================
# DATABASE INITIALIZATION & SERVER
# ==========================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

        print("EduSphere database initialized successfully!")

    app.run(debug=True)
