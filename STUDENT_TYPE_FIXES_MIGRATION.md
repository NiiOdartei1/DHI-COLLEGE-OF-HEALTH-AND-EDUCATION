# Student Type Fixes - Database Migration & Implementation

## Overview
Fixed two critical issues:
1. **Study format not displaying correctly** - Added `applicant_study_format` field to capture what applicant selected
2. **Missing emails for regular students** - Updated email function to send confirmation for both online and regular students with appropriate messages

## Database Changes

### New Field in Application Model
```sql
ALTER TABLE application ADD COLUMN applicant_study_format VARCHAR(50);
```

## Code Changes

### 1. Admissions Models (`admissions/models.py`)
- **Added**: `applicant_study_format` column to `Application` model to store applicant's study format choice
- **Added**: `display_study_format` property to return either admin's assigned stream or applicant's choice
- **Added**: `display_student_type` property to return human-readable student type (Online Student / Regular Student)

### 2. Admissions Routes (`admissions/routes.py`) 
- **Updated `choose_student_type`**: Now stores both `student_type` and `applicant_study_format` in the Application when selected
- **Updated `voucher_authentication`**: Ensures `applicant_study_format` is set when creating new Application

```python
# In choose_student_type route
app_row.student_type = student_type
app_row.applicant_study_format = 'Online' if student_type == 'online' else 'Regular'

# In voucher_authentication route
app_row.applicant_study_format = 'Online' if student_type == 'online' else 'Regular'
```

### 3. Admin Routes (`admin_routes.py`)
- **Updated `update_application_status`**: 
  - Now uses `study_format_final = application.admitted_stream or application.applicant_study_format or 'Regular'`
  - Passes `student_type` parameter to email function
  - Ensures StudentProfile is created with correct study_format

### 4. Email Template (`utils/email.py`)
- **Updated `send_approval_credentials_email`**: 
  - Now accepts `student_type` parameter
  - **For Online Students**: Shows LMS features and access information
  - **For Regular Students**: Clarifies they're in the regular admissions process and will not have LMS access until fully enrolled
  - Sends confirmation email to BOTH types of students

## Email Content Differences

### Online Student Approval Email
```
Learning Management System (LMS) Access
As an Online Student, you have full access to the Learning Management System where you can:
- View course materials and class notes
- Complete assignments and quizzes
- Participate in online exams
- Access the class chat and discussions
- Check your grades and academic records
```

### Regular Student Approval Email
```
Admissions Status
You are registered as a Regular Student pursuing admission through the regular admissions process. 
You will receive further communication regarding your programme placement, payment schedules, and next steps.

Note: As a regular student, you will not have access to the Learning Management System (LMS) features 
until your admission is fully processed and enrolled as an online student.
```

## Migration Steps

### 1. Create Migration
```bash
cd c:\Users\lampt\Desktop\LMS
flask db migrate -m "Add applicant_study_format to Application model"
```

### 2. Review Migration
Check the generated migration file in `migrations/versions/` and ensure it includes:
```python
op.add_column('application', sa.Column('applicant_study_format', sa.String(50), nullable=True))
```

### 3. Apply Migration
```bash
flask db upgrade
```

### 4. Verify Database
```python
from models import *
from admissions.models import Application

# Test query
app = Application.query.first()
print(f"Display Format: {app.display_study_format}")
print(f"Student Type: {app.display_student_type}")
```

## Testing Checklist

- [ ] Run registration and select "Online Student" → Check `applicant_study_format = 'Online'`
- [ ] Run registration and select "Regular Student" → Check `applicant_study_format = 'Regular'`
- [ ] Approve online student → Check email mentions LMS features
- [ ] Approve regular student → Check email mentions regular admissions process
- [ ] Check StudentProfile.study_format is set correctly in both cases
- [ ] Check application in admin panel shows correct study format

## Files Modified

1. ✅ `admissions/models.py` - Added field and properties
2. ✅ `admissions/routes.py` - Store student choice in Application
3. ✅ `admin_routes.py` - Pass student_type to email, use correct study_format
4. ✅ `utils/email.py` - Differentiated email content by student_type

## Deployment Notes

1. Apply database migration first
2. No code changes needed in other files
3. Existing applications will have NULL `applicant_study_format` - they'll default to 'Regular'
4. All new registrations will have this field populated automatically
