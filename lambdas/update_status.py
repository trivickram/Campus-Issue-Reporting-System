import json
import boto3 # type: ignore
from datetime import datetime

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
        assigned_to = body.get('assignedTo')  # NEW: Assignment
        comment_text = body.get('comment')  # NEW: Comment
        updated_by = body.get('updatedBy', 'admin')  # NEW: Track who updated
        timestamp = datetime.utcnow().isoformat()

        # Get current issue to access statusHistory and comments
        current_issue = table.get_item(Key={'issueId': issue_id})
        if 'Item' not in current_issue:
            return {
                "statusCode": 404,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"message": "Issue not found"})
            }
        
        item = current_issue['Item']
        
        # Prepare status history update
        status_history = item.get('statusHistory', [])
        status_history.append({
            'status': new_status,
            'timestamp': timestamp,
            'by': updated_by
        })
        
        # Prepare comments update
        comments = item.get('comments', [])
        if comment_text:
            comments.append({
                'text': comment_text,
                'timestamp': timestamp,
                'by': updated_by
            })

        # Build update expression dynamically
        update_expr = "SET #s = :s, statusHistory = :sh, comments = :c"
        expr_attr_names = {"#s": "status"}
        expr_attr_values = {
            ":s": new_status,
            ":sh": status_history,
            ":c": comments
        }
        
        # Add assignment if provided
        if assigned_to:
            update_expr += ", assignedTo = :a"
            expr_attr_values[":a"] = assigned_to

        # Update status in DynamoDB with all new fields
        response = table.update_item(
            Key={'issueId': issue_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )

        updated_item = response['Attributes']

        # Send Email Notification to USER if email exists
        user_email = updated_item.get('email')
        if user_email:
            try:
                email_body = (
                    f"Your issue has been updated:\n\n"
                    f"Issue ID: {issue_id}\n"
                    f"New Status: {new_status}\n"
                )
                if assigned_to:
                    email_body += f"Assigned To: {assigned_to.replace('_', ' ')}\n"
                if comment_text:
                    email_body += f"\nUpdate from admin:\n{comment_text}\n"
                email_body += (
                    f"\nType: {updated_item.get('issueType', 'N/A')}\n"
                    f"Location: {updated_item.get('location', 'N/A')}\n"
                    f"Priority: {updated_item.get('priority', 'N/A')}\n\n"
                    f"You can track your issue using the Issue ID.\n"
                    f"Campus Facilities Management"
                )
                
                ses.send_email(
                    Source=SENDER,
                    Destination={"ToAddresses": [user_email]},
                    Message={
                        "Subject": {"Data": f"Issue Update - {issue_id}"},
                        "Body": {"Text": {"Data": email_body}}
                    }
                )
                print(f"User notification sent to {user_email}")
            except Exception as e:
                print(f"User email error: {str(e)}")

        # Send Email Notification to ADMIN
        try:
            admin_body = (
                f"Issue status updated:\n\n"
                f"Issue ID: {issue_id}\n"
                f"New Status: {new_status}\n"
                f"Updated By: {updated_by}\n"
            )
            if assigned_to:
                admin_body += f"Assigned To: {assigned_to.replace('_', ' ')}\n"
            if comment_text:
                admin_body += f"Comment Added: {comment_text}\n"
            admin_body += (
                f"\nType: {updated_item.get('issueType', 'N/A')}\n"
                f"Location: {updated_item.get('location', 'N/A')}\n"
                f"Priority: {updated_item.get('priority', 'N/A')}\n"
                f"Description: {updated_item.get('description', 'N/A')}"
            )
            
            ses.send_email(
                Source=SENDER,
                Destination={"ToAddresses": [RECEIVER]},
                Message={
                    "Subject": {"Data": f"Issue Status Updated ({issue_id})"},
                    "Body": {"Text": {"Data": admin_body}}
                }
            )
            print(f"Admin email sent for issue {issue_id}")
        except Exception as email_error:
            print(f"Admin email failed: {str(email_error)}")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "PUT"
            },
            "body": json.dumps({
                "message": "Status updated successfully",
                "issueId": issue_id,
                "newStatus": new_status,
                "assignedTo": assigned_to,
                "commentAdded": bool(comment_text)
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }