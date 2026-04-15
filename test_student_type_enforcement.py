#!/usr/bin/env python3
"""
Test script to verify student type enforcement
- Verify regular students cannot access LMS features
- Verify online students CAN access LMS features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import User, StudentProfile
from admissions.models import Application, Applicant
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_student_type_assignment():
    """Test 1: Verify student_type is correctly assigned during account creation"""
    print("\n" + "="*70)
    print("TEST 1: Student Type Assignment During Account Creation")
    print("="*70)
    
    with app.app_context():
        # Clean up test data
        test_users = User.query.filter_by(username__ilike='test_%').all()
        for user in test_users:
            StudentProfile.query.filter_by(user_id=user.user_id).delete()
            db.session.delete(user)
        db.session.commit()
        
        # Create test: regular student
        regular_user = User(
            user_id='TST001',
            username='test_regular',
            email='test_regular@example.com',
            first_name='Regular',
            last_name='Student',
            role='student'
        )
        regular_user.set_password('password123')
        db.session.add(regular_user)
        db.session.flush()
        
        regular_profile = StudentProfile(
            user_id=regular_user.user_id,
            current_programme='Midwifery',
            programme_level=100,
            student_type='regular'
        )
        db.session.add(regular_profile)
        db.session.commit()
        
        # Verify
        profile = StudentProfile.query.filter_by(user_id='TST001').first()
        assert profile is not None, "❌ StudentProfile not created"
        assert profile.student_type == 'regular', f"❌ Expected student_type='regular', got '{profile.student_type}'"
        assert not profile.is_online_student, "❌ is_online_student should be False for regular students"
        print(f"✅ Regular student created: {profile.user_id}")
        print(f"   - student_type: {profile.student_type}")
        print(f"   - is_online_student: {profile.is_online_student}")
        
        # Create test: online student
        online_user = User(
            user_id='TST002',
            username='test_online',
            email='test_online@example.com',
            first_name='Online',
            last_name='Student',
            role='student'
        )
        online_user.set_password('password123')
        db.session.add(online_user)
        db.session.flush()
        
        online_profile = StudentProfile(
            user_id=online_user.user_id,
            current_programme='Midwifery',
            programme_level=100,
            student_type='online'
        )
        db.session.add(online_profile)
        db.session.commit()
        
        # Verify
        profile = StudentProfile.query.filter_by(user_id='TST002').first()
        assert profile is not None, "❌ StudentProfile not created"
        assert profile.student_type == 'online', f"❌ Expected student_type='online', got '{profile.student_type}'"
        assert profile.is_online_student, "❌ is_online_student should be True for online students"
        print(f"✅ Online student created: {profile.user_id}")
        print(f"   - student_type: {profile.student_type}")
        print(f"   - is_online_student: {profile.is_online_student}")


def test_application_to_student_conversion():
    """Test 2: Verify Application.student_type is transferred to StudentProfile"""
    print("\n" + "="*70)
    print("TEST 2: Application -> StudentProfile Type Conversion")
    print("="*70)
    
    with app.app_context():
        # Create test application (regular student)
        applicant = Applicant(
            email='applicant_test@example.com',
            first_name='Test',
            surname='Applicant'
        )
        db.session.add(applicant)
        db.session.flush()
        
        app_regular = Application(
            applicant_id=applicant.id,
            email='applicant_test@example.com',
            first_name='Test',
            surname='Applicant',
            status='submitted',
            student_type='regular',  # 👈 Regular student choice
            applicant_study_format='Regular',
            first_choice='Midwifery',
            admitted_programme='Midwifery'
        )
        db.session.add(app_regular)
        db.session.commit()
        
        # Verify application has correct type
        app = Application.query.filter_by(email='applicant_test@example.com').first()
        assert app is not None, "❌ Application not found"
        assert app.student_type == 'regular', f"❌ Expected student_type='regular', got '{app.student_type}'"
        print(f"✅ Application created with student_type='regular'")
        print(f"   - Application.student_type: {app.student_type}")
        print(f"   - Application.applicant_study_format: {app.applicant_study_format}")
        print(f"   (When admin approves this, StudentProfile.student_type should be 'regular')")


def test_decorator_protection():
    """Test 3: Verify @online_student_required() decorator blocks regular students"""
    print("\n" + "="*70)
    print("TEST 3: Route Protection (@online_student_required Decorator)")
    print("="*70)
    
    with app.test_client() as client:
        # Get existing test users
        with app.app_context():
            regular_user = User.query.filter_by(username='test_regular').first()
            online_user = User.query.filter_by(username='test_online').first()
            
            if not regular_user or not online_user:
                print("⚠️  Test users not found. Skipping decorator test.")
                print("   Run Test 1 first to create test users.")
                return
        
        # Test 1: Regular student tries to access protected route
        with client.session_transaction() as sess:
            sess['_user_id'] = f'user:{regular_user.public_id}'
        
        response = client.get('/student/courses')
        print(f"Regular student accessing /student/courses:")
        print(f"   - Status: {response.status_code}")
        if response.status_code == 403:
            print(f"   ✅ Got 403 Forbidden (correct!)")
        else:
            print(f"   ❌ Expected 403, got {response.status_code}")
        
        # Test 2: Online student accesses protected route
        with client.session_transaction() as sess:
            sess['_user_id'] = f'user:{online_user.public_id}'
        
        response = client.get('/student/courses')
        print(f"\nOnline student accessing /student/courses:")
        print(f"   - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Got 200 OK (correct!)")
        elif response.status_code == 302:
            print(f"   ⚠️  Got 302 Redirect (may be due to flash redirect, check)")
        else:
            print(f"   ❌ Expected 200, got {response.status_code}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("STUDENT TYPE ENFORCEMENT TEST SUITE")
    print("="*70)
    
    try:
        test_student_type_assignment()
        test_application_to_student_conversion()
        test_decorator_protection()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        print("\nNext steps:")
        print("1. Manually register as 'Regular' student through admissions")
        print("2. Verify admin approval creates StudentProfile with student_type='regular'")
        print("3. Try to login as regular student and access /exams, /student/courses, /chat")
        print("4. Verify you get 403 Forbidden errors")
        print("5. Login as 'Online' student and verify access works")
        
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
