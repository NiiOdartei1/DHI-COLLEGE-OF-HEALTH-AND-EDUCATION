# Student Type Administration Guide

## Overview
The LMS now enforces two distinct student types:
- **Online Students**: Pay-to-access LMS features (exams, courses, chat, assignments)
- **Regular Students**: Admissions-only (no LMS access - they don't pay for LMS)

## Creating Students

### Method 1: Through Admissions Portal (Recommended for Tertiary)
1. Applicant goes to `/admissions/register`
2. After verification, they choose: **"Register as Online Student"** or **"Register as Regular Student"**
3. Admin approves in `/admin/admissions`
4. StudentProfile is automatically created with the selected `student_type`

### Method 2: Manual Registration (Admin)
Go to `/admin/register-continuing-student`
- Fill all fields
- **Student Type** dropdown: Select "online" or "regular"
- Click Register

## Verifying Student Type

### In Admin Panel:
1. Go to `/admin/manage-students`
2. Check the "Student Type" column (or view student profile)
3. Should see either "Online" or "Regular"

### Via Database:
```sql
SELECT user_id, first_name, last_name, student_type, current_programme 
FROM student_profile 
ORDER BY student_type;
```

### Check if Type Matches Fee Payment:
```sql
-- Online students should have LMS fee structures assigned
SELECT sp.user_id, sp.student_type, ps.study_format, ps.programme_name
FROM student_profile sp
LEFT JOIN programme_fee_structure ps ON sp.current_programme = ps.programme_name
WHERE sp.student_type = 'online'
ORDER BY sp.user_id;
```

## Troubleshooting

### "Regular student can still access exams"
❌ **Problem**: StudentProfile.student_type is still 'online'

**Check**:
```sql
SELECT user_id, student_type FROM student_profile WHERE user_id='STD001';
```

**Fix**: Update the database directly (⚠️ Do this only as emergency):
```sql
UPDATE student_profile SET student_type='regular' WHERE user_id='STD001';
```

### "Online student getting 403 on exams"
❌ **Problem**: StudentProfile.student_type is incorrectly set to 'regular'

**Check**:
```sql
SELECT user_id, student_type FROM student_profile WHERE user_id='STD002';
```

**Fix**: Update in database
```sql
UPDATE student_profile SET student_type='online' WHERE user_id='STD002';
```

### "New approved students default to online status"
✅ **Should be fixed now!** The approval flow now properly sets `student_type` from `Application.student_type`.

If still happening:
1. Check that applicant selected "Regular" or "Online" during registration
2. Verify `Application.student_type = 'regular'` before approval
3. Check that `Application.applicant_study_format` is set
4. Check admin logs for approval processing

## Fee Management

### For Online Students:
- Must have LMS fee structure set in `/admin/finance/configure-structure`
- Fee should be linked to study_format='Online' 

Example:
```
Programme: Midwifery
Level: 100
Study Format: Online
Fees: Tuition + LMS Access + Other = Total
```

### For Regular Students:
- May have admission fee only
- Should NOT have LMS fee structure assigned (they don't pay for LMS)
- Fee structure for study_format='Regular' should only have admissions fees

## Access Control Summary

| Feature | Online | Regular | Notes |
|---------|--------|---------|-------|
| Exams | ✅ | ❌ | `/exam/*` requires @online_student_required |
| Quizzes | ✅ | ❌ | Part of `/student/courses` |
| Assignments | ✅ | ❌ | Virtual Classroom system |
| Course Reg | ✅ | ❌ | `/student/courses` protected |
| Chat | ✅ | ❌ | `/chat/*` protected |
| Materials | ✅ | ❌ | `/vclass/materials/*` protected |
| Results | ✅ | ❌ | LMS-only results (not admission results) |
| Profile | ✅ | ✅ | Everyone can update profile |
| Fees | ✅ | ✅ | Everyone can view/pay fees |
| Admissions | ✅ | ✅ | Both can view admission status |
| ID Card | ✅ | ✅ | Everyone can download ID card |

## Database Schema Reference

### StudentProfile Table
```python
student_type: db.String(20), default='online'
# Values: 'online' or 'regular' 

# Property (read-only):
is_online_student  # Returns True if student_type == 'online'
```

### Application Table
```python
student_type: db.String(20), default='online'
# This is what gets copied to StudentProfile on approval

applicant_study_format: db.String(50)
# What applicant selected (Regular, Online, Weekend, etc.)
# Used for display and to determine study_format in StudentProfile
```

## Email Notifications

When admin approves an applicant:
- **Online Student**: Email includes LMS access information
- **Regular Student**: Email includes admission/registration information only

Email subject and body are different based on `application.student_type`.

See: `utils/email.py` - `send_approval_credentials_email(..., student_type='online'|'regular')`

## Bulk Operations

### Convert all students in a cohort to regular (if needed):
```sql
UPDATE student_profile 
SET student_type='regular' 
WHERE current_programme='Midwifery' AND programme_level=100 AND academic_year='2024/2025';
```

### Count students by type:
```sql
SELECT 
  study_format,
  COUNT(*) as total,
  SUM(CASE WHEN student_type='online' THEN 1 ELSE 0 END) as online_count,
  SUM(CASE WHEN student_type='regular' THEN 1 ELSE 0 END) as regular_count
FROM student_profile
GROUP BY study_format
ORDER BY study_format;
```

## Logs

Enable debug logging to see decorator checks:
```python
# In permission_decorators.py (line ~445)
logger.warning(f"Regular student attempted to access LMS feature: {current_user.user_id}")
```

Check logs when regular students try to access protected routes. Should see messages like:
```
WARNING:utils.permission_decorators:Regular student attempted to access LMS feature: STD001
```

## FAQ

**Q: Can I change a student's type after creation?**
A: Yes, update `StudentProfile.student_type` directly in database if absolutely necessary.

**Q: Do regular students get a different welcome page?**
A: Not yet. They see regular student dashboard but get 403 when clicking LMS links.

**Q: Can a regular student upgrade to online later?**
A: Yes, update `student_type` to 'online' and assign LMS fee structure.

**Q: What happens to existing students?**
A: If `student_type` is NULL or 'online', they're treated as online (existing default).

**Q: How do I audit who accessed what?**
A: Enable route logging in `permission_decorators.py` to log all 403 attempts.
