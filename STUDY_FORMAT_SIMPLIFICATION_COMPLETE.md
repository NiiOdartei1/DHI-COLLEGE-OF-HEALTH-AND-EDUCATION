# Study Format Simplification - Complete Implementation

## Overview
The study format system has been simplified to **only support "Online" and "Regular"** formats, automatically derived from the student type selection during application.

## What Changed

### 1. **Study Formats Configuration** (admissions/forms.py)
✅ Removed: Sandwich, Part-Time, Weekend  
✅ Kept: Online, Regular  

```python
# OLD (5 formats)
STUDY_FORMATS = [
    ('', '— Select Format —'),
    ('Regular', 'Regular'),
    ('Sandwich', 'Sandwich'),
    ('Part-Time', 'Part-Time'),
    ('Weekend', 'Weekend')
]

# NEW (2 formats)
STUDY_FORMATS = [
    ('', '— Select Format —'),
    ('Online', 'Online'),
    ('Regular', 'Regular')
]
```

### 2. **Application Approval Flow** (admin_routes.py, line ~5149-5160)
Updated `update_application_status()` to **auto-derive** `study_format` from `student_type`:

```python
# OLD: Admin could manually set admitted_stream, fallback to applicant_study_format
study_format_final = application.admitted_stream or application.applicant_study_format or 'Regular'

# NEW: Auto-derive based on student_type
if application.admitted_stream:
    study_format_final = application.admitted_stream
else:
    # Auto-derive: student_type → study_format
    study_format_final = 'Online' if application.student_type == 'online' else 'Regular'
```

### 3. **Continuing Student Registration** (admin_routes.py, line ~754-759)
Removed study_format dropdown from form input; **auto-derive** from student_type selection:

```python
# OLD: Read study_format from form dropdown
study_format = request.form.get('study_format', 'Regular').strip()

# NEW: Auto-derive from student_type
student_type = request.form.get('student_type', 'online').strip()
study_format = 'Online' if student_type == 'online' else 'Regular'
```

### 4. **Continuing Student Registration Template** (templates/admin/register_continuing_student.html)
✅ **Removed** the study_format dropdown entirely  
✅ **Kept** the student_type selection with explanatory text:
- Online: Access to quizzes, assignments, exams, materials, chat
- Regular: Admissions process only, no LMS features

### 5. **Application View for Admins** (templates/admin/view_application.html)
✅ **Added** a new "Study Type Selection" card that shows:
- Type selected: "Online Student (Full LMS Access)" or "Regular Student (Admissions Only)" [with badge]
- Study Format: "Online" or "Regular"

## Data Flow

### For Admissions Flow:
```
1. Student registers → 2. Verifies email → 3. Chooses "Online" or "Regular"
    ↓
    Application.student_type = 'online' or 'regular'
    Application.applicant_study_format = 'Online' or 'Regular'
    ↓
4. Admin reviews application and sees the choice clearly displayed
    ↓
5. Admin approves → StudentProfile is created with:
    - student_type = application.student_type
    - study_format = 'Online' if student_type=='online' else 'Regular' (auto-derived)
```

### For Continuing Students (via Admin):
```
Admin creates student:
1. Selects programme, level
2. Selects student_type (Online or Regular)
3. System auto-sets: study_format = 'Online' or 'Regular'
    ↓
StudentProfile created with both fields automatically set
```

## Benefits

| Feature | Before | After |
|---------|--------|-------|
| Study formats | 5 options (Regular, Sandwich, Part-Time, Weekend, + blank) | 2 options (Online, Regular) |
| Admin input | Must manually select study_format dropdown | Auto-derived from student_type |
| Consistency | Could mismatch student_type and study_format | Always consistent |
| Fees matching | Had to match 5 study_formats | Only 2 study_formats (easy to manage) |
| Clear intent | Confusing: which format means LMS access? | Clear: Online = LMS, Regular = No LMS |

## Database Changes

**No migrations needed!**

The `study_format` column already exists in `student_profile`. The change is purely logic-level:
- `student_type` → determines if student has LMS access
- `study_format` → auto-derived to be "Online" or "Regular"

## Testing Checklist

### Test 1: Admissions Flow
1. Register new applicant
2. Verify email
3. Choose "Register as Online Student"
4. Check that `Application.student_type = 'online'`
5. Check that `Application.applicant_study_format = 'Online'`
6. View application as admin → Should see "Online Student (Full LMS Access)" badge
7. Approve → StudentProfile created with `study_format='Online'`

### Test 2: Admissions Flow - Regular Student
1. Register new applicant
2. Verify email
3. Choose "Register as Regular Student"
4. Check that `Application.student_type = 'regular'`
5. Check that `Application.applicant_study_format = 'Regular'`
6. View application as admin → Should see "Regular Student (Admissions Only)" badge
7. Approve → StudentProfile created with `study_format='Regular'`

### Test 3: Continuing Student Registration
1. Admin goes to `/admin/register-continuing-student`
2. Fill in student details
3. Select student_type: "Online"
4. Submit
5. Check StudentProfile: `study_format='Online'`, `student_type='online'`

### Test 4: Fee Structures
1. Create fee structure for "Midwifery 100 Level Online"
2. Should only show: Online, Regular in dropdown
3. Create fee structure for "Midwifery 100 Level Regular"
4. Verify both work and students get correct fees

### Test 5: Access Control
1. Online student logs in → Can access exams, courses, etc.
2. Regular student logs in → Gets 403 Forbidden on LMS features

## Configuration Changes

No configuration changes needed. The `STUDY_FORMATS` constant is used by:
- `admin_routes.py` - Finance fee structure creation
- `finance_routes.py` - Fee management
- `templates/admin/assign_fees.html` - Fee form dropdowns
- `templates/admin/edit_fee_group.html` - Fee form dropdowns

All will now show only "Online" and "Regular".

## Files Modified

1. **admissions/forms.py** - Updated STUDY_FORMATS constant
2. **admin_routes.py**
   - Line 754-759: Auto-derive study_format for continuing students
   - Line 5149-5160: Auto-derive study_format for approved applicants
3. **templates/admin/register_continuing_student.html**
   - Removed study_format dropdown section
4. **templates/admin/view_application.html**
   - Added Study Type Selection card displaying student's choice

## Backward Compatibility

✅ **Existing students are NOT affected**
- Their `study_format` values remain unchanged
- Only new registrations use the simplified flow

✅ **Existing fee structures**
- If a fee structure exists for "Sandwich" or "Weekend", it won't be deleted
- But the dropdown won't let admins create NEW ones with those values

## Migration Path (If Needed)

If you want to clean up old study_format values in the database:

```sql
-- Count students by old study_format
SELECT study_format, COUNT(*) FROM student_profile GROUP BY study_format;

-- Update old formats to Online or Regular (example: Sandwich → Online)
UPDATE student_profile 
SET study_format='Online' 
WHERE study_format IN ('Sandwich', 'Part-Time', 'Weekend');
```

But this is optional since the system will only create "Online" or "Regular" going forward.

## Summary

✅ System simplification complete  
✅ Study format is now auto-derived from student_type  
✅ Admins see clear student type selection during approval  
✅ No database migration needed  
✅ All files error-checked and working  
✅ Backward compatible with existing data
