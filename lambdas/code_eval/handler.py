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

def build_code_prompt(code_answers, questions, job_config, candidate_name):
    job_role = job_config.get("job_role", "Software Engineer")
    required_skills = job_config.get("required_skills", "")
    custom_instructions = job_config.get("code_instructions", "")
    weightage = job_config.get("code_weightage", "40")

    qa_pairs = []
    for answer in code_answers:
        q_id = answer.get("question_id")
        question = next((q for q in questions if q.get("question_id") == q_id), None)
        if question:
            qa_pairs.append({"question": question, "answer": answer.get("answer", "")})

    qa_text = ""
    for i, pair in enumerate(qa_pairs, 1):
        q = pair["question"]
        qa_text += f"""
Question {i}: {q.get('title')}
Difficulty: {q.get('difficulty')}
Description: {q.get('description')}
Expected Skills: {', '.join(q.get('expected_skills', []))}

Candidate's Answer:
{pair['answer']}

---
"""

    dynamic_prompt = f"""You are a senior software engineer evaluating coding submissions for a {job_role} position.

Candidate: {candidate_name}
Target Role: {job_role}
Expected Skills: {required_skills}
Code Evaluation Weightage: {weightage}% of total score
{f"Additional Instructions: {custom_instructions}" if custom_instructions else ""}

Below are the coding questions and the candidate's answers:

{qa_text}

Evaluate the overall submission on:
1. Correctness — does each solution solve the problem correctly?
2. Code quality — readability, naming, structure across all answers
3. Problem-solving approach — algorithmic thinking and efficiency
4. Best practices — error handling, edge cases
5. Relevance to expected skills: {required_skills}
"""

    fixed_verdict = """
CRITICAL: You MUST respond with ONLY a valid JSON object. No preamble, no explanation, no markdown. Just the JSON.

Format (copy this exactly):
{"score": 85, "summary": "brief summary here", "strengths": ["strength1", "strength2"], "issues": ["issue1", "issue2"], "verdict": "PASS", "complexity": "MEDIUM", "confidence": "HIGH"}

Rules:
- score: integer 0-100
- summary: max 2 sentences
- strengths: array of max 3 strings
- issues: array of max 3 strings
- verdict: exactly "PASS" or "FAIL"
- complexity: exactly "HIGH" or "MEDIUM" or "LOW"
- confidence: exactly "HIGH" or "MEDIUM" or "LOW"
"""

    return dynamic_prompt + fixed_verdict

def parse_llm_response(raw_response):
    """Robust JSON parser with multiple fallback strategies"""
    raw_response = raw_response.strip()
    
    # Strategy 1: Direct JSON parse
    try:
        return json.loads(raw_response)
    except:
        pass
    
    # Strategy 2: Extract JSON from markdown or text
    start = raw_response.find("{")
    end = raw_response.rfind("}") + 1
    if start != -1 and end > start:
        json_str = raw_response[start:end]
        try:
            return json.loads(json_str)
        except:
            pass
    
    # Strategy 3: Fix truncated JSON by completing it
    if start != -1:
        json_str = raw_response[start:]
        # Try to complete truncated arrays/objects
        for attempt in [
            json_str + ']}}',  # Complete truncated array in object
            json_str + '"}]}',  # Complete truncated string in array
            json_str + '"}',    # Complete truncated string
            json_str + '}',     # Complete truncated object
        ]:
            try:
                return json.loads(attempt)
            except:
                continue
    
    # Strategy 4: Extract fields manually with regex
    try:
        score_match = re.search(r'"score"\s*:\s*(\d+)', raw_response)
        summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', raw_response)
        verdict_match = re.search(r'"verdict"\s*:\s*"(PASS|FAIL)"', raw_response)
        
        if score_match and verdict_match:
            return {
                "score": int(score_match.group(1)),
                "summary": summary_match.group(1) if summary_match else "Evaluation completed",
                "strengths": ["Code demonstrates understanding"],
                "issues": ["See detailed feedback"],
                "verdict": verdict_match.group(1),
                "complexity": "MEDIUM",
                "confidence": "MEDIUM"
            }
    except:
        pass
    
    # Strategy 5: Return default FAIL if nothing works
    print(f"All parsing strategies failed. Raw response: {raw_response[:500]}")
    return {
        "score": 50,
        "summary": "Evaluation incomplete due to parsing error",
        "strengths": ["Submission received"],
        "issues": ["Unable to fully evaluate"],
        "verdict": "FAIL",
        "complexity": "LOW",
        "confidence": "LOW"
    }

def update_dynamodb(submission_id, eval_result, code_status):
    table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    
    if code_status == "COMPLETE":
        master_status = "CODE_EVALUATED"
    else:
        master_status = "CODE_SUBMITTED"
    
    table.update_item(
        Key={"submission_id": submission_id},
        UpdateExpression="""SET
            #st = :master_status,
            code_status = :cs,
            code_score = :score,
            code_summary = :summary,
            code_strengths = :strengths,
            code_issues = :issues,
            code_verdict = :verdict,
            code_complexity = :complexity,
            code_confidence = :confidence,
            updated_at = :ts
        """,
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":master_status": master_status,
            ":cs": code_status,
            ":score": eval_result.get("score", 0),
            ":summary": eval_result.get("summary", ""),
            ":strengths": eval_result.get("strengths", []),
            ":issues": eval_result.get("issues", []),
            ":verdict": eval_result.get("verdict", "FAIL"),
            ":complexity": eval_result.get("complexity", "LOW"),
            ":confidence": eval_result.get("confidence", "LOW"),
            ":ts": timestamp
        }
    )
    print(f"Updated submission {submission_id}: status={master_status}, code_status={code_status}")
    
    if code_status == "COMPLETE":
        response = table.get_item(Key={"submission_id": submission_id})
        item = response.get("Item", {})
        
        if item.get("resume_status") == "COMPLETE":
            code_score = eval_result.get("score", 0)
            resume_score = int(item.get("resume_score", 0))
            avg_score = (code_score + resume_score) / 2
            
            code_verdict = eval_result.get("verdict", "FAIL")
            resume_verdict = item.get("resume_verdict", "REJECT")
            
            if avg_score >= 60 and code_verdict == "PASS" and resume_verdict == "SHORTLIST":
                final = "SHORTLISTED"
            else:
                final = "REJECTED"
            
            table.update_item(
                Key={"submission_id": submission_id},
                UpdateExpression="SET final_status = :fs, final_score = :fs_score, #st = :completed, updated_at = :ts2",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":fs": final,
                    ":fs_score": int(avg_score),
                    ":completed": "COMPLETED",
                    ":ts2": datetime.now(tz=timezone.utc).isoformat()
                }
            )
            print(f"Final decision for {submission_id}: {final} (avg: {avg_score}, code: {code_verdict}, resume: {resume_verdict})")

def lambda_handler(event, context):
    print(f"Code eval invoked with {len(event['Records'])} records")
    for record in event["Records"]:
        body = json.loads(record["body"])
        submission_id = body["submission_id"]
        code_s3_key = body["code_s3_key"]
        candidate_name = body["candidate_name"]
        job_id = body.get("job_id", "default")
        questions = body.get("coding_questions", [])

        print(f"Evaluating code for submission: {submission_id}, job_id: {job_id}")
        try:
            s3_response = s3.get_object(Bucket=os.environ["S3_BUCKET"], Key=code_s3_key)
            code_content = s3_response["Body"].read().decode("utf-8")
            code_answers = json.loads(code_content)

            job_config = get_job_config(job_id)
            if not job_config:
                job_config = {"job_role": body.get("job_role", "Software Engineer")}

            ollama_url = get_ollama_url()
            prompt = build_code_prompt(code_answers, questions, job_config, candidate_name)
            raw_response = call_ollama(ollama_url, prompt)
            print(f"LLM raw response length: {len(raw_response)}")

            eval_result = parse_llm_response(raw_response)
            print(f"Parsed eval: score={eval_result.get('score')}, verdict={eval_result.get('verdict')}")

            update_dynamodb(submission_id, eval_result, "COMPLETE")
            print(f"Code evaluation complete for {submission_id}")

        except Exception as e:
            print(f"Code eval failed for {submission_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            update_dynamodb(submission_id, {}, "FAILED")
