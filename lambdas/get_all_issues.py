import json
import boto3 # type: ignore
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('CampusIssues')

# Helper function to convert Decimal to native Python types
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    try:
        # Scan the entire table to get all issues
        response = table.scan()
        items = response.get('Items', [])
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # Sort by createdAt descending (newest first)
        items.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET"
            },
            "body": json.dumps({
                "issues": items,
                "count": len(items)
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }
