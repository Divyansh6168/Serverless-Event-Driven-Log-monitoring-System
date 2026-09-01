import boto3
import time
import random
import uuid
from datetime import datetime, timezone

client = boto3.client('logs', region_name='ap-south-1')
LOG_GROUP = '/paytrack/application-logs'
LOG_STREAM = 'simulator-stream'

# 1. Safely handle Log Group creation
try:
    client.create_log_group(logGroupName=LOG_GROUP)
    print(f"Successfully created missing Log Group: {LOG_GROUP}")
except client.exceptions.ResourceAlreadyExistsException:
    pass  # Already exists, move on safely

# 2. Safely handle Log Stream creation
try:
    client.create_log_stream(logGroupName=LOG_GROUP, logStreamName=LOG_STREAM)
    print(f"Successfully created Log Stream: {LOG_STREAM}")
except client.exceptions.ResourceAlreadyExistsException:
    pass

log_levels = ['INFO', 'WARNING', 'CRITICAL']
error_types = ['PaymentFailure', 'AuthBreach', 'TransactionTimeout', 'DatabaseError']

def push_log():
    severity = random.choice(log_levels)
    error_type = random.choice(error_types)
    # Using modern timezone-aware UTC datetime
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

for _ in range(20):
    push_log()
    time.sleep(2)
