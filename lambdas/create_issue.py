import json
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

table = dynamodb.Table('CampusIssues')

# Replace with your verified email addresses
SENDER = "your_verified_email@gmail.com"
RECEIVER = "your_verified_email@gmail.com"

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])

        issue_id = str(uuid.uuid4())

        item = {
            'issueId': issue_id,
            'issueType': body['issueType'],
            'description': body['description'],
            'location': body['location'],
            'status': 'OPEN',
            'createdAt': datetime.utcnow().isoformat()
        }

        # Save to DynamoDB
        table.put_item(Item=item)

        # Send Email Notification via SES
        try:
            ses.send_email(
                Source=SENDER,
                Destination={"ToAddresses": [RECEIVER]},
                Message={
                    "Subject": {
                        "Data": f"New Campus Issue Reported ({issue_id})"
                    },
                    "Body": {
                        "Text": {
                            "Data": (
                                f"Issue ID: {issue_id}\n"
                                f"Type: {body['issueType']}\n"
                                f"Location: {body['location']}\n"
                                f"Description: {body['description']}\n"
                                f"Status: OPEN\n"
                                f"Created At: {item['createdAt']}"
                            )
                        }
                    }
                }
            )
            print(f"Email sent successfully for issue {issue_id}")
        except Exception as email_error:
            print(f"Email sending failed: {str(email_error)}")
            # Continue execution - email failure shouldn't break the flow

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "POST"
            },
            "body": json.dumps({
                "message": "Issue reported successfully",
                "issueId": issue_id
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }