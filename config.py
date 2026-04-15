import os


class Config:
    # ------------------------------------------------------
    # CORE
    # ------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # DATABASE (Render-safe)
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        SQLALCHEMY_DATABASE_URI = db_url.replace(
            "postgres://", "postgresql://"
        )
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///instance/lms.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB uploads

    # ------------------------------------------------------
    # BASE DIRECTORY
    # ------------------------------------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # ------------------------------------------------------
    # ADMISSIONS
    # ------------------------------------------------------
    VOUCHER_DEFAULT_AMOUNT = 220.0

    # ------------------------------------------------------
    # FILE UPLOADS
    # ------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "assignments")
    MATERIALS_FOLDER = os.path.join(BASE_DIR, "uploads", "materials")

    PAYMENT_PROOF_FOLDER = os.path.join(
        BASE_DIR, "static", "uploads", "payments"
    )
    RECEIPT_FOLDER = os.path.join(
        BASE_DIR, "static", "uploads", "receipts"
    )
    PROFILE_PICS_FOLDER = os.path.join(
        BASE_DIR, "static", "uploads", "profile_pictures"
    )

    # ------------------------------------------------------
    # EMAIL (Flask-Mailman – GMAIL)
    # ------------------------------------------------------
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")  # App password only

    MAIL_DEFAULT_SENDER = (
        "Admissions Office",
        MAIL_USERNAME
    )

    # ------------------------------------------------------
    # ZOOM (OPTIONAL)
    # ------------------------------------------------------
    ZOOM_ACCOUNT_ID = os.environ.get("ZOOM_ACCOUNT_ID")
    ZOOM_ACCOUNT_EMAIL = os.environ.get("ZOOM_ACCOUNT_EMAIL")
    ZOOM_CLIENT_ID = os.environ.get("ZOOM_CLIENT_ID")
    ZOOM_CLIENT_SECRET = os.environ.get("ZOOM_CLIENT_SECRET")
