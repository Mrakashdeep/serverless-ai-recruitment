import json
import boto3
import urllib.request
import os
import re
from datetime import datetime, timezone

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

def get_ollama_url():
    client = boto3.client("secretsmanager", region_name=os.environ["AWS_REGION"])
    response = client.get_secret_value(SecretId=os.environ["OLLAMA_SECRET_ARN"])
    return json.loads(response["SecretString"])["url"]

def get_job_config(job_id):
    table = dynamodb.Table(os.environ["JOB_CONFIGS_TABLE"])
    result = table.get_item(Key={"job_id": job_id})
    return result.get("Item", {})

def call_ollama(ollama_url, prompt):
    data = json.dumps({
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{ollama_url}/api/generate",
        data=data,
        headers={
            "Content-Type": "application/json",
            "ngrok-skip-browser-warning": "true"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))["response"]

def build_question_prompt(resume_content, job_config, candidate_name):
    job_role = job_config.get("job_role", "Software Engineer")
    required_skills = job_config.get("required_skills", "Python, Data Structures, Algorithms")
    difficulty = job_config.get("question_difficulty", "MEDIUM")

    prompt = f"""You are a senior technical interviewer generating coding questions for a {job_role} position.

Candidate: {candidate_name}
Candidate Resume Summary: {resume_content[:500]}

Job Requirements:
- Role: {job_role}
- Required Skills: {required_skills}
- Difficulty Level: {difficulty}

Generate exactly 3 coding questions tailored to this candidate's background and the job requirements.
Questions should progressively increase in difficulty.

IMPORTANT: Respond ONLY with a valid JSON array. No introduction, no explanation. Start with [ and end with ].

[
  {{
    "question_id": "q1",
    "title": "<short question title>",
    "description": "<detailed problem statement>",
    "difficulty": "<EASY or MEDIUM or HARD>",
    "expected_skills": ["<skill1>", "<skill2>"],
    "sample_input": "<example input if applicable>",
    "sample_output": "<expected output if applicable>"
  }},
  {{
    "question_id": "q2",
    "title": "<short question title>",
    "description": "<detailed problem statement>",
    "difficulty": "<EASY or MEDIUM or HARD>",
    "expected_skills": ["<skill1>", "<skill2>"],
    "sample_input": "<example input if applicable>",
    "sample_output": "<expected output if applicable>"
  }},
  {{
    "question_id": "q3",
    "title": "<short question title>",
    "description": "<detailed problem statement>",
    "difficulty": "<EASY or MEDIUM or HARD>",
    "expected_skills": ["<skill1>", "<skill2>"],
    "sample_input": "<example input if applicable>",
    "sample_output": "<expected output if applicable>"
  }}
]"""
    return prompt

def parse_questions(raw_response):
    raw_response = raw_response.strip()
    print(f"Raw response preview: {raw_response[:500]}")

    # Try direct parse first
    try:
        return json.loads(raw_response)
    except Exception:
        pass

    # Extract JSON array
    start = raw_response.find("[")
    end = raw_response.rfind("]") + 1
    if start != -1 and end > start:
        json_str = raw_response[start:end]
        # Try parsing extracted JSON
        try:
            return json.loads(json_str)
        except Exception as e:
            # Clean common JSON issues
            print(f"JSON parse error: {e}. Attempting to clean...")
            # Remove trailing commas before closing braces/brackets
            import re
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
            try:
                return json.loads(json_str)
            except Exception as e2:
                print(f"Cleaned JSON still failed: {e2}")
                print(f"Problematic JSON: {json_str[:1000]}")
                raise ValueError(f"JSON parse failed after cleaning: {e2}")

    raise ValueError(f"No JSON array found in response: {raw_response[:300]}")

def lambda_handler(event, context):
    print(f"Question generator invoked with {len(event['Records'])} records")

    for record in event["Records"]:
        body = json.loads(record["body"])
        submission_id = body["submission_id"]
        resume_s3_key = body["resume_s3_key"]
        candidate_name = body["candidate_name"]
        job_id = body.get("job_id", "default")

        print(f"Generating questions for submission: {submission_id}")

        try:
            # Fetch resume
            s3_response = s3.get_object(
                Bucket=os.environ["S3_BUCKET"],
                Key=resume_s3_key
            )
            resume_content = s3_response["Body"].read().decode("utf-8")

            # Get job config
            job_config = get_job_config(job_id)
            if not job_config:
                job_config = {"job_role": body.get("job_role", "Software Engineer")}

            # Generate questions via Ollama
            ollama_url = get_ollama_url()
            prompt = build_question_prompt(resume_content, job_config, candidate_name)
            raw_response = call_ollama(ollama_url, prompt)
            print(f"LLM raw response length: {len(raw_response)}")

            questions = parse_questions(raw_response)
            print(f"Generated {len(questions)} questions")

            # Update DynamoDB
            table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
            timestamp = datetime.now(tz=timezone.utc).isoformat()
            table.update_item(
                Key={"submission_id": submission_id},
                UpdateExpression="SET #st = :s, coding_questions = :q, updated_at = :ts",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":s": "CODING_READY",
                    ":q": questions,
                    ":ts": timestamp
                }
            )
            print(f"Questions stored for {submission_id}, status: CODING_READY")

        except Exception as e:
            print(f"Question generation failed for {submission_id}: {str(e)}")
            table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
            table.update_item(
                Key={"submission_id": submission_id},
                UpdateExpression="SET #st = :s, updated_at = :ts",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":s": "CODING_PENDING",
                    ":ts": datetime.now(tz=timezone.utc).isoformat()
                }
            )
