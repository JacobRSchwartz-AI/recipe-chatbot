# AWS Deployment Guide - Recipe Chatbot

This document outlines the production deployment strategy for the Recipe Chatbot application using AWS services, with a focus on balancing scalability, cost-effectiveness, and operational simplicity.

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

**ECS Fargate** was selected as the primary compute platform for the following reasons:

#### ✅ **Serverless Containers**
- No EC2 instances to manage or patch
- AWS handles all infrastructure updates
- Pay only for compute resources used
- Automatic scaling without managing servers

#### ✅ **Docker-Native**
- Our application already uses Docker Compose
- Minimal changes needed for production deployment
- Consistent development and production environments
- Easy local testing with identical containers

#### ✅ **Production-Ready**
- Built-in load balancing with ALB
- Zero-downtime deployments
- Health checks and automatic recovery
- Native AWS service integrations

#### ✅ **Cost-Effective at Scale**
- No idle compute costs
- Scales to zero if needed
- More predictable pricing than Lambda
- Cheaper than EKS for small-medium workloads

### Alternative Compute Options Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **AWS Lambda** | True serverless, automatic scaling | 15-min timeout unsuitable for LLMs, cold starts | ❌ Not suitable |
| **AWS App Runner** | Extremely simple deployment | Less control, newer service | ✅ Good alternative for MVP |
| **EKS (Kubernetes)** | Industry standard, powerful | Complex, expensive, overkill | ❌ Over-engineered |
| **EC2 + Docker** | Full control | Manual scaling, server management | ❌ Too much overhead |

### Core Components

- **ECS Cluster**: Container orchestration using Fargate
- **Application Load Balancer**: Routes traffic, handles SSL
- **ECS Services**: Separate services for backend and frontend
- **ECR**: Private container registry for our Docker images
- **Secrets Manager/SSM**: Secure storage for API keys
- **CloudWatch**: Centralized logging and monitoring

## Secret Management

### Approach: SSM Parameter Store with Secrets Manager for Sensitive Data

**SSM Parameter Store** for configuration:
- Non-sensitive configuration values
- Environment variables
- Feature flags
- Free tier sufficient for our needs

**AWS Secrets Manager** for sensitive data:
- OpenAI API key
- SERP API key
- Future database credentials
- Automatic rotation capabilities when needed

### Implementation Strategy

1. **Development**: Use `.env` files locally
2. **Staging/Production**: ECS tasks pull from SSM/Secrets Manager
3. **Access Control**: IAM roles restrict access per service

## Observability & Monitoring

### Logging Strategy

**Structured Logging**
- JSON format for easy parsing
- Correlation IDs for request tracing
- Log levels: ERROR, WARNING, INFO, DEBUG
- Automatic CloudWatch Logs integration

**Log Retention**
- 7 days for development
- 30 days for production
- Archive to S3 for compliance if needed

### Metrics & Monitoring

**Application Metrics**
- Request rate and latency
- Error rates by endpoint
- LLM API usage and costs
- Tool usage frequency (web search, cookware check)

**Infrastructure Metrics**
- CPU and memory utilization
- Task health status
- ALB target health
- Container restart frequency

**Alerting**
- High error rate (>5% for 5 minutes)
- High latency (p95 > 5 seconds)
- Task failures
- LLM API errors

### Future Observability Enhancements

When the application grows, consider:
- AWS X-Ray for distributed tracing
- Custom CloudWatch dashboards
- Third-party APM tools (DataDog, New Relic)

## Scaling & Networking

### Auto-Scaling Configuration

**Backend Service**
- Minimum tasks: 2 (high availability)
- Maximum tasks: 10
- Scale on CPU utilization (target: 70%)
- Scale on memory utilization (target: 80%)
- Scale on custom metrics (request queue depth)

**Frontend Service**
- Minimum tasks: 2
- Maximum tasks: 5
- Scale on CPU utilization (target: 70%)
- Frontend typically needs less scaling

### Network Architecture

**Simple VPC Setup**
- Single VPC with public and private subnets
- ECS tasks in private subnets
- ALB in public subnets
- NAT Gateway for outbound internet (single AZ for cost savings)

**Security Groups**
- ALB: Allow 80/443 from internet
- ECS Backend: Allow 8000 from ALB only
- ECS Frontend: Allow 3000 from ALB only
- Outbound: Allow HTTPS for external APIs

### Load Balancer Configuration

**Application Load Balancer**
- SSL termination with ACM certificate
- Path-based routing:
  - `/api/*` → Backend target group
  - `/*` → Frontend target group
- Health checks on `/health` endpoints
- Sticky sessions not required

## Deployment Process

### CI/CD Pipeline Overview

**GitHub Actions Workflow**
1. Trigger on push to main branch
2. Run tests and linting
3. Build Docker images
4. Push to ECR
5. Update ECS service definitions
6. Monitor deployment health

**Deployment Strategy**
- Rolling updates with ECS
- Maximum 200% capacity during deployment
- Minimum 100% healthy capacity
- Automatic rollback on failures

### Infrastructure as Code

**Terraform** for infrastructure:
- VPC and networking
- ECS cluster and services
- ALB and target groups
- IAM roles and policies

**Why Terraform over CloudFormation:**
- Better syntax and tooling
- Multi-cloud potential
- Stronger community support
- Easier state management

## Cost Optimization

### Estimated Monthly Costs

**Base Infrastructure**
- ECS Fargate (4 tasks minimum): ~$30
- Application Load Balancer: $18
- NAT Gateway (single AZ): $45
- Route 53: $0.50
- CloudWatch Logs: ~$5
- Secrets Manager: $2
- **Total Base**: ~$100/month

**Scaling Costs**
- Each additional task: ~$7.50/month
- Data transfer: Variable based on usage
- Additional monitoring: ~$10-20/month

### Cost Optimization Strategies

1. **Right-size containers**: Start small, scale up based on metrics
2. **Single AZ for non-critical**: Add multi-AZ when needed
3. **Spot Fargate**: Use for non-critical workloads
4. **CloudFront CDN**: Cache static assets
5. **Reserved Capacity**: When usage patterns stabilize

### Cost Monitoring

- AWS Cost Explorer for trends
- Budget alerts at 80% and 100%
- Tag all resources for cost allocation
- Regular cost optimization reviews

## Security Considerations

### Application Security

**API Security**
- Rate limiting at ALB level
- API key authentication for initial version
- CORS properly configured
- Input validation and sanitization
- SQL injection prevention (when DB added)

**Container Security**
- Non-root user in containers
- Minimal base images (alpine/slim)
- Regular security scanning with ECR
- No secrets in images

### Infrastructure Security

**Network Security**
- Private subnets for compute
- Security groups as firewalls
- NACLs for additional protection
- VPC Flow Logs for audit

**Access Control**
- IAM roles for service access
- Least privilege principle
- No long-lived credentials
- CloudTrail for audit logging

### Compliance Readiness

**Current State**
- Basic security hygiene
- Encryption at rest and in transit
- Access logging enabled

**Future Enhancements**
- WAF for application protection
- GuardDuty for threat detection
- Security Hub for compliance
- Regular penetration testing

## Migration and Rollback Strategy

### Deployment Phases

**Phase 1: MVP Deployment**
- Single ECS service with both frontend/backend
- Manual deployments
- Basic monitoring

**Phase 2: Production Ready**
- Separate services
- CI/CD pipeline
- Enhanced monitoring

**Phase 3: Scale Ready**
- Multi-AZ deployment
- Advanced observability
- Performance optimization

### Rollback Procedures

1. **ECS Service Rollback**: Update service to previous task definition
2. **Database Rollback**: Not applicable (no database yet)
3. **Infrastructure Rollback**: Terraform state management
4. **Emergency Procedures**: Document runbooks for common issues

## Future Enhancements

### Short Term (1-3 months)
- Add Redis for caching
- Implement API versioning
- Add integration tests
- Set up staging environment

### Medium Term (3-6 months)
- Multi-region deployment
- GraphQL API option
- WebSocket support for real-time
- Advanced LLM prompt management

### Long Term (6+ months)
- Kubernetes migration if needed
- Multi-cloud strategy
- Edge computing with Lambda@Edge
- ML model self-hosting option

## Summary

This deployment plan provides a production-ready foundation that:
- Leverages AWS managed services for reduced operational overhead
- Scales efficiently with demand
- Maintains security best practices
- Keeps costs predictable and optimized
- Provides clear upgrade paths for future growth

The architecture is intentionally kept simple initially, with well-documented paths for adding complexity as the application grows and requirements evolve.