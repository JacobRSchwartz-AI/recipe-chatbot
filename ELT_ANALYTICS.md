# ELT Analytics & Data Pipeline - Recipe Chatbot

This document outlines a pragmatic data pipeline for analyzing user cooking behavior and generating insights for stakeholders.

## Architecture Overview

We use a simple event-driven pipeline that captures conversation data and generates analytics without over-engineering:

**Data Flow**: Application → DynamoDB → S3 Data Lake → Athena → QuickSight

This approach avoids expensive services like Redshift and complex ETL tools until we actually need them.

## Data Collection Strategy

### Conversation Tracking

```python
from datetime import datetime
from typing import List, Dict, Optional
import boto3
import json

class ConversationTracker:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('recipe-conversations')
        self.s3 = boto3.client('s3')
    
    async def track_conversation(self, conversation_id: str, user_id: str, 
                                message: str, role: str, metadata: dict = {}):
        """Track conversation messages in DynamoDB."""
        
        # Store minimal data for analytics
        item = {
            'conversation_id': conversation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'role': role,
            'message': message[:500],  # Truncate long messages
            'metadata': metadata
        }
        
        # Also track analytics-specific fields
        if role == "assistant" and "recipe" in message.lower():
            item['has_recipe'] = True
            item['recipe_name'] = self._extract_recipe_name(message)
        
        self.table.put_item(Item=item)
        
        # Batch write to S3 every hour for analytics
        if datetime.utcnow().minute == 0:
            await self._batch_to_s3()
    
    def _extract_recipe_name(self, message: str) -> Optional[str]:
        """Simple recipe name extraction."""
        # Basic pattern matching - no ML needed for MVP
        import re
        patterns = [
            r'recipe for (.+?)(?:\.|,|!|\?|$)',
            r'how to make (.+?)(?:\.|,|!|\?|$)',
            r'cooking (.+?)(?:\.|,|!|\?|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1).strip()
        return None
```

### Data Schema

```python
# DynamoDB table configuration (simple single table design)
DYNAMODB_CONFIG = {
    "TableName": "recipe-conversations",
    "KeySchema": [
        {"AttributeName": "conversation_id", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"}
    ],
    "BillingMode": "PAY_PER_REQUEST",  # No need to provision capacity
    "StreamSpecification": {
        "StreamEnabled": True,
        "StreamViewType": "NEW_IMAGE"
    },
    "TimeToLiveSpecification": {
        "AttributeName": "ttl",
        "Enabled": True  # Auto-cleanup after 90 days
    }
}
```

## Storage & Analytics

### S3 Data Lake Structure

Keep it simple with daily partitions:

```
s3://recipe-chatbot-analytics/
├── conversations/
│   └── year=2025/month=01/day=15/
│       └── conversations-2025-01-15.json
└── aggregated/
    └── daily/
        └── year=2025/month=01/day=15/
            └── daily-metrics-2025-01-15.json
```

### Daily Aggregation Lambda

```python
import boto3
import json
from datetime import datetime, timedelta
from collections import defaultdict

def lambda_daily_aggregation(event, context):
    """Simple daily aggregation Lambda function."""
    
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    table = dynamodb.Table('recipe-conversations')
    
    # Get yesterday's data
    yesterday = datetime.utcnow() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    
    # Query conversations for the day
    response = table.query(
        IndexName='date-index',
        KeyConditionExpression='date_str = :date',
        ExpressionAttributeValues={':date': date_str}
    )
    
    # Simple aggregations
    metrics = {
        'date': date_str,
        'total_conversations': 0,
        'unique_users': set(),
        'recipes_discussed': defaultdict(int),
        'total_messages': 0,
        'avg_conversation_length': 0
    }
    
    conversations = defaultdict(list)
    
    for item in response['Items']:
        conv_id = item['conversation_id']
        conversations[conv_id].append(item)
        metrics['total_messages'] += 1
        metrics['unique_users'].add(item.get('user_id'))
        
        if item.get('recipe_name'):
            metrics['recipes_discussed'][item['recipe_name']] += 1
    
    # Calculate final metrics
    metrics['total_conversations'] = len(conversations)
    metrics['unique_users'] = len(metrics['unique_users'])
    metrics['avg_conversation_length'] = metrics['total_messages'] / max(metrics['total_conversations'], 1)
    
    # Convert to JSON-serializable format
    metrics['recipes_discussed'] = dict(metrics['recipes_discussed'])
    
    # Save to S3
    s3_key = f"aggregated/daily/year={yesterday.year}/month={yesterday.month:02d}/day={yesterday.day:02d}/daily-metrics-{date_str}.json"
    
    s3.put_object(
        Bucket='recipe-chatbot-analytics',
        Key=s3_key,
        Body=json.dumps(metrics),
        ContentType='application/json'
    )
    
    return {'statusCode': 200, 'metrics': metrics}
```

## Analytics with Athena

### Create Athena Tables

```sql
-- Create external table for conversations
CREATE EXTERNAL TABLE IF NOT EXISTS recipe_conversations (
    conversation_id string,
    timestamp string,
    user_id string,
    role string,
    message string,
    has_recipe boolean,
    recipe_name string
)
PARTITIONED BY (
    year int,
    month int,
    day int
)
STORED AS JSON
LOCATION 's3://recipe-chatbot-analytics/conversations/';

-- Create external table for daily metrics
CREATE EXTERNAL TABLE IF NOT EXISTS daily_metrics (
    date string,
    total_conversations int,
    unique_users int,
    recipes_discussed map<string, int>,
    total_messages int,
    avg_conversation_length float
)
PARTITIONED BY (
    year int,
    month int,
    day int
)
STORED AS JSON
LOCATION 's3://recipe-chatbot-analytics/aggregated/daily/';

-- Add partitions (run daily)
MSCK REPAIR TABLE recipe_conversations;
MSCK REPAIR TABLE daily_metrics;
```

### Common Analytics Queries

```sql
-- Weekly recipe popularity
SELECT 
    recipe_name,
    COUNT(*) as mentions,
    COUNT(DISTINCT user_id) as unique_users
FROM recipe_conversations
WHERE year = 2025 
    AND month = 1 
    AND day BETWEEN 8 AND 15
    AND recipe_name IS NOT NULL
GROUP BY recipe_name
ORDER BY mentions DESC
LIMIT 20;

-- User engagement metrics
SELECT 
    date,
    total_conversations,
    unique_users,
    CAST(total_messages AS FLOAT) / total_conversations as avg_messages_per_conversation
FROM daily_metrics
WHERE year = 2025 AND month = 1
ORDER BY date DESC;

-- Recipe diversity by day
SELECT 
    date,
    cardinality(recipes_discussed) as unique_recipes,
    reduce(
        map_values(recipes_discussed), 
        0, 
        (s, x) -> s + x, 
        s -> s
    ) as total_recipe_mentions
FROM daily_metrics
WHERE year = 2025 AND month = 1
ORDER BY date DESC;
```

## QuickSight Dashboard

### Simple Dashboard Setup

1. **Connect QuickSight to Athena**
   - Use Athena as data source
   - Point to the analytics tables

2. **Key Visualizations**
   - Daily active users (line chart)
   - Top 10 recipes this week (bar chart)
   - Average conversation length trend (line chart)
   - Recipe category distribution (pie chart)

3. **Calculated Fields**
   ```sql
   -- Week-over-week growth
   (current_week_users - previous_week_users) / previous_week_users * 100

   -- Recipe completion estimate (simple heuristic)
   CASE 
       WHEN avg_conversation_length > 5 THEN 'High'
       WHEN avg_conversation_length > 3 THEN 'Medium'
       ELSE 'Low'
   END
   ```

## Data Privacy & Compliance

### Simple Privacy Measures

```python
class PrivacyManager:
    def __init__(self):
        self.pii_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
            (r'\b\d{16}\b', '[CARD]')  # Credit card
        ]
    
    def anonymize_message(self, message: str) -> str:
        """Remove PII from messages before analytics."""
        import re
        
        for pattern, replacement in self.pii_patterns:
            message = re.sub(pattern, replacement, message)
        
        return message
    
    def hash_user_id(self, user_id: str) -> str:
        """Create consistent hash for analytics."""
        import hashlib
        
        # Use daily salt so same user has same ID within a day
        daily_salt = datetime.utcnow().strftime('%Y-%m-%d')
        return hashlib.sha256(f"{daily_salt}:{user_id}".encode()).hexdigest()[:16]
```

### Data Retention

- **Conversations**: 90 days (auto-deleted via TTL)
- **Aggregated metrics**: 2 years
- **No PII in analytics data**

## Cost Estimates

Monthly costs for moderate usage (1000 conversations/day):

- **DynamoDB**: ~$5 (on-demand pricing)
- **S3 Storage**: ~$1 (minimal data)
- **Lambda**: ~$1 (daily aggregations)
- **Athena**: ~$5 (assuming 100 queries/month)
- **QuickSight**: $12/user (author), $5/user (reader)
- **Total**: ~$25-50/month

## Key Metrics for Stakeholders

### Usage Metrics
- Daily/Weekly/Monthly active users
- Total conversations
- Average conversation length

### Recipe Insights
- Most popular recipes
- Recipe category distribution
- Seasonal trends

### User Behavior
- Peak usage hours
- User retention (returning users)
- Tool usage (web search, cookware check)

### Business Metrics
- Estimated cooking completion rate
- User satisfaction (based on conversation patterns)
- Feature adoption rates

## Summary

This ELT pipeline provides:

- Simple, cost-effective analytics using AWS managed services
- No complex ETL tools or expensive data warehouses
- Easy to implement and maintain
- Clear upgrade path as data volume grows

The focus is on getting actionable insights quickly rather than building a complex data infrastructure that may never be fully utilized.
