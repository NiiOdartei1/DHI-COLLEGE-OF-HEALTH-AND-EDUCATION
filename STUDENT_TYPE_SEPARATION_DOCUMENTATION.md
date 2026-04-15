# Student Type Separation Feature Documentation

## Overview

The LMS now supports two distinct student types with different levels of access:

1. **Online Students**: Full access to all LMS features (quizzes, assignments, exams, course materials, chat)
2. **Regular Students**: Limited to admissions process only, no access to LMS features

This feature allows institutions to manage both actively enrolled online learners and admission applicants in a single system.

---

## Architecture

### Data Models

#### StudentProfile (models.py)
```python
class StudentProfile(db.Model):
    # ... existing fields ...
    student_type = db.Column(db.String(20), default='online')  # 'online' or 'regular'
    
    @property
    def is_online_student(self):
        """Returns True if student is an online student with full LMS access"""
        return self.student_type == 'online'
```

#### Application (admissions/models.py)
```python
class Application(db.Model):
    # ... existing fields ...
    student_type = db.Column(db.String(20), default='online')  # 'online' or 'regular'
```

### Access Control Decorator

**Location**: `utils/permission_decorators.py`

```python
@online_student_required()
def some_lms_feature():
    """Only online students can access this feature"""
    pass
```

This decorator:
- Checks if the user is authenticated
- Verifies the user is a student (role='student')
- Checks if the student's profile has `student_type='online'`
- Returns 403 Forbidden if the student is a regular student

---

## Registration Flow

### Admissions Portal (Applicants)

1. **Register** → Create account with email and phone
2. **Verify Email** → Confirm email address
3. **Choose Student Type** (`/admissions/choose-student-type`) - **NEW STEP**
   - Online Student: Full LMS features
   - Regular Student: Admissions only
4. **Authenticate Voucher** → Use admission voucher
5. **Complete Application** → Fill out all required forms
6. **Submit Application** → Send for review

### Admin Registration (Continue Students)

Admins can register continuing students (Level 200-400) through:
- Route: `/admin/register-continuing-student`
- Template: `templates/admin/register_continuing_student.html`

**New Field Added**: Student Type dropdown
- **Online Student**: Gets full LMS access
- **Regular Student**: Limited access (primarily for administrative/enrollment tracking)

---

## Feature Access Control

### Protected LMS Features

The following features require `@online_student_required()` decorator:

#### Exams (`exam_routes.py`)
- `/exam/exams` - View available exams
- `/exam/take-exam/<exam_id>/<attempt_id>` - Take an exam
- `/exam/exams/<exam_id>/password` - Enter exam password
- `/exam/exams/<exam_id>/instructions` - View exam instructions
- `/exam/exams/<exam_id>/select-set` - Choose exam set
- `/exam/start-exam-timer/<exam_id>` - Start exam timer
- `/exam/autosave_exam_answer` - Auto-save exam responses
- `/exam/submit_exam/<exam_id>` - Submit exam
- `/exam/exam_result/<submission_id>` - View exam results

#### Chat (`chat_routes.py`)
- `/chat/` - Chat home page
- `/chat/conversations` - View conversations
- `/chat/conversations/<conv_id>/messages` - Get messages
- `/chat/send_dm` - Send direct message
- *Additional chat routes can be protected as needed*

#### Assessments (`student_routes.py`)
- `/student/assessments` - View assessment results

### Unprotected Student Features

These features remain accessible to all authenticated students:

- Dashboard
- Course registration
- Results and transcripts
- Student profile
- Fees management
- Notifications
- Timetable
- Appointment booking
- ID card download

---

## Implementation Details

### Step 1: Define Student Type in Models

Add the `student_type` field to both StudentProfile and Application models:

```python
student_type = db.Column(db.String(20), default='online')
```

### Step 2: Create Helper Decorator

The `@online_student_required()` decorator checks student type before allowing access:

```python
@online_student_required()
def protected_feature():
    # Only online students can reach here
    return render_template('feature.html')
```

### Step 3: Apply to Routes

Add decorator to all LMS feature routes:

```python
@exam_bp.route('/exams')
@login_required
@online_student_required()
def exams():
    # Only online students can view exams
    pass
```

### Step 4: Update Registration Flows

**Admissions Portal**:
- New route: `/admissions/choose-student-type`
- Stores choice in session
- Applies to Application record during voucher authentication

**Admin Portal**:
- Add dropdown field for student type
- Applied to StudentProfile during registration

---

## Admission Flow Updates

### New Route: `/admissions/choose-student-type`

**Location**: `admissions/routes.py`

**Method**: GET, POST

**Flow**:
1. User selects student type (Online or Regular)
2. Choice is stored in session: `session['student_type']`
3. Redirects to voucher authentication
4. At voucher binding, `student_type` is applied to Application record

**Template**: `templates/admissions/choose_student_type.html`

---

## User Experience

### For Online Students

✅ Full access to:
- Take quizzes and exams
- Submit assignments  
- Access course materials
- Chat with instructors and classmates
- View results and grades
- Full LMS experience

### For Regular Students

❌ No access to LMS features:
- Cannot take quizzes or exams
- Cannot submit assignments
- Cannot access course materials
- Cannot use chat
- Can only complete admissions process

✅ Can still access:
- Profile management
- Admission status and documents
- Basic student portal features (without LMS)

---

## Database Migration

To add the `student_type` field to existing databases, create a migration:

```bash
flask db migrate -m "Add student_type field to StudentProfile and Application"
flask db upgrade
```

Or manually:

```sql
-- For StudentProfile table
ALTER TABLE student_profile ADD COLUMN student_type VARCHAR(20) DEFAULT 'online';

-- For Application table
ALTER TABLE application ADD COLUMN student_type VARCHAR(20) DEFAULT 'online';
```

---

## Configuration

### Default Values

- **New StudentProfile**: `student_type='online'` (default)
- **New Application**: `student_type='online'` (default)

### Changing Student Type

To change a student's type after creation:

```python
# Via Admin Panel (future feature)
student = StudentProfile.query.get(student_id)
student.student_type = 'regular' or 'online'
db.session.commit()

# Or programmatically
from models import StudentProfile
student = StudentProfile.query.filter_by(user_id='STD001').first()
student.student_type = 'online'
db.session.commit()
```

---

## Testing

### Manual Testing

1. **Register Online Student via Admissions**:
   - Create account → Verify email → Select "Online Student" → Complete application
   - Verify: Can access exams, chat, assessments

2. **Register Regular Student via Admin**:
   - Go to `/admin/register-continuing-student`
   - Fill form with "Regular Student" type
   - Verify: Cannot access exams, chat, assessments (gets 403)

3. **Test Access Control**:
   - Log in as online student → Can access `/exam/exams` ✅
   - Log in as regular student → `/exam/exams` returns 403 ✅

### API Testing

```bash
# As online student (should work)
curl -H "Authorization: Bearer TOKEN" https://app.com/exam/exams
# Response: 200 OK

# As regular student (should fail)
curl -H "Authorization: Bearer TOKEN" https://app.com/exam/exams  
# Response: 403 Forbidden
```

---

## Error Handling

### Regular Student Tries to Access LMS Feature

When a regular student attempts to access a protected feature:

1. Decorator intercepts request
2. Checks `student.is_online_student` property
3. Returns HTTP 403 Forbidden
4. (Optional) Redirect to appropriate dashboard

### Error Message

```
403 Forbidden
This feature is not available for regular students. 
Please contact the admissions office if you believe this is an error.
```

---

## Future Enhancements

### 1. Admin Dashboard for Student Type Management
- Bulk change student types
- View statistics by student type
- Generate reports

### 2. Conditional Menu Items
- Hide/show menu items based on student type
- Dynamic navigation

### 3. Student Type Change Request
- Allow students to request type changes
- Admissions approval workflow

### 4. Detailed Access Logs
- Track feature access by student type
- Generate compliance reports

### 5. Customizable Access Levels
- More granular control (e.g., 'assessment_only', 'materials_only')
- Permission matrix per student type

---

## Files Modified

### Core Models
- `models.py` - Added `student_type` to `StudentProfile`
- `admissions/models.py` - Added `student_type` to `Application`

### Route Files
- `exam_routes.py` - Added `@online_student_required()` to exam routes
- `chat_routes.py` - Added `@online_student_required()` to chat routes
- `student_routes.py` - Added `@online_student_required()` to assessment route
- `admissions/routes.py` - Added student type selection step

### Templates
- `templates/admissions/choose_student_type.html` - NEW
- `templates/admin/register_continuing_student.html` - Updated with student type dropdown

### Utilities
- `utils/permission_decorators.py` - Added `@online_student_required()` decorator

---

## Rollback Plan

If needed to rollback:

1. Remove `student_type` column from database
2. Remove `@online_student_required()` decorators from routes
3. Remove student type selection from admissions flow
4. Delete `choose_student_type.html` template
5. Database migration: `ALTER TABLE student_profile DROP COLUMN student_type;`

---

## Support & Troubleshooting

### Issue: Regular student can still access LMS features

**Solution**: 
- Verify `student_type` field is in database
- Check student record: `SELECT student_type FROM student_profile WHERE user_id='STD001';`
- Ensure decorator is applied: `@online_student_required()`

### Issue: Online student getting 403 Forbidden

**Solution**:
- Check student profile: `student.is_online_student` should return `True`
- Verify `student_type='online'` in database
- Check user role: must be `role='student'`

### Issue: Student type choice not saving during registration

**Solution**:
- Verify session storage: `session['student_type']` in admissions/routes.py
- Check Application.student_type is nullable: false in form processing
- Review admissions/routes.py voucher_authentication() method

---

## References

- [Permission Decorators](utils/permission_decorators.py)
- [StudentProfile Model](models.py#L870)
- [Application Model](admissions/models.py#L25)
- [Exam Routes](exam_routes.py#L125)
- [Chat Routes](chat_routes.py#L220)
- [Student Routes](student_routes.py#L217)
- [Admissions Routes](admissions/routes.py#L165)

---

**Last Updated**: February 5, 2026
**Feature Status**: ✅ Complete and Deployed
