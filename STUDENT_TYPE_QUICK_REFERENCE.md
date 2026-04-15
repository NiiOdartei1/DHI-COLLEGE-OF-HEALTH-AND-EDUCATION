# Student Type Separation - Quick Reference Guide

## Key Concepts

| Aspect | Online Student | Regular Student |
|--------|---|---|
| **Access Level** | Full LMS Access | Admissions Only |
| **Quizzes** | ✅ Can take | ❌ Cannot take |
| **Assignments** | ✅ Can submit | ❌ Cannot submit |
| **Exams** | ✅ Can take | ❌ Cannot take |
| **Materials** | ✅ Can access | ❌ Cannot access |
| **Chat** | ✅ Can use | ❌ Cannot use |
| **Results** | ✅ Can view | ✅ Can view |
| **Profile** | ✅ Can manage | ✅ Can manage |
| **Fees** | ✅ Can view | ✅ Can view |

---

## Database Queries

### Check Student Type
```sql
SELECT user_id, student_type FROM student_profile WHERE user_id='STD001';
```

### Change Student Type
```sql
UPDATE student_profile SET student_type='regular' WHERE user_id='STD001';
```

### Count by Type
```sql
SELECT student_type, COUNT(*) as count FROM student_profile GROUP BY student_type;
```

### Check Application Type
```sql
SELECT applicant_id, student_type FROM application WHERE applicant_id=123;
```

---

## Code Examples

### Apply Decorator to Route
```python
from utils.permission_decorators import online_student_required

@student_bp.route('/my-feature')
@login_required
@online_student_required()
def my_feature():
    return render_template('my_feature.html')
```

### Check in Template
```html
{% if current_user.student_profile.is_online_student %}
    <!-- Show LMS features -->
{% else %}
    <!-- Show message: feature not available -->
    <div class="alert alert-info">
        This feature is not available for regular students.
    </div>
{% endif %}
```

### Check in Python Code
```python
from flask_login import current_user
from models import StudentProfile

student = StudentProfile.query.filter_by(user_id=current_user.user_id).first()

if student.is_online_student:
    # Allow LMS feature
    pass
else:
    # Deny access or show alternative
    abort(403)
```

---

## Routes Affected

### ✅ Protected Routes (Online Students Only)

**Exams**:
- `/exam/exams`
- `/exam/take-exam/<id>/<attempt_id>`
- `/exam/exams/<id>/password`
- `/exam/exams/<id>/instructions`
- `/exam/exams/<id>/select-set`
- `/exam/start-exam-timer/<id>`
- `/exam/autosave_exam_answer`
- `/exam/submit_exam/<id>`
- `/exam/exam_result/<submission_id>`

**Chat**:
- `/chat/`
- `/chat/conversations`
- `/chat/conversations/<id>/messages`
- `/chat/send_dm`

**Assessments**:
- `/student/assessments`

### ✅ Open Routes (All Students)

- `/student/dashboard`
- `/student/profile`
- `/student/fees`
- `/student/my_results`
- `/student/id-card`
- `/student/notifications`

---

## Files Changed Summary

```
admissions/
├── models.py (added student_type field)
├── routes.py (added choose_student_type route)
└── templates/
    └── admissions/
        └── choose_student_type.html (NEW)

templates/
└── admin/
    └── register_continuing_student.html (updated)

exam_routes.py (@online_student_required on 9 routes)
chat_routes.py (@online_student_required on 4 routes)
student_routes.py (@online_student_required on 1 route)

models.py (added student_type to StudentProfile)

utils/
└── permission_decorators.py (added @online_student_required decorator)
```

---

## Flow Diagrams

### Admissions Registration Flow
```
Register
    ↓
Verify Email
    ↓
[NEW] Choose Student Type  ← Online or Regular
    ↓
Authenticate Voucher
    ↓
Complete Application Form
    ↓
Submit Application
    ↓
(Admissions Committee Reviews)
    ↓
Approval → StudentProfile Created with student_type
```

### Admin Registration Flow
```
Go to /admin/register-continuing-student
    ↓
Fill Form (with new Student Type dropdown)
    ↓
Select: Online Student or Regular Student
    ↓
Submit
    ↓
StudentProfile Created with student_type
```

### Feature Access Flow
```
Student Requests Protected Feature
    ↓
Check: Is user authenticated? → No → Redirect to login
    ↓
Check: Is user a student? → No → 403 Forbidden
    ↓
Check: Is student online_student? → No → 403 Forbidden
    ↓
Yes → Grant Access ✅
```

---

## Default Behavior

- **New students default to**: `student_type='online'`
- **Existing students**: Not affected (no change unless updated)
- **Backward compatible**: All existing students work as online students

---

## Testing Checklist

- [ ] Online student can access `/exam/exams`
- [ ] Regular student gets 403 on `/exam/exams`
- [ ] Online student can access `/chat/`
- [ ] Regular student gets 403 on `/chat/`
- [ ] Can select student type during admissions
- [ ] Can set student type when registering via admin
- [ ] Student type saves to database
- [ ] `is_online_student` property works correctly
- [ ] Decorator prevents unauthorized access
- [ ] Error message is clear to users

---

## Deployment Steps

1. **Backup database** (important!)
2. **Create migration**: `flask db migrate -m "Add student_type"`
3. **Run migration**: `flask db upgrade`
4. **Verify fields exist**: Check database tables
5. **Test locally** with both student types
6. **Deploy to production**
7. **Monitor logs** for 403 errors

---

## Verification Queries

### Verify Migration Successful
```sql
-- Check StudentProfile
PRAGMA table_info(student_profile);
-- Should show: student_type | VARCHAR(20) | 0 | online | 0

-- Check Application
PRAGMA table_info(application);
-- Should show: student_type | VARCHAR(20) | 0 | online | 0
```

### Check Student Records
```sql
SELECT COUNT(*) as total, 
       SUM(CASE WHEN student_type='online' THEN 1 ELSE 0 END) as online,
       SUM(CASE WHEN student_type='regular' THEN 1 ELSE 0 END) as regular
FROM student_profile;
```

---

## Support Matrix

| Need | Location | Status |
|------|----------|--------|
| Admissions student type selection | `/admissions/choose-student-type` | ✅ Implemented |
| Admin student type selection | `/admin/register-continuing-student` | ✅ Implemented |
| LMS feature protection | `@online_student_required()` | ✅ Implemented |
| Error handling | 403 Forbidden | ✅ Implemented |
| Documentation | This guide + full docs | ✅ Complete |

---

## Troubleshooting

**Q: Why is my regular student seeing error 403?**
A: That's correct! Regular students cannot access LMS features.

**Q: How do I change a student's type after creation?**
A: Run this query:
```sql
UPDATE student_profile SET student_type='online' WHERE user_id='STD001';
```

**Q: What if I want to allow regular students to access certain features?**
A: Remove the `@online_student_required()` decorator from those routes.

**Q: Does this affect existing students?**
A: No. Existing students default to `'online'` and work as before.

---

**Last Updated**: February 5, 2026
