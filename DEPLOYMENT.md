# AWS Deployment Guide - Recipe Chatbot

This document outlines the production deployment strategy for the Recipe Chatbot application using AWS services, with a focus on AWS ECS Fargate as the primary compute platform.

## Table of Contents
- [Compute Choice: AWS ECS with Fargate](#compute-choice-aws-ecs-with-fargate)
- [Architecture Overview](#architecture-overview)
- [Secret Management](#secret-management)
- [Observability & Monitoring](#observability--monitoring)
- [Scaling & Networking](#scaling--networking)
- [Deployment Process](#deployment-process)
- [Cost Optimization](#cost-optimization)
- [Security Considerations](#security-considerations)

## Compute Choice: AWS ECS with Fargate

### Why ECS Fargate?

**ECS Fargate** was selected as the primary compute platform over other AWS options for the following reasons:

#### ✅ **Perfect Docker Alignment**
- Our application is already containerized with Docker and Docker Compose
- ECS task definitions map directly to our existing container configuration
- No refactoring required - containers run identically in development and production

#### ✅ **Serverless Container Management**
- No EC2 instances to manage, patch, or scale
- AWS handles the underlying infrastructure completely
- Automatic capacity provisioning and scaling

#### ✅ **Cost Efficiency**
- Pay only for running containers (CPU and memory usage)
- Automatic scaling to zero during low traffic periods
- No idle server costs compared to EC2-based solutions

#### ✅ **Production-Ready Features**
- Built-in load balancing with Application Load Balancer (ALB)
- Zero-downtime rolling deployments
- Health checks and automatic container replacement
- Service discovery for inter-service communication

#### ✅ **Operational Simplicity**
- Significantly less operational overhead than Kubernetes (EKS)
- More control and flexibility than Lambda for long-running processes
- Native AWS service integration (CloudWatch, Secrets Manager, etc.)

### Alternative Compute Options Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **AWS Lambda** | True serverless, infinite scale | Cold starts hurt LLM performance, 15min timeout, complex streaming implementation | ❌ Not suitable for LLM workloads |
| **EKS (Kubernetes)** | Industry standard, powerful orchestration | High complexity, management overhead, cost | ❌ Over-engineered for this scale |
| **EC2 + Docker** | Full control, familiar setup | Server management, single point of failure, manual scaling | ❌ Too much operational burden |
| **App Runner** | Ultra-simple deployment | Limited customization, newer service | ⚠️ Good alternative but less mature |

## Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│   Route 53  │────│     ALB     │────│   ECS Cluster   │
│  (DNS)      │    │ (Load Bal.) │    │   (Fargate)     │
└─────────────┘    └─────────────┘    └─────────────────┘
                           │                    │
                           │           ┌────────┴────────┐
                           │           │                 │
                           │    ┌──────▼──────┐  ┌──────▼──────┐
                           │    │   Backend   │  │  Frontend   │
                           │    │  Service    │  │  Service    │
                           │    │ (Port 8000) │  │ (Port 3000) │
                           │    └─────────────┘  └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   Secrets   │
                    │  Manager    │
                    └─────────────┘
                           │
                    ┌──────▼──────┐
                    │ CloudWatch  │
                    │    Logs     │
                    └─────────────┘
```

### Core Components

- **ECS Cluster**: Container orchestration platform
- **ECS Services**: Backend (FastAPI) and Frontend (Next.js) services
- **Application Load Balancer**: Traffic distribution and SSL termination
- **Route 53**: DNS management and health checks
- **ECR**: Private container registry for Docker images
- **Secrets Manager**: Secure storage for API keys and sensitive data
- **CloudWatch**: Centralized logging and monitoring

## Secret Management

### AWS Secrets Manager (Primary Choice)

**Why Secrets Manager over SSM Parameter Store?**

| Feature | Secrets Manager | SSM Parameter Store |
|---------|-----------------|-------------------- |
| **Automatic Rotation** | ✅ Built-in rotation for DB passwords, API keys | ❌ Manual rotation only |
| **Encryption** | ✅ Always encrypted at rest and in transit | ⚠️ Standard parameters not encrypted |
| **Cross-Region Replication** | ✅ Automatic replication | ❌ Manual setup required |
| **Fine-Grained Access** | ✅ Resource-based policies | ✅ IAM policies only |
| **Cost** | ❌ $0.40/secret/month + API calls | ✅ Free tier, then $0.05/1K API calls |
| **Integration** | ✅ Native ECS integration | ✅ Native ECS integration |

**Decision**: Use **Secrets Manager** for sensitive secrets (API keys) and **SSM Parameter Store** for non-sensitive configuration.

### Secret Configuration

```json
{
  "secrets": {
    "openai-api-key": {
      "arn": "arn:aws:secretsmanager:us-east-1:account:secret:recipe-chatbot/openai-key",
      "description": "OpenAI API key for LLM operations",
      "rotation": "manual"
    },
    "serp-api-key": {
      "arn": "arn:aws:secretsmanager:us-east-1:account:secret:recipe-chatbot/serp-key",
      "description": "SERP API key for web search functionality",
      "rotation": "manual"
    }
  },
  "parameters": {
    "environment": "production",
    "log-level": "INFO",
    "cors-origins": "https://recipe-chatbot.example.com"
  }
}
```

### ECS Task Definition Integration

```json
{
  "secrets": [
    {
      "name": "OPENAI_API_KEY",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:account:secret:recipe-chatbot/openai-key:SecretString:api_key"
    },
    {
      "name": "SERP_API_KEY", 
      "valueFrom": "arn:aws:secretsmanager:us-east-1:account:secret:recipe-chatbot/serp-key:SecretString:api_key"
    }
  ],
  "environment": [
    {
      "name": "ENVIRONMENT",
      "value": "production"
    }
  ]
}
```

## Observability & Monitoring

### CloudWatch Integration

#### **Structured Logging Strategy**

```python
# Backend logging configuration
import structlog
import json

logger = structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

#### **Log Groups Structure**

```
/aws/ecs/recipe-chatbot/backend    # Backend application logs
/aws/ecs/recipe-chatbot/frontend   # Frontend application logs  
/aws/ecs/recipe-chatbot/nginx      # Load balancer access logs
```

#### **Custom Metrics**

```python
# Key business metrics to track
CUSTOM_METRICS = {
    "chat_requests_total": "Number of chat requests processed",
    "cooking_queries_ratio": "Percentage of cooking vs non-cooking queries", 
    "tool_usage_count": "Frequency of each tool (web_search, cookware_check)",
    "response_time_p95": "95th percentile response time",
    "llm_token_usage": "OpenAI API token consumption",
    "error_rate": "Application error rate by endpoint"
}
```

### OpenTelemetry Integration

#### **Distributed Tracing Setup**

```python
# requirements.txt additions
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-requests==0.42b0
opentelemetry-exporter-otlp==1.21.0

# Tracing configuration
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracing
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:14250")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
```

#### **Trace Correlation**

```python
# LangGraph workflow tracing
@trace.get_tracer(__name__).start_as_current_span("langgraph_workflow")
def run_workflow(user_message: str):
    with trace.get_tracer(__name__).start_as_current_span("query_classification"):
        classification = classify_query(user_message)
    
    with trace.get_tracer(__name__).start_as_current_span("tool_execution"):
        if classification.needs_web_search:
            search_results = web_search(user_message)
    
    return generate_response(classification, search_results)
```

### Monitoring Dashboard

```yaml
# CloudWatch Dashboard Configuration
Dashboard:
  Widgets:
    - ServiceHealth:
        metrics: ["CPUUtilization", "MemoryUtilization", "HealthyHostCount"]
        period: 300
    - BusinessMetrics:
        metrics: ["ChatRequestsPerMinute", "CookingQueryRatio", "ToolUsageDistribution"]
        period: 60
    - ErrorTracking:
        metrics: ["HTTPErrorRate", "LLMFailureRate", "ToolTimeouts"]
        period: 60
    - Performance:
        metrics: ["ResponseTimeP95", "TokensPerSecond", "ConcurrentConnections"]
        period: 300

Alarms:
  HighErrorRate:
    threshold: 5%
    period: 300
    notification: "recipe-chatbot-alerts"
  HighResponseTime:
    threshold: 5000ms
    period: 300
    notification: "recipe-chatbot-alerts"
  LowHealthyHosts:
    threshold: 1
    period: 60
    notification: "recipe-chatbot-critical"
```

## Scaling & Networking

### Auto Scaling Configuration

#### **ECS Service Auto Scaling**

```json
{
  "scalingPolicies": {
    "backend": {
      "targetTrackingPolicies": [
        {
          "targetValue": 70.0,
          "scaleOutCooldown": 300,
          "scaleInCooldown": 300,
          "metricType": "ECSServiceAverageCPUUtilization"
        },
        {
          "targetValue": 80.0,
          "scaleOutCooldown": 300,
          "scaleInCooldown": 300,
          "metricType": "ECSServiceAverageMemoryUtilization"
        }
      ],
      "minCapacity": 2,
      "maxCapacity": 20
    },
    "frontend": {
      "targetTrackingPolicies": [
        {
          "targetValue": 70.0,
          "scaleOutCooldown": 300,
          "scaleInCooldown": 300,
          "metricType": "ECSServiceAverageCPUUtilization"
        }
      ],
      "minCapacity": 2,
      "maxCapacity": 10
    }
  }
}
```

#### **Custom Scaling Metrics**

```python
# Custom CloudWatch metric for LLM queue depth
def publish_llm_queue_metric(queue_depth: int):
    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='RecipeChatbot/LLM',
        MetricData=[
            {
                'MetricName': 'QueueDepth',
                'Value': queue_depth,
                'Unit': 'Count',
                'Dimensions': [
                    {
                        'Name': 'Service',
                        'Value': 'Backend'
                    }
                ]
            }
        ]
    )

# Scale based on queue depth
QUEUE_DEPTH_SCALING_POLICY = {
    "targetValue": 5.0,
    "metricType": "Custom",
    "customMetricSpecification": {
        "metricName": "QueueDepth",
        "namespace": "RecipeChatbot/LLM",
        "statistic": "Average"
    }
}
```

### Network Architecture

#### **VPC Configuration**

```
┌─────────────────────────────────────────────────────────────┐
│                        VPC (10.0.0.0/16)                   │
│                                                             │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │  Public Subnet  │              │  Public Subnet  │      │
│  │   10.0.1.0/24   │              │   10.0.2.0/24   │      │
│  │      AZ-A       │              │      AZ-B       │      │
│  │                 │              │                 │      │
│  │      ALB        │◄────────────►│      ALB        │      │
│  └─────────────────┘              └─────────────────┘      │
│           │                                │                │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │ Private Subnet  │              │ Private Subnet  │      │
│  │   10.0.3.0/24   │              │   10.0.4.0/24   │      │
│  │      AZ-A       │              │      AZ-B       │      │
│  │                 │              │                 │      │
│  │  ECS Services   │              │  ECS Services   │      │
│  │                 │              │                 │      │
│  └─────────────────┘              └─────────────────┘      │
│           │                                │                │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │   NAT Gateway   │              │   NAT Gateway   │      │
│  │     AZ-A        │              │     AZ-B        │      │
│  └─────────────────┘              └─────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

#### **Security Groups**

```json
{
  "securityGroups": {
    "alb-sg": {
      "ingress": [
        {"port": 80, "source": "0.0.0.0/0", "protocol": "tcp"},
        {"port": 443, "source": "0.0.0.0/0", "protocol": "tcp"}
      ],
      "egress": [
        {"port": 8000, "destination": "ecs-backend-sg", "protocol": "tcp"},
        {"port": 3000, "destination": "ecs-frontend-sg", "protocol": "tcp"}
      ]
    },
    "ecs-backend-sg": {
      "ingress": [
        {"port": 8000, "source": "alb-sg", "protocol": "tcp"}
      ],
      "egress": [
        {"port": 443, "destination": "0.0.0.0/0", "protocol": "tcp"}
      ]
    },
    "ecs-frontend-sg": {
      "ingress": [
        {"port": 3000, "source": "alb-sg", "protocol": "tcp"}
      ],
      "egress": [
        {"port": 8000, "destination": "ecs-backend-sg", "protocol": "tcp"},
        {"port": 443, "destination": "0.0.0.0/0", "protocol": "tcp"}
      ]
    }
  }
}
```

#### **Application Load Balancer Setup**

```yaml
# ALB Configuration
LoadBalancer:
  Type: application
  Scheme: internet-facing
  SecurityGroups: [alb-sg]
  Subnets: [public-subnet-a, public-subnet-b]
  
  Listeners:
    - Port: 443
      Protocol: HTTPS
      SSLPolicy: ELBSecurityPolicy-TLS-1-2-2017-01
      Certificates: [recipe-chatbot-ssl-cert]
      DefaultActions:
        - Type: forward
          TargetGroupArn: frontend-tg
      Rules:
        - Priority: 100
          Conditions:
            - Field: path-pattern
              Values: ["/api/*", "/health", "/docs"]
          Actions:
            - Type: forward
              TargetGroupArn: backend-tg
    
    - Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: redirect
          RedirectConfig:
            Protocol: HTTPS
            Port: 443
            StatusCode: HTTP_301

TargetGroups:
  backend-tg:
    Port: 8000
    Protocol: HTTP
    VPC: recipe-chatbot-vpc
    HealthCheck:
      Path: /health
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      Timeout: 5
      Interval: 30
  
  frontend-tg:
    Port: 3000
    Protocol: HTTP
    VPC: recipe-chatbot-vpc
    HealthCheck:
      Path: /
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3
      Timeout: 5
      Interval: 30
```

## Deployment Process

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS ECS

on:
  push:
    branches: [main]
  
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push backend
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: recipe-chatbot-backend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ./backend
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Build and push frontend  
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: recipe-chatbot-frontend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ./frontend
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster recipe-chatbot-cluster \
            --service recipe-chatbot-backend \
            --force-new-deployment
          
          aws ecs update-service \
            --cluster recipe-chatbot-cluster \
            --service recipe-chatbot-frontend \
            --force-new-deployment
```

### Blue-Green Deployment Strategy

```json
{
  "deploymentConfiguration": {
    "maximumPercent": 200,
    "minimumHealthyPercent": 100,
    "deploymentCircuitBreaker": {
      "enable": true,
      "rollback": true
    }
  },
  "deploymentSteps": [
    {
      "phase": "preparation",
      "actions": ["validate-task-definition", "check-cluster-capacity"]
    },
    {
      "phase": "deployment", 
      "actions": ["start-new-tasks", "health-check", "traffic-shift"]
    },
    {
      "phase": "cleanup",
      "actions": ["stop-old-tasks", "clean-unused-images"]
    }
  ]
}
```

## Cost Optimization

### Resource Sizing Strategy

```yaml
TaskDefinitions:
  Backend:
    CPU: 512     # 0.5 vCPU
    Memory: 1024 # 1 GB RAM
    Rationale: "LLM API calls are I/O bound, moderate compute needs"
    
  Frontend:
    CPU: 256     # 0.25 vCPU  
    Memory: 512  # 0.5 GB RAM
    Rationale: "Static serving with minimal server-side processing"

ScalingPolicy:
  Backend:
    MinTasks: 2    # High availability
    MaxTasks: 20   # Peak load handling
    TargetCPU: 70% # Optimal resource utilization
    
  Frontend:
    MinTasks: 2    # High availability
    MaxTasks: 10   # Frontend is less resource intensive
    TargetCPU: 70% # Optimal resource utilization
```

### Cost Monitoring

```python
# Cost allocation tags
COST_TAGS = {
    "Project": "RecipeChatbot",
    "Environment": "Production", 
    "Owner": "AI-Team",
    "CostCenter": "R&D"
}

# Estimated monthly costs (us-east-1)
MONTHLY_COST_ESTIMATE = {
    "ECS Fargate (2-20 backend tasks)": "$50-500",
    "ECS Fargate (2-10 frontend tasks)": "$25-250", 
    "Application Load Balancer": "$18",
    "NAT Gateway (2 AZs)": "$90",
    "CloudWatch Logs (10 GB/month)": "$5",
    "Secrets Manager (2 secrets)": "$1",
    "Route 53 Hosted Zone": "$0.50",
    "ECR Storage (< 1GB)": "$0.10",
    "Total Estimated Range": "$189.60 - $864.60"
}
```

## Security Considerations

### Container Security

```dockerfile
# Multi-stage build for minimal attack surface
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
RUN adduser --disabled-password --gecos '' appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . /app
USER appuser
WORKDIR /app
ENV PATH=/home/appuser/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### IAM Roles and Policies

```json
{
  "ECSTaskRole": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue"
        ],
        "Resource": [
          "arn:aws:secretsmanager:*:*:secret:recipe-chatbot/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": [
          "arn:aws:logs:*:*:log-group:/aws/ecs/recipe-chatbot/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "cloudwatch:PutMetricData"
        ],
        "Resource": "*",
        "Condition": {
          "StringEquals": {
            "cloudwatch:namespace": "RecipeChatbot/*"
          }
        }
      }
    ]
  }
}
```

### Network Security

```yaml
SecurityMeasures:
  - WAF: "AWS WAF v2 with OWASP Core Rule Set"
  - DDoS: "AWS Shield Standard (included with ALB)"
  - SSL: "TLS 1.2+ only with perfect forward secrecy"
  - VPC: "Private subnets for all compute resources"
  - NACLs: "Network ACLs for additional layer of security"
  - GuardDuty: "Threat detection for malicious activity"
  
DataProtection:
  - SecretsRotation: "Quarterly rotation of API keys"
  - Encryption: "EBS encryption, S3 encryption, Secrets Manager encryption"
  - BackupStrategy: "ECS task definitions versioned, configuration as code"
```

---

This deployment strategy provides a robust, scalable, and cost-effective foundation for the Recipe Chatbot application while maintaining security best practices and operational excellence.
