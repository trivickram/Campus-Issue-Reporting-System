import json
import uuid
import boto3
from datetime import datetime
import os

# SES Configuration - IMPORTANT: Change region to where your SES is verified
SES_REGION = os.environ.get('SES_REGION', 'ap-south-1')  # Change to your SES region

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses', region_name=SES_REGION)

table = dynamodb.Table('CampusIssues')

# Replace with your VERIFIED SES email addresses
# Both must be verified in SES console if in Sandbox mode
SENDER = "rahulkrishnabommu@gmail.com"  # Must be verified in SES
RECEIVER = "rahulbommu123@gmail.com"    # Must be verified in SES (if sandbox mode)

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])

        issue_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Create item with new Phase A fields
        item = {
            'issueId': issue_id,
            'issueType': body['issueType'],
            'description': body['description'],
            'location': body['location'],
            'priority': body.get('priority', 'MEDIUM'),  # NEW: Priority
            'email': body.get('email', ''),  # NEW: User email
            'status': 'OPEN',
            'createdAt': timestamp,
            'statusHistory': [  # NEW: Track status changes
                {
                    'status': 'OPEN',
                    'timestamp': timestamp,
                    'by': 'system'
                }
            ],
            'comments': [],  # NEW: Comments array
            'assignedTo': None  # NEW: Assignment
        }

        # Save to DynamoDB
        table.put_item(Item=item)

        # Send Email Notification to user if provided
        user_email = body.get('email')
        if user_email:
            try:
                priority_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
                ses.send_email(
                    Source=SENDER,
                    Destination={"ToAddresses": [user_email]},
                    Message={
                        "Subject": {
                            "Data": f"Issue Submitted - {issue_id}"
                        },
                        "Body": {
                            "Text": {
                                "Data": (
                                    f"Thank you for reporting the campus issue.\n\n"
                                    f"Issue ID: {issue_id}\n"
                                    f"Priority: {priority_emoji.get(item['priority'], '')} {item['priority']}\n"
                                    f"Type: {body['issueType']}\n"
                                    f"Location: {body['location']}\n"
                                    f"Status: OPEN\n\n"
                                    f"You can track your issue status using the Issue ID.\n"
                                    f"We will notify you of any updates.\n\n"
                                    f"Campus Facilities Management"
                                )
                            }
                        }
                    }
                )
                print(f"User email sent to {user_email}")
            except Exception as e:
                print(f"User email error: {str(e)}")

        # Send Email to Admin via SES
        try:
            priority_emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
            ses.send_email(
                Source=SENDER,
                Destination={"ToAddresses": [RECEIVER]},
                Message={
                    "Subject": {
                        "Data": f"{priority_emoji.get(item['priority'], '')} New {item['priority']} Priority Issue ({issue_id})"
                    },
                    "Body": {
                        "Text": {
                            "Data": (
                                f"New campus issue reported:\n\n"
                                f"Issue ID: {issue_id}\n"
                                f"Priority: {item['priority']}\n"
                                f"Type: {body['issueType']}\n"
                                f"Location: {body['location']}\n"
                                f"Description: {body['description']}\n"
                                f"Reported by: {user_email if user_email else 'Anonymous'}\n"
                                f"Status: OPEN\n"
                                f"Created At: {timestamp}\n\n"
                                f"Please login to admin panel to manage this issue."
                            )
                        }
                    }
                }
            )
            print(f"Admin email sent successfully for issue {issue_id}")
        except Exception as email_error:
            print(f"Admin email failed: {str(email_error)}")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST"
            },
            "body": json.dumps({
                "message": "Issue reported successfully",
                "issueId": issue_id,
                "priority": item['priority']
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }