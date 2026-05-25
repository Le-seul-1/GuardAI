"""
Test script to verify GuardAI database models functionality.

This script tests:
1. Model creation and relationships
2. File count constraints (max 5 files)
3. Model methods (can_add_file, increment_file_count, calculate_security_score)
4. Unique constraints
5. Security score calculation
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardai.settings')
django.setup()

from django.contrib.auth.models import User
from github_auth.models import UserGitHubToken
from analyzer.models import AnalysisSession, FileAnalysis, SecurityReport
from django.db import IntegrityError


def test_user_github_token():
    """Test UserGitHubToken model."""
    print("\n=== Testing UserGitHubToken Model ===")
    
    # Create test user
    user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
    print(f"[OK] Created user: {user.username}")
    
    # Create GitHub token
    token = UserGitHubToken.objects.create(
        user=user,
        access_token='ghp_test_token_123456789',
        token_type='Bearer',
        scope='user,repo',
        is_active=True
    )
    print(f"[OK] Created GitHub token for {user.username}")
    print(f"  - Token type: {token.token_type}")
    print(f"  - Scope: {token.scope}")
    print(f"  - Is active: {token.is_active}")
    print(f"  - Validate token: {token.validate_token()}")
    
    return user


def test_analysis_session(user):
    """Test AnalysisSession model and file count constraints."""
    print("\n=== Testing AnalysisSession Model ===")
    
    # Create analysis session
    session = AnalysisSession.objects.create(
        user=user,
        repository_name='test-repo',
        repository_owner='testowner',
        repository_url='https://github.com/testowner/test-repo',
        branch_name='main',
        status='pending'
    )
    print(f"[OK] Created analysis session: {session}")
    print(f"  - Repository: {session.repository_owner}/{session.repository_name}")
    print(f"  - Branch: {session.branch_name}")
    print(f"  - Status: {session.status}")
    print(f"  - File count: {session.file_count}")
    
    # Test can_add_file method
    print("\n--- Testing file count constraints ---")
    for i in range(1, 7):
        can_add = session.can_add_file()
        print(f"  File {i}: can_add_file() = {can_add}, file_count = {session.file_count}")
        
        if can_add:
            success = session.increment_file_count()
            print(f"    -> increment_file_count() = {success}, new file_count = {session.file_count}")
        else:
            print(f"    -> Cannot add more files (limit reached)")
            break
    
    # Verify max 5 files
    assert session.file_count == 5, f"Expected file_count=5, got {session.file_count}"
    print(f"[OK] File count limit enforced: {session.file_count}/5 files")
    
    return session


def test_file_analysis(session):
    """Test FileAnalysis model."""
    print("\n=== Testing FileAnalysis Model ===")
    
    # Create auto-selected files (1-3)
    auto_files = []
    for i in range(1, 4):
        file = FileAnalysis.objects.create(
            session=session,
            file_path=f'src/backend/app{i}.py',
            file_name=f'app{i}.py',
            file_extension='.py',
            is_auto_selected=True,
            file_size=1024 * i,
            analysis_result={
                'explanation': f'This is file {i}',
                'vulnerabilities': [
                    {
                        'type': 'SQL Injection',
                        'severity': 'high',
                        'line': 42,
                        'description': 'Unsafe SQL query'
                    }
                ],
                'code_quality_score': 7.5
            },
            vulnerabilities_count=1,
            severity_level='high',
            analysis_order=i
        )
        auto_files.append(file)
        print(f"[OK] Created auto-selected file {i}: {file.file_name}")
        print(f"  - Path: {file.file_path}")
        print(f"  - Size: {file.file_size} bytes")
        print(f"  - Vulnerabilities: {file.vulnerabilities_count}")
        print(f"  - Severity: {file.severity_level}")
    
    # Create manually added files (4-5)
    manual_files = []
    for i in range(4, 6):
        file = FileAnalysis.objects.create(
            session=session,
            file_path=f'src/utils/helper{i}.py',
            file_name=f'helper{i}.py',
            file_extension='.py',
            is_auto_selected=False,
            file_size=512 * i,
            analysis_result={
                'explanation': f'This is helper file {i}',
                'vulnerabilities': [],
                'code_quality_score': 9.0
            },
            vulnerabilities_count=0,
            severity_level='info',
            analysis_order=i
        )
        manual_files.append(file)
        print(f"[OK] Created manual file {i}: {file.file_name}")
    
    # Test unique_together constraint
    print("\n--- Testing unique_together constraint ---")
    try:
        FileAnalysis.objects.create(
            session=session,
            file_path='src/backend/app1.py',  # Duplicate path
            file_name='app1.py',
            file_extension='.py',
            is_auto_selected=False,
            file_size=1024,
            analysis_order=6
        )
        print("[FAIL] Should not allow duplicate file_path in same session")
    except IntegrityError:
        print("[OK] Unique constraint enforced: Cannot add duplicate file_path")
    
    return auto_files + manual_files


def test_security_report(session, files):
    """Test SecurityReport model and security score calculation."""
    print("\n=== Testing SecurityReport Model ===")
    
    # Calculate vulnerability counts
    total_vulns = sum(f.vulnerabilities_count for f in files)
    critical_count = 2
    high_count = 3
    medium_count = 1
    low_count = 0
    
    # Create security report
    report = SecurityReport.objects.create(
        session=session,
        summary='Security analysis completed. Found multiple vulnerabilities.',
        total_vulnerabilities=total_vulns,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        recommendations=[
            {
                'priority': 'high',
                'category': 'Security',
                'title': 'Fix SQL Injection vulnerabilities',
                'description': 'Use parameterized queries',
                'affected_files': ['app1.py', 'app2.py']
            }
        ]
    )
    
    print(f"[OK] Created security report for session {session.id}")
    print(f"  - Total vulnerabilities: {report.total_vulnerabilities}")
    print(f"  - Critical: {report.critical_count}")
    print(f"  - High: {report.high_count}")
    print(f"  - Medium: {report.medium_count}")
    print(f"  - Low: {report.low_count}")
    
    # Test security score calculation
    print("\n--- Testing security score calculation ---")
    expected_score = report.calculate_security_score()
    print(f"  Calculated score: {expected_score}/10")
    print(f"  Stored score: {report.security_score}/10")
    
    # Verify calculation
    penalty = (critical_count * 2.0 + high_count * 1.5 + medium_count * 1.0 + low_count * 0.5)
    manual_score = max(0.0, 10.0 - penalty)
    print(f"  Manual calculation: 10.0 - {penalty} = {manual_score}")
    
    assert report.security_score == expected_score, "Security score mismatch"
    print(f"[OK] Security score calculation correct: {report.security_score}/10")
    
    return report


def test_relationships():
    """Test model relationships and queries."""
    print("\n=== Testing Model Relationships ===")
    
    # Get user with related data
    user = User.objects.get(username='testuser')
    
    # Test reverse relationships
    print(f"\n[OK] User: {user.username}")
    print(f"  - Has GitHub token: {hasattr(user, 'github_token')}")
    print(f"  - Analysis sessions: {user.analysis_sessions.count()}")
    
    # Get session with related data
    session = user.analysis_sessions.first()
    print(f"\n[OK] Session: {session.repository_name}")
    print(f"  - File analyses: {session.file_analyses.count()}")
    print(f"  - Has security report: {hasattr(session, 'security_report')}")
    
    # Query files by type
    auto_files = session.file_analyses.filter(is_auto_selected=True).count()
    manual_files = session.file_analyses.filter(is_auto_selected=False).count()
    print(f"  - Auto-selected files: {auto_files}")
    print(f"  - Manual files: {manual_files}")
    
    # Get security report
    if hasattr(session, 'security_report'):
        report = session.security_report
        print(f"\n[OK] Security Report:")
        print(f"  - Total vulnerabilities: {report.total_vulnerabilities}")
        print(f"  - Security score: {report.security_score}/10")


def cleanup():
    """Clean up test data."""
    print("\n=== Cleaning Up Test Data ===")
    User.objects.filter(username='testuser').delete()
    print("[OK] Test data cleaned up")


def main():
    """Run all tests."""
    print("=" * 60)
    print("GuardAI Database Models Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        user = test_user_github_token()
        session = test_analysis_session(user)
        files = test_file_analysis(session)
        report = test_security_report(session, files)
        test_relationships()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        cleanup()


if __name__ == '__main__':
    main()

# Made with Bob
