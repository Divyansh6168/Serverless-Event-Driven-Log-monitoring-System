import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PayTrackErrors')

def lambda_handler(event, context):
    response = table.scan(Limit=20)
    items = response.get('Items', [])
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*' # Optional: Allows testing from frontend apps
        },
        'body': json.dumps(items)
    }
