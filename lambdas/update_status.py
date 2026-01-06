import json
import boto3 # type: ignore

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
table = dynamodb.Table('CampusIssues')

# Replace with your verified email addresses
SENDER = "rahulkrishnabommu@gmail.com"
RECEIVER = "rahulbommu123@gmail.com"

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        issue_id = body['issueId']
        new_status = body['status']

        # Update status in DynamoDB
        response = table.update_item(
            Key={'issueId': issue_id},
            UpdateExpression="SET #s = :s",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":s": new_status},
            ReturnValues="ALL_NEW"
        )

        # Send Email Notification via SES
        try:
            ses.send_email(
                Source=SENDER,
                Destination={"ToAddresses": [RECEIVER]},
                Message={
                    "Subject": {
                        "Data": f"Issue Status Updated ({issue_id})"
                    },
                    "Body": {
                        "Text": {
                            "Data": (
                                f"Issue ID: {issue_id}\n"
                                f"New Status: {new_status}\n"
                                f"Type: {response['Attributes'].get('issueType', 'N/A')}\n"
                                f"Location: {response['Attributes'].get('location', 'N/A')}\n"
                                f"Description: {response['Attributes'].get('description', 'N/A')}"
                            )
                        }
                    }
                }
            )
            print(f"Status update email sent successfully for issue {issue_id}")
        except Exception as email_error:
            print(f"Email sending failed: {str(email_error)}")
            # Continue execution - email failure shouldn't break the flow

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "PUT"
            },
            "body": json.dumps({
                "message": "Status updated and email sent",
                "issueId": issue_id,
                "newStatus": new_status
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }