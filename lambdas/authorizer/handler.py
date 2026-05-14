import json
import boto3
import hmac
import hashlib
import base64
import os
from datetime import datetime, timezone

def get_jwt_secret():
    client = boto3.client("secretsmanager", region_name=os.environ["AWS_REGION"])
    response = client.get_secret_value(SecretId=os.environ["JWT_SECRET_ARN"])
    secret = json.loads(response["SecretString"])
    return secret["jwt_secret"]

def decode_jwt(token, secret):
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT structure")

    header_b64, payload_b64, signature_b64 = parts

    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    ).rstrip(b"=").decode()

    if not hmac.compare_digest(expected_sig, signature_b64):
        raise ValueError("Invalid JWT signature")

    # Decode payload
    padding = 4 - len(payload_b64) % 4
    payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * padding)
    payload = json.loads(payload_json)

    # Check expiration
    if "exp" in payload:
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        if datetime.now(tz=timezone.utc) > exp:
            raise ValueError("JWT has expired")

    return payload

def generate_policy(principal_id, effect, resource, context=None):
    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": resource
            }]
        }
    }
    if context:
        policy["context"] = context
    return policy

def lambda_handler(event, context):
    print(f"Authorizer invoked: {json.dumps(event)}")

    token = event.get("authorizationToken", "")
    method_arn = event.get("methodArn", "")

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        secret = get_jwt_secret()
        payload = decode_jwt(token, secret)
        print(f"JWT valid for principal: {payload.get('sub', 'unknown')}")
        return generate_policy(
            principal_id=payload.get("sub", "user"),
            effect="Allow",
            resource=method_arn,
            context={"sub": str(payload.get("sub", "")), "scope": str(payload.get("scope", ""))}
        )
    except Exception as e:
        print(f"Authorization failed: {str(e)}")
        return generate_policy(
            principal_id="unauthorized",
            effect="Deny",
            resource=method_arn
        )
