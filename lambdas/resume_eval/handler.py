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

def build_resume_prompt(resume_content, job_config, candidate_name):
    job_role = job_config.get("job_role", "Software Engineer")
    required_skills = job_config.get("required_skills", "")
    min_experience = job_config.get("min_experience_years", "2")
    custom_instructions = job_config.get("custom_instructions", "")
    weightage = job_config.get("resume_weightage", "60")

    dynamic_prompt = f"""You are evaluating a resume for the position of {job_role}.
Candidate: {candidate_name}

Job Requirements:
- Required Skills: {required_skills}
- Minimum Experience: {min_experience} years
- Resume Evaluation Weightage: {weightage}% of total score
{f"- Additional Instructions: {custom_instructions}" if custom_instructions else ""}

Resume Content:
{resume_content}

Evaluate this candidate on:
1. Relevant technical skills match for {job_role}
2. Years and quality of experience (minimum required: {min_experience} years)
3. Educational background
4. Project relevance to required skills: {required_skills}
5. Overall fit for the role
"""

    fixed_verdict = """
IMPORTANT: Your response must be ONLY the JSON object below. No introduction, no explanation, no markdown. Start your response with {{ and end with }}.

{{
  "score": <integer 0-100>,
  "summary": "<2-3 sentence evaluation summary>",
  "strengths": ["<strength1>", "<strength2>"],
  "gaps": ["<gap1>", "<gap2>"],
  "verdict": "<SHORTLIST or REJECT>",
  "confidence": "<HIGH or MEDIUM or LOW>"
}}"""

    return dynamic_prompt + fixed_verdict

def parse_llm_response(raw_response):
    raw_response = raw_response.strip()
    print(f"Full LLM response length: {len(raw_response)}")

    # Try direct parse first
    try:
        return json.loads(raw_response)
    except Exception:
        pass

    # Extract JSON block using regex
    json_match = re.search(r'\{[^{}]*"score"[^{}]*\}', raw_response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except Exception:
            pass

    # Fallback: find outermost braces
    start = raw_response.find("{")
    end = raw_response.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(raw_response[start:end])
        except Exception as e:
            raise ValueError(f"JSON parse failed: {e}. Raw: {raw_response[start:end][:300]}")

    raise ValueError(f"No JSON found. Raw response: {raw_response[:300]}")

def update_dynamodb(submission_id, eval_result, resume_status):
    table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    
    # Determine master status based on resume verdict
    if resume_status == "COMPLETE":
        verdict = eval_result.get("verdict", "REJECT")
        master_status = "RESUME_EVALUATED"
    else:
        master_status = "RESUME_PENDING"
    
    table.update_item(
        Key={"submission_id": submission_id},
        UpdateExpression="""SET
            #st = :master_status,
            resume_status = :rs,
            resume_score = :score,
            resume_summary = :summary,
            resume_strengths = :strengths,
            resume_gaps = :gaps,
            resume_verdict = :verdict,
            resume_confidence = :confidence,
            updated_at = :ts
        """,
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":master_status": master_status,
            ":rs": resume_status,
            ":score": eval_result.get("score", 0),
            ":summary": eval_result.get("summary", ""),
            ":strengths": eval_result.get("strengths", []),
            ":gaps": eval_result.get("gaps", []),
            ":verdict": eval_result.get("verdict", "REJECT"),
            ":confidence": eval_result.get("confidence", "LOW"),
            ":ts": timestamp
        }
    )
    print(f"Updated submission {submission_id}: status={master_status}, resume_status={resume_status}")

def lambda_handler(event, context):
    print(f"Resume eval invoked with {len(event['Records'])} records")
    for record in event["Records"]:
        body = json.loads(record["body"])
        submission_id = body["submission_id"]
        resume_s3_key = body["resume_s3_key"]
        candidate_name = body["candidate_name"]
        job_id = body.get("job_id", "default")

        print(f"Evaluating resume for submission: {submission_id}, job_id: {job_id}")
        try:
            s3_response = s3.get_object(Bucket=os.environ["S3_BUCKET"], Key=resume_s3_key)
            resume_content = s3_response["Body"].read().decode("utf-8")

            job_config = get_job_config(job_id)
            if not job_config:
                job_config = {"job_role": body.get("job_role", "Software Engineer")}

            ollama_url = get_ollama_url()
            prompt = build_resume_prompt(resume_content, job_config, candidate_name)
            raw_response = call_ollama(ollama_url, prompt)

            eval_result = parse_llm_response(raw_response)
            print(f"Parsed eval: score={eval_result.get('score')}, verdict={eval_result.get('verdict')}")

            update_dynamodb(submission_id, eval_result, "COMPLETE")
            print(f"Resume evaluation complete for {submission_id}")

        except Exception as e:
            print(f"Resume eval failed for {submission_id}: {str(e)}")
            update_dynamodb(submission_id, {}, "FAILED")
