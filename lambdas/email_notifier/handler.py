import json
import os
import smtplib
import boto3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_smtp_credentials():
    """Fetch SMTP credentials from Secrets Manager"""
    try:
        client = boto3.client('secretsmanager', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
        response = client.get_secret_value(SecretId='serverless-recruitment/smtp-credentials')
        creds = json.loads(response['SecretString'])
        return creds.get('user'), creds.get('pass')
    except Exception as e:
        print(f"No SMTP credentials: {e}")
        return None, None

def lambda_handler(event, context):
    smtp_user, smtp_pass = get_smtp_credentials()
    
    to_email = event.get('to')
    subject = event.get('subject')
    email_type = event.get('type')
    data = event.get('data', {})
    
    if not smtp_user or not smtp_pass:
        print(f"� [MOCK EMAIL] To: {to_email}")
        print(f"� [MOCK EMAIL] Subject: {subject}")
        print(f"� [MOCK EMAIL] Type: {email_type}")
        return {"statusCode": 200, "body": "Email logged (mock mode)"}
    
    try:
        if email_type == 'questions_ready':
            body = build_questions_ready_email(data)
        elif email_type == 'results_ready':
            body = build_results_ready_email(data)
        else:
            body = "<p>Your application has been updated.</p>"
        
        msg = MIMEMultipart('alternative')
        msg['From'] = os.environ.get('FROM_EMAIL', 'noreply@recruitment.system')
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp-relay.brevo.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        print(f"✓ Email sent to {to_email}")
        return {"statusCode": 200, "body": "Email sent"}
    except Exception as e:
        print(f"Email error: {str(e)}")
        return {"statusCode": 500, "body": str(e)}

def build_questions_ready_email(data):
    candidate_name = data.get('candidate_name', 'Candidate')
    submission_id = data.get('submission_id', '')
    
    return f"""<html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">� Coding Challenge Ready!</h1>
    </div>
    <div style="padding: 30px; background: #f9fafb;">
        <p>Hi <strong>{candidate_name}</strong>,</p>
        <p>Your resume has been reviewed and you've been advanced to the coding round!</p>
        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
            <p style="margin: 0;"><strong>⏱️ Important:</strong> You have 30 minutes once you start.</p>
        </div>
        <p>Best of luck!</p>
    </div>
    </body></html>"""

def build_results_ready_email(data):
    candidate_name = data.get('candidate_name', 'Candidate')
    final_status = data.get('final_status', 'PENDING')
    final_score = data.get('final_score', 0)
    
    color = '#10b981' if final_status == 'SHORTLISTED' else '#6b7280'
    emoji = '�' if final_status == 'SHORTLISTED' else '�'
    
    return f"""<html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: {color}; padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{emoji} Application Results</h1>
    </div>
    <div style="padding: 30px; background: #f9fafb;">
        <p>Hi <strong>{candidate_name}</strong>,</p>
        <div style="background: white; border: 2px solid {color}; border-radius: 8px; padding: 20px; text-align: center;">
            <p style="font-size: 18px; font-weight: bold; color: {color};">Status: {final_status}</p>
            <p style="font-size: 24px; font-weight: bold;">Score: {final_score}/100</p>
        </div>
        <p>{'Congratulations! We will be in touch soon.' if final_status == 'SHORTLISTED' else 'Thank you for your interest.'}</p>
    </div>
    </body></html>"""
