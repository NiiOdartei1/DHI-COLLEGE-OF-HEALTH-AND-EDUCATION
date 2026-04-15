from flask import current_app, url_for
from flask_mailman import EmailMessage
import logging


def _get_sender():
    """
    Safely get default sender from config.
    """
    return current_app.config.get(
        'MAIL_DEFAULT_SENDER',
        'Admissions Office <no-reply@example.com>'
    )


def _get_applicant_name(applicant):
    """
    Safely resolve applicant name.
    Falls back to email if personal info is not yet filled.
    """
    try:
        if applicant.application and applicant.application.surname:
            return f"{applicant.application.surname} {applicant.application.other_names or ''}".strip()
    except Exception:
        pass

    return applicant.email


def send_email(to_email, subject, body):
    """
    Core email sender using Flask-Mailman.
    Logs failures instead of failing silently.
    """
    try:
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=_get_sender(),
            to=[to_email]
        )
        message.send()
        logging.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logging.error(f"Email sending failed to {to_email}: {str(e)}")
        return False


# ------------------------------------------------------------------
# PASSWORD RESET EMAIL
# ------------------------------------------------------------------

def send_password_reset_email(applicant, token):
    reset_url = url_for(
        'auth.reset_password',
        token=token,
        _external=True
    )

    name = _get_applicant_name(applicant)

    subject = "Password Reset – Online Admissions Portal"

    body = f"""
Dear {name},

A request has been received to reset the password for your Online Admissions Portal account.

To proceed, please click the secure link below to set a new password.
This link will expire in 1 hour.

{reset_url}

If you did not initiate this request, please ignore this email.
No changes will be made to your account.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)


# ------------------------------------------------------------------
# TEMPORARY PASSWORD EMAIL (ADMIN RESET)
# ------------------------------------------------------------------

def send_temporary_password_email(applicant, temp_password):
    name = _get_applicant_name(applicant)

    subject = "Temporary Password – Online Admissions Portal"

    body = f"""
Dear {name},

Your account password has been reset by the Admissions Office.

Your temporary password is:

{temp_password}

Please log in immediately and change your password to keep your account secure.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)


# ------------------------------------------------------------------
# EMAIL VERIFICATION (KNUST-STYLE)
# ------------------------------------------------------------------

def send_email_verification(applicant, verification_code):
    name = _get_applicant_name(applicant)

    subject = "Verify Your Email Address – Online Admissions"

    body = f"""
Dear {name},

Thank you for creating an account on the Online Admissions Portal.

To complete your registration, please verify your email address
using the verification code below:

VERIFICATION CODE: {verification_code}

This code will expire shortly.
Do not share this code with anyone.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)

# ------------------------------------------------------------------
# APPLICATION COMPLETION EMAIL
# ------------------------------------------------------------------

def send_application_completed_email(applicant):
    name = _get_applicant_name(applicant)

    subject = "Admission Application Successfully Submitted"

    body = f"""
Dear {name},

Your admission application has been successfully submitted.

Our admissions team will review your application.
If additional information is required, you will be contacted via this email address.

You may log into the Online Admissions Portal at any time to track your application status.

Thank you for choosing our institution.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)

def send_approval_credentials_email(applicant, username, student_id, temp_password, fees_info=None, student_type='online'):
    name = _get_applicant_name(applicant)

    subject = "Your Student Account is Ready – Online Admissions Portal"

    # Build LMS access message based on student type
    lms_access_message = ""
    if student_type == 'online':
        lms_access_message = """
    <hr>
    <h3>Learning Management System (LMS) Access</h3>
    <p>As an <b>Online Student</b>, you have full access to the Learning Management System where you can:</p>
    <ul>
        <li>View course materials and class notes</li>
        <li>Complete assignments and quizzes</li>
        <li>Participate in online exams</li>
        <li>Access the class chat and discussions</li>
        <li>Check your grades and academic records</li>
    </ul>
        """
    else:  # regular student
        lms_access_message = """
    <hr>
    <h3>Admissions Status</h3>
    <p>You are registered as a <b>Regular Student</b> pursuing admission through the regular admissions process. 
    You will receive further communication regarding your programme placement, payment schedules, and next steps.</p>
    <p><b>Note:</b> As a regular student, you will not have access to the Learning Management System (LMS) features 
    until your admission is fully processed and enrolled as an online student.</p>
        """

    fees_section = ""
    if fees_info:
        fees_section = f"""
    <hr>
    <h3>Programme Fees</h3>
    <p><b>Programme:</b> {fees_info.get('programme_name', 'N/A')}</p>
    <table style="border-collapse: collapse; width: 100%; margin-top: 10px;">
        <tr style="background-color: #f2f2f2;">
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Fee Component</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Amount (GHS)</th>
        </tr>
"""
        total_fees = 0
        for fee in fees_info.get('fees', []):
            amount = float(fee.get('amount', 0))
            total_fees += amount
            fees_section += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{fee.get('description', 'Fee')}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{amount:,.2f}</td>
        </tr>
"""
        fees_section += f"""
        <tr style="background-color: #f2f2f2; font-weight: bold;">
            <td style="border: 1px solid #ddd; padding: 8px;">Total</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_fees:,.2f}</td>
        </tr>
    </table>
    <p style="margin-top: 10px;">You will be prompted to pay these fees upon login to your student portal.</p>
        """

    body = f"""
    <p>Dear {name},</p>

    <p>Congratulations! Your admission application has been approved.</p>

    <p>Your student account has been created with the following credentials:</p>

    <ul>
        <li><b>Username:</b> {username}</li>
        <li><b>Student ID:</b> {student_id}</li>
        <li><b>Temporary Password:</b> {temp_password}</li>
    </ul>

    <p>
        Please log in immediately at
        <a href="{url_for('admissions.login', _external=True)}">Online Admissions Portal</a>
        and change your password.
    </p>

    {lms_access_message}

    {fees_section}

    <p>Admissions Office<br>Online Admissions Portal</p>
    """

    try:
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=_get_sender(),
            to=[applicant.email]
        )
        message.content_subtype = "html"
        message.send()
        logging.info(f"Approval credentials email sent successfully to {applicant.email}")
        return True
    except Exception as e:
        logging.error(
            f"Failed to send approval credentials email to {applicant.email}: {str(e)}"
        )
        return False
