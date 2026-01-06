import json
import boto3 # type: ignore

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CampusIssues')

def lambda_handler(event, context):
    try:
        issue_id = event['pathParameters']['issueId']

        response = table.get_item(
            Key={'issueId': issue_id}
        )

        if 'Item' not in response:
            return {
                "statusCode": 404,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "GET"
                },
                "body": json.dumps({"message": "Issue not found"})
            }

        # Convert Decimal to native Python types for JSON serialization
        item = response['Item']
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET"
            },
            "body": json.dumps(item, default=str)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }