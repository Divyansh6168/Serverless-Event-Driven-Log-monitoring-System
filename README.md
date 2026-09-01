# PayTrack: Serverless Event-Driven Log Monitoring & Analytics System

An end-to-end, cost-optimized, and production-ready **Serverless Log Monitoring Infrastructure** built on AWS. This system intercepts application logs in real-time, isolates critical faults via automated pipelines, alerts engineering teams instantly, and exposes a secure browser-based analytical dashboard for developers.

---

## 🏗️ Architecture & Component Ecosystem

The production pipeline enforces absolute separation of concerns, adhering strictly to the principles of **least privilege security** and **on-demand resource allocation**:

```text
[ Local Script/App ] ──(Pushes Raw Logs)──> [ CloudWatch Logs ] 
                                                   │
                                     (CRITICAL Subscription Filter Pattern)
                                                   │
                                                   ▼
[ Amazon SNS Email ] <──(Alerts If CRITICAL)── [ Lambda: Log Processor ] ──> [ DynamoDB Archive ]
                                                                                   │
                                                                             (Reads Last 20)
                                                                                   │
[ Web Browser View ] <──(Returns HTML UI)───── [ API Gateway + Lambda ] <──────────┘
```

---

## 🚀 Deployment Guide

### 1. Set Up SNS Email Alerts
1. Navigate to the **Amazon SNS Console** and create a new **Standard** topic named `PayTrackCriticalAlerts`.
2. Open the topic details and select **Create subscription**.
   * **Protocol:** `Email`
   * **Endpoint:** Your engineer email address.
3. ⚠️ **Critical Validation Step:** Check your email for a message from AWS Notifications and click **Confirm subscription**.
4. Copy the **Topic ARN** from the SNS dashboard for the next step.

### 2. Deploy the Log Processor Lambda Engine
This function parses log streams, logs entries to DynamoDB, and alerts teams if anomalies match security definitions.

1. Open the **AWS Lambda Console** and create a function named `PayTrackLogProcessor` using **Python 3.12**.
2. Attach your custom Lambda Execution Role with permissions for CloudWatch Logs, DynamoDB, and SNS.
3. Deploy the following code, replacing the `SNS_TOPIC_ARN` variable:

```python
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

```

### 3. Link CloudWatch to Lambda via Subscription Filters
1. In the **CloudWatch Console**, create a Log group named `/paytrack/application-logs`.
2. Go to the **Subscription filters** tab and click **Create Lambda subscription filter**.
3. Set the Destination to `PayTrackLogProcessor`.
4. Set the Log format to **Raw data**.
5. Set the Subscription filter pattern to `CRITICAL` (case-sensitive) and name it `CriticalErrorFilter`.
6. Click **Start streaming**.

### 4. Deploy the Query API & HTML Dashboard
This microservice serves a responsive HTML monitoring dashboard for developers.

1. Create a new Lambda function named `PayTrackQueryLogs` (Python 3.12).
2. Deploy the following presentation code:

```python
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

```
3. Open **API Gateway** and create a **REST API**.
4. Create a Resource path `/logs` and add a **GET** method.
5. Enable **Lambda Proxy Integration** and map it to `PayTrackQueryLogs`.
6. Deploy the API to a stage (e.g., `dev`) and copy the **Invoke URL**.

---

## 🧪 Testing the Pipeline

To verify the system captures data, isolates critical logs, routes alerts, and updates the dashboard, run the standalone simulator script locally.

1. Save the following code as `log_simulator.py`:

```python
import boto3
import time
import random
import uuid
from datetime import datetime, timezone

client = boto3.client('logs', region_name='ap-south-1')
LOG_GROUP = '/paytrack/application-logs'
LOG_STREAM = 'simulator-stream'

try:
    client.create_log_group(logGroupName=LOG_GROUP)
except client.exceptions.ResourceAlreadyExistsException:
    pass

try:
    client.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
except client.exceptions.ResourceAlreadyExistsException:
    pass

log_levels = ['INFO', 'WARNING', 'CRITICAL']
error_types = ['PaymentFailure', 'AuthBreach', 'TransactionTimeout', 'DatabaseError']

def push_log():
    severity = random.choice(log_levels)
    error_type = random.choice(error_types)
    timestamp_str = datetime.now(timezone.utc).isoformat()
    message = f"{severity} | {error_type} | Transaction ID {uuid.uuid4()} failed at {timestamp_str}"
    
    client.put_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=LOG_STREAM,
        logEvents=[{
            'timestamp': int(time.time() * 1000),
            'message': message
        }]
    )
    print(f"Pushed log: {message}")

print("🚀 Commencing transaction log simulator streams (20 iterations)...")
for _ in range(20):
    push_log()
    time.sleep(2)
```

2. Run the script: `python3 log_simulator.py`
3. **Verify:** Check your email inbox for alerts on `CRITICAL` records, and navigate to your API Gateway URL (`https://{api-id}.execute-api.{region}.amazonaws.com/dev/logs`) in a web browser to view the real-time HTML reporting dashboard.
