#!/usr/bin/env python3
"""
Light load testing script (free-tier safe)
- 5-10 concurrent users
- Realistic workflow simulation
- Metrics collection
"""

import requests
import json
import time
import concurrent.futures
from datetime import datetime
import sys
import subprocess
import re

API_URL = "https://nin1zoih0d.execute-api.ap-south-1.amazonaws.com/prod"

# Sample resumes for testing
SAMPLE_RESUMES = [
    {
        "name": "Alice Johnson",
        "email": "alice@test.com",
        "resume": "Senior Python Developer with 5 years AWS experience. Built serverless applications using Lambda, DynamoDB, and API Gateway. Reduced costs by 40% through optimization. Expertise in FastAPI, Docker, Terraform."
    },
    {
        "name": "Bob Smith",
        "email": "bob@test.com",
        "resume": "Full-stack developer, 3 years experience. Worked with React, Node.js, some Python. Familiar with AWS basics. Built a few REST APIs."
    },
    {
        "name": "Carol Martinez",
        "email": "carol@test.com",
        "resume": "DevOps Engineer with 6 years experience in AWS, Kubernetes, CI/CD. Strong Python scripting skills. Led cloud migration projects. Cost optimization expert."
    },
    {
        "name": "David Lee",
        "email": "david@test.com",
        "resume": "Junior developer, 1 year Python experience. Learning AWS through online courses. Built small Flask applications. Eager to learn serverless."
    },
    {
        "name": "Eve Wilson",
        "email": "eve@test.com",
        "resume": "Cloud Architect with 8 years AWS experience. Designed large-scale serverless systems. Expert in Lambda, Step Functions, EventBridge. Published AWS blog posts."
    }
]

def get_jwt_token():
    """Generate JWT token - extract just the token part"""
    result = subprocess.run(
        ['python3', 'generate_token.py'],
        capture_output=True,
        text=True,
        cwd='/home/akashdeep-choudhury/serverless-recruitment-system/scripts'
    )
    
    # Extract just the JWT token using regex
    output = result.stdout
    match = re.search(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', output)
    
    if match:
        return match.group(0)
    else:
        print("ERROR: Could not extract JWT token")
        print(output)
        sys.exit(1)

def submit_application(candidate, token, job_id="test-job-001"):
    """Submit a resume application"""
    try:
        response = requests.post(
            f"{API_URL}/submit",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "job_id": job_id,
                "candidate_name": candidate["name"],
                "email": candidate["email"],
                "resume_content": candidate["resume"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            submission_id = data.get("submission_id")
            print(f"✓ {candidate['name']}: Submitted (ID: {submission_id[:8]}...)")
            return submission_id
        else:
            print(f"✗ {candidate['name']}: Failed ({response.status_code}) - {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"✗ {candidate['name']}: Error - {str(e)[:100]}")
        return None

def wait_for_evaluation(submission_id, token, max_wait=120):
    """Wait for resume evaluation to complete"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"{API_URL}/results?submission_id={submission_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "RESUME_EVALUATED":
                    verdict = data.get("resume_verdict")
                    score = data.get("resume_score")
                    print(f"  → Resume evaluated: {verdict} ({score}/100)")
                    return True
                    
        except Exception:
            pass
            
        time.sleep(5)
    
    print(f"  → Timeout waiting for evaluation")
    return False

def run_single_user_test(user_num, token):
    """Simulate a single user's workflow"""
    candidate = SAMPLE_RESUMES[user_num % len(SAMPLE_RESUMES)]
    candidate = candidate.copy()  # Don't modify original
    candidate["name"] = f"{candidate['name']} #{user_num}"
    candidate["email"] = f"user{user_num}@test.com"
    
    print(f"\n[User {user_num}] Starting test...")
    
    # Submit application
    submission_id = submit_application(candidate, token)
    if not submission_id:
        return False
    
    # Wait for evaluation
    return wait_for_evaluation(submission_id, token)

def main():
    print("=" * 60)
    print("SERVERLESS RECRUITMENT - LIGHT LOAD TEST")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Concurrent users: 5")
    print(f"API: {API_URL}")
    print("=" * 60)
    
    # Get JWT token
    print("\n� Generating JWT token...")
    token = get_jwt_token()
    print(f"✓ Token generated ({token[:20]}...)")
    
    # Run concurrent tests
    print("\n� Launching concurrent requests...")
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_single_user_test, i, token) for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    elapsed = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print(f"Duration: {elapsed:.1f}s")
    print(f"Successful: {sum(results)}/5")
    print(f"Failed: {5 - sum(results)}/5")
    print("=" * 60)
    print("\n✓ Check CloudWatch dashboards for metrics!")
    print(f"  Performance: https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=serverless-recruitment-performance")
    print(f"  Business: https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=serverless-recruitment-business")

if __name__ == "__main__":
    main()
