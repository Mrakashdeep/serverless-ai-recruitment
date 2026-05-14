#!/usr/bin/env python3
"""
JWT Token Generator for Serverless Recruitment System
Generates HS256 signed JWT tokens for testing API Gateway authentication
"""
import hmac
import hashlib
import base64
import json
import time
import sys

JWT_SECRET = "mtech-iitpatna-recruitment-secret-2026"

def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

def generate_jwt(subject="recruiter", scope="submit read", expiry_hours=24):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "scope": scope,
        "iat": int(time.time()),
        "exp": int(time.time()) + (expiry_hours * 3600),
        "iss": "serverless-recruitment-system"
    }

    header_b64 = base64url_encode(json.dumps(header))
    payload_b64 = base64url_encode(json.dumps(payload))
    signing_input = f"{header_b64}.{payload_b64}"

    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256
    ).digest()

    token = f"{signing_input}.{base64url_encode(signature)}"
    return token, payload

if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "recruiter"
    token, payload = generate_jwt(subject=subject)
    print(f"\nGenerated JWT Token:")
    print(f"{'='*60}")
    print(token)
    print(f"{'='*60}")
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    print(f"\nExpires: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(payload['exp']))}")
    print(f"\nExport command:")
    print(f"export JWT_TOKEN='{token}'")
