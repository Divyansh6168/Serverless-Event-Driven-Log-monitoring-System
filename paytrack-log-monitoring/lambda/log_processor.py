import json
import boto3
import base64
import gzip
import uuid
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = 'PayTrackErrors'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:476663693226:PayTrackCriticalAlerts'

def lambda_handler(event, context):
    # Decode and decompress the CloudWatch log data
    compressed_payload = base64.b64decode(event['awslogs']['data'])
    payload = gzip.decompress(compressed_payload)
    log_data = json.loads(payload)

    table = dynamodb.Table(TABLE_NAME)

    for log_event in log_data['logEvents']:
        message = log_event['message']

        # Parse log fields (Format: LEVEL | ErrorType | Message)
        parts = message.split('|')
        
        # FIX: Explicitly apply .strip() to clean up trailing/leading spaces from the split strings
        severity = parts[0].strip() if len(parts) > 0 else 'INFO'
        error_type = parts[1].strip() if len(parts) > 1 else 'Unknown'
        error_message = parts[2].strip() if len(parts) > 2 else message
        
        # Modern timezone-aware UTC format
        timestamp = datetime.now(timezone.utc).isoformat()
        log_id = str(uuid.uuid4())

        # Save to DynamoDB
        table.put_item(Item={
            'logId': log_id,
            'timestamp': timestamp,
            'severity': severity,
            'errorType': error_type,
            'message': error_message
        })

        # This evaluation will now correctly result in True
        if severity == 'CRITICAL':
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject='CRITICAL ERROR DETECTED - PayTrack',
                Message=f'Error Type: {error_type}\nMessage: {error_message}\nTimestamp: {timestamp}'
            )

    return {'statusCode': 200, 'body': 'Logs processed successfully'}
