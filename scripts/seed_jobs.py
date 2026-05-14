#!/usr/bin/env python3
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('serverless-recruitment-job-configs')

jobs = [
    {
        "job_id": "backend-eng-001",
        "job_role": "Backend Software Engineer",
        "required_skills": "Python, FastAPI, PostgreSQL, Redis, AWS Lambda, DynamoDB, Docker, Kubernetes",
        "min_experience_years": "3",
        "description": "Build scalable microservices and RESTful APIs. Work with event-driven architectures on AWS.",
        "custom_instructions": "Focus on system design and scalability considerations",
        "resume_weightage": "60",
        "code_weightage": "40",
        "question_difficulty": "MEDIUM",
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "job_id": "senior-backend-002",
        "job_role": "Senior Backend Engineer",
        "required_skills": "Python, Django, PostgreSQL, Redis, AWS, Microservices, System Design, Mentoring",
        "min_experience_years": "5",
        "description": "Lead backend architecture decisions, mentor junior developers, and design distributed systems handling millions of requests.",
        "custom_instructions": "Emphasize leadership experience and architectural thinking",
        "resume_weightage": "50",
        "code_weightage": "50",
        "question_difficulty": "HARD",
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "job_id": "fullstack-003",
        "job_role": "Full Stack Developer",
        "required_skills": "Python, React, TypeScript, PostgreSQL, AWS, Docker",
        "min_experience_years": "2",
        "description": "Build end-to-end features across frontend and backend. Work in a fast-paced startup environment.",
        "custom_instructions": "Evaluate both frontend and backend capabilities",
        "resume_weightage": "55",
        "code_weightage": "45",
        "question_difficulty": "MEDIUM",
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }
]

for job in jobs:
    table.put_item(Item=job)
    print(f"✓ Created job: {job['job_id']} - {job['job_role']}")

print(f"\n✓ Seeded {len(jobs)} jobs successfully")
