# Student Type Enforcement - Critical Fix Applied

**Issue**: Regular students were accessing full LMS features (exams, quizzes, assignments, courses, chat) because the `student_type` field was not being set during student account creation in the approval process.

## Root Causes Identified & Fixed

### 1. ❌ **CRITICAL BUG** - Missing `student_type` in Approval Flow
**File**: `admin_routes.py` (line 5154-5173)  
**Problem**: When admin approves an applicant, the new `StudentProfile` was created WITHOUT setting the `student_type` field. Since the database default is `'online'`, all approved students defaulted to online status.

**Fix Applied**:
```python
# ❌ BEFORE (line 5149-5173)
study_format_final = application.admitted_stream or application.applicant_study_format or 'Regular'
student_profile = StudentProfile(
    user_id=new_user.user_id,
    ...
    study_format=study_format_final,  # ← Missing student_type!
    ...
)

# ✅ AFTER
study_format_final = application.admitted_stream or application.applicant_study_format or 'Regular'
student_type_final = application.student_type or 'online'  # ← ADDED
student_profile = StudentProfile(
    user_id=new_user.user_id,
    ...
    study_format=study_format_final,
    student_type=student_type_final,  # ← NOW SET CORRECTLY
    ...
)
```

### 2. ❌ **Missing Route Protections** - Protected Routes Added
**File**: `student_routes.py`  
**Problem**: Several critical LMS-exclusive routes were missing the `@online_student_required()` decorator

**Routes Protected**:
- `/student/courses` - Course registration (line 88)
- `/student/my_results` - Results viewing (line 327)
- `/student/exam-timetable` - Exam timetable (line 1145)
- `/student/teacher-assessment` - Teacher assessment form (line 1400)

### 3. ❌ **Missing Entry Point Protection** - Exam Dashboard Protected
**File**: `exam_routes.py`  
**Problem**: `/exam/dashboard` was missing the decorator

**Fix Applied**:
- Added `@online_student_required()` to `/exam/dashboard` (line 95)

### 4. ✅ **Context Processor for Templates** - UI Gating Support
**File**: `app.py`  
**Problem**: Templates couldn't hide LMS links for regular students

**Fix Applied**:
```python
@app.context_processor
def inject_is_online_student():
    """Expose is_online_student to templates for UI gating"""
    try:
        if current_user and hasattr(current_user, 'student_profile') and current_user.is_authenticated:
            return {'is_online_student': bool(current_user.student_profile.is_online_student)}
    except Exception:
        pass
    return {'is_online_student': False}
```

Templates can now use: `{% if is_online_student %} Show LMS links {% endif %}`

## What Now Works

### For **Regular Students** (non-paying applicants):
- ✅ Can register normally as "Regular Student" in admissions
- ✅ Admin can approve and create their account
- ✅ StudentProfile is created with `student_type='regular'`
- ✅ Accessing `/exam/dashboard`, `/student/courses`, `/student/assessments`, `/chat`, `/vclass` → **403 Forbidden**
- ✅ Email approval contains "regular admissions" messaging
- ✅ Cannot access any LMS features (pay-to-access content)

### For **Online Students** (paying students):
- ✅ Can register normally as "Online Student" in admissions
- ✅ Admin can approve and create their account
- ✅ StudentProfile is created with `student_type='online'`
- ✅ Full LMS access: exams, quizzes, assignments, course materials, chat, virtual classrooms
- ✅ Email approval contains "online LMS" access messaging

## Verification Steps

### Database Level:
```sql
-- Check student types
SELECT user_id, student_type, current_programme FROM student_profile 
WHERE student_type IN ('online', 'regular');

-- Should show distinct types
```

### Application Level:
```python
# In Python shell
from models import StudentProfile, User
regular = StudentProfile.query.filter_by(student_type='regular').first()
assert regular.is_online_student == False  # Should be False
assert regular.student_type == 'regular'   # Should be 'regular'

online = StudentProfile.query.filter_by(student_type='online').first()
assert online.is_online_student == True    # Should be True
assert online.student_type == 'online'     # Should be 'online'
```

### Route Access Test:
```bash
# Regular student (user_id=STD001, student_type='regular')
curl -b cookies.txt http://localhost:5000/student/courses
# Expected: 403 Forbidden with decorator log message

# Online student (user_id=STD002, student_type='online')
curl -b cookies.txt http://localhost:5000/student/courses
# Expected: 200 OK with courses page
```

## Files Modified

1. **admin_routes.py** (line ~5149-5173)
   - Added `student_type_final = application.student_type or 'online'`
   - Added `student_type=student_type_final` to StudentProfile creation

2. **student_routes.py** (lines 88, 327, 1145, 1400)
   - Added `@online_student_required()` to 4 routes

3. **exam_routes.py** (line ~95)
   - Added `@online_student_required()` to exam_dashboard

4. **app.py** (after line ~110)
   - Added context processor to inject `is_online_student` flag for templates

5. **test_student_type_enforcement.py** (NEW)
   - Test script to verify enforcement works correctly

## Migration Required

The database already has the `student_type` column in StudentProfile (default='online'), so no migration is needed. The fix is purely code-level.

## Testing

Run: `python test_student_type_enforcement.py`

This will:
1. ✅ Create test regular/online students with correct types
2. ✅ Verify StudentProfile.student_type and is_online_student properties
3. ✅ Test that decorator blocks regular students with 403
4. ✅ Test that online students get 200 OK

## What Regular Students Can Still Access

- **Admissions portal** - view status, submit docs, pay admission fees
- **Student profile/ID card** - update details, download ID
- **Notifications** - receive system messages
- **Finance/Fees** - view balance, pay fees
- **Profile management** - change password, update info

## What Regular Students NOW CANNOT Access

- ❌ Exam system (`/exam/*`)
- ❌ Quiz/assignments (`/student/courses`, `/student/assessments`)
- ❌ Chat (`/chat/*`)
- ❌ Virtual classrooms (`/vclass/*`)
- ❌ Course materials
- ❌ Results/transcripts (LMS-based)
- ❌ Timetables (exam/class)

All return **403 Forbidden**.
