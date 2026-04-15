# ===== GTK RUNTIME FIX FOR WEASYPRINT (Windows) =====
import os
import sys

if sys.platform == "win32":
    gtk_path = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if os.path.exists(gtk_path):
        os.add_dll_directory(gtk_path)
        os.environ["PATH"] = gtk_path + ";" + os.environ["PATH"]
# ================================================

# app.py - My LMS — Bulletproof Startup

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, send_from_directory, current_app
from sqlalchemy import Table
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import Admin, StudentProfile, User

if os.environ.get("FLASK_ENV") == "production":
    import eventlet
    eventlet.monkey_patch()

# ===== Extensions & Config =====
from flask_login import LoginManager, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf
from flask_session import Session
from utils.extensions import db, mail, socketio
from config import Config

# ===== Logging =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Flask App =====
app = Flask(__name__)
app.config.from_object(Config)

# ===== Paths =====
DB_PATH = os.path.join(app.instance_path, "lms.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config.setdefault('SESSION_TYPE', 'sqlalchemy')
app.config['SESSION_SQLALCHEMY'] = db
app.config.setdefault('SESSION_SQLALCHEMY_TABLE', 'sessions')
app.config.setdefault('SESSION_PERMANENT', False)
app.config.setdefault('SESSION_USE_SIGNER', True)
app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.instance_path, 'uploads'))
app.config.setdefault('MATERIALS_FOLDER', os.path.join(app.instance_path, 'materials'))
app.config.setdefault('PAYMENT_PROOF_FOLDER', os.path.join(app.instance_path, 'payment_proofs'))
app.config.setdefault('RECEIPT_FOLDER', os.path.join(app.instance_path, 'receipts'))
app.config.setdefault('PROFILE_PICS_FOLDER', os.path.join(app.instance_path, 'profile_pics'))

for folder in [
    app.instance_path,
    app.config['UPLOAD_FOLDER'],
    app.config['MATERIALS_FOLDER'],
    app.config['PAYMENT_PROOF_FOLDER'],
    app.config['RECEIPT_FOLDER'],
    app.config['PROFILE_PICS_FOLDER'],
]:
    os.makedirs(folder, exist_ok=True)

logger.info("App instance path: %s", app.instance_path)

# ===== Extensions =====
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
load_dotenv()

IS_PRODUCTION = os.environ.get("FLASK_ENV") == "production"
SOCKETIO_ASYNC_MODE = "eventlet" if IS_PRODUCTION else "threading"

logger.info("SocketIO async_mode=%s", SOCKETIO_ASYNC_MODE)
socketio.init_app(app, async_mode=SOCKETIO_ASYNC_MODE, manage_session=False)

# ===== Patch Flask-Session BEFORE using it =====
from flask_session.sqlalchemy import SqlAlchemySessionInterface
from sqlalchemy import Table

# patch to allow redefinition of 'sessions' table
SqlAlchemySessionInterface.create_session_model = lambda self, app: \
    Table('sessions', db.metadata, extend_existing=True)

# now import and initialize Session
from flask_session import Session
sess = Session(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'student.student_login'

# ===== Context processors =====
@app.context_processor
def inject_current_app():
    return dict(current_app=current_app)

@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_active_assessment_period():
    def get_active_period():
        try:
            from models import TeacherAssessmentPeriod
            return TeacherAssessmentPeriod.query.filter_by(is_active=True).first()
        except Exception:
            return None
    return {'active_assessment_period': get_active_period}


@app.context_processor
def inject_is_online_student():
    """Expose `is_online_student` boolean to templates for UI gating.

    Usage in templates:
      {% if is_online_student %} show LMS links {% endif %}
    """
    try:
        if current_user and hasattr(current_user, 'student_profile') and current_user.is_authenticated:
            return {'is_online_student': bool(current_user.student_profile.is_online_student)}
    except Exception:
        pass
    return {'is_online_student': False}

# ===== Custom Jinja2 Filters =====
@app.template_filter('floatformat')
def floatformat(value, decimals=2):
    """Format a float to specified decimal places (Django-like floatformat)"""
    try:
        return f"{float(value):.{int(decimals)}f}"
    except (ValueError, TypeError):
        return value

# ===== Error Handlers =====
@app.errorhandler(CSRFError)
def handle_csrf(e):
    return jsonify({'error': 'CSRF token missing or invalid', 'reason': e.description}), 400

@app.after_request
def set_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers.setdefault('Cache-Control', 'no-store')
    return response


# Import blueprints
from admin_routes import admin_bp
from teacher_routes import teacher_bp
from student_routes import student_bp
from utils.auth_routes import auth_bp
from exam_routes import exam_bp
from vclass_routes import vclass_bp
from chat_routes import chat_bp
from admissions.routes import admissions_bp
from utils.notification_routes import notification_bp
from student_transcript_routes import create_student_transcript_blueprint
from admin_grading_routes import grading_bp
from student_results_routes import results_bp
from finance_routes import finance_bp

student_transcript_bp = create_student_transcript_blueprint()

# Register blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(teacher_bp, url_prefix="/teacher")
app.register_blueprint(student_bp, url_prefix="/student")
app.register_blueprint(auth_bp)
app.register_blueprint(exam_bp, url_prefix="/exam")
app.register_blueprint(vclass_bp, url_prefix="/vclass")
app.register_blueprint(chat_bp, url_prefix="/chat")
app.register_blueprint(admissions_bp, url_prefix="/admissions")
app.register_blueprint(notification_bp)  # Registered at /notifications
app.register_blueprint(student_transcript_bp)
app.register_blueprint(grading_bp)
app.register_blueprint(results_bp)
app.register_blueprint(finance_bp, url_prefix='/admin/finance')
#app.register_blueprint(jarvis_bp)

logger.info("✓ All blueprints registered")

# -------------------------
# Jinja filters
# -------------------------
def _start_year_filter(val):
    try:
        if not val:
            return ''
        s = str(val)
        return s.split('/')[0].split('-')[0]
    except Exception:
        return val

app.jinja_env.filters['start_year'] = _start_year_filter

# ===== Login Manager =====
@login_manager.user_loader
def load_user(user_id):
    try:
        logger.debug("load_user called with user_id=%s", user_id)
        if not user_id:
            return None

        if isinstance(user_id, str) and user_id.startswith("admin:"):
            uid = user_id.split(":", 1)[1]
            admin = Admin.query.filter_by(public_id=uid).first()
            logger.debug("Loaded admin: %s", getattr(admin, 'username', None))
            return admin

        if isinstance(user_id, str) and user_id.startswith("user:"):
            uid = user_id.split(":", 1)[1]
            user = User.query.filter_by(public_id=uid).first()
            logger.debug("Loaded user: %s", getattr(user, 'user_id', None))
            return user

        # Fallback: maybe a raw numeric id was stored
        try:
            numeric = int(user_id)
            user = User.query.get(numeric)
            if user:
                logger.debug("Loaded user by numeric id: %s", user.user_id)
                return user
        except Exception:
            pass

    except Exception as e:
        logger.exception("user_loader error: %s", e)
    return None

# ===== One-Time Initialization Function =====
def one_time_init():
    logger.info("Starting data initialization")

    # 1️⃣ Ensure tables exist
    db.create_all()

    # 2️⃣ Create SuperAdmin if missing
    super_admin = Admin.query.filter_by(username='SuperAdmin').first()
    if not super_admin:
        admin = Admin(
            username='SuperAdmin',
            admin_id='ADM001',
            email='superadmin@dhi.edu.gh',
            role='superadmin',
            profile_picture='default_avatar.png'
        )
        admin.set_password('Password123')
        Admin.apply_superadmin_preset(admin)

        db.session.add(admin)
        db.session.commit()
        logger.info("✓ SuperAdmin created")
    else:
        logger.info("✓ SuperAdmin already exists")

    # Default programmes + levels
    try:
        from utils.helpers import get_programme_choices  # Returns list of (programme_name, levels)
        
        # Fetch existing cohorts from StudentProfile (to avoid duplicates)
        existing_cohorts = {
            f"{sp.current_programme} {sp.programme_level}"
            for sp in StudentProfile.query.all()
        }

        created = 0
        for programme_name, levels in get_programme_choices():
            for level in levels:  # e.g., [100, 200, 300, 400]
                cohort_str = f"{programme_name} {level}"
                if cohort_str not in existing_cohorts:
                    # Optionally create a placeholder in StudentProfile or another "ProgrammeCohort" table
                    # Here we'll log only
                    logger.info(f"✓ Default cohort ready: {cohort_str}")
                    created += 1

        if created:
            logger.info(f"✓ Prepared {created} default tertiary cohorts")
        else:
            logger.info("✓ All default cohorts already exist")

    except Exception as e:
        logger.exception("⚠ Programme setup warning (non-fatal): %s", e)

    logger.info("=" * 70)
    logger.info("✓✓✓ APP INITIALIZATION COMPLETE - READY TO SERVE REQUESTS ✓✓✓")
    logger.info("=" * 70)

# ===== Routes =====
@app.route('/')
def home():
    try:
        return render_template('home.html')
    except Exception as e:
        logger.exception("Template error on / : %s", e)
        return f"<h1>Template rendering error: {e}</h1>", 500

@app.route('/portal')
def select_portal():
    return render_template('portal_selection.html')

@app.route('/portal/<portal>')
def redirect_to_portal(portal):
    mapping = {
        'exams': 'exam.exam_login',
        'teachers': 'teacher.teacher_login',
        'students': 'student.student_login',
        'vclass': 'vclass.vclass_login'
    }
    key = portal.lower()
    if key not in mapping:
        abort(404)
    return redirect(url_for(mapping[key]))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('select_portal'))

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    filename = secure_filename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/routes')
def list_routes():
    from urllib.parse import unquote
    lines = [f"{rule.endpoint:30s} → {unquote(str(rule))}" for rule in app.url_map.iter_rules()]
    return "<pre>" + "\n".join(sorted(lines)) + "</pre>"

# ===== Run =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting LMS app")
    logger.info("Environment: %s", "PRODUCTION" if IS_PRODUCTION else "LOCAL")
    logger.info("SocketIO mode: %s", SOCKETIO_ASYNC_MODE)

    # ===== RUN ONE-TIME INIT BEFORE SERVER START =====
    with app.app_context():
        one_time_init()

    socketio.run(
        app,
        host="0.0.0.0" if IS_PRODUCTION else "127.0.0.1",
        port=port,
        debug=not IS_PRODUCTION,
        allow_unsafe_werkzeug=not IS_PRODUCTION
    )
