# Deployment Guide

This guide provides comprehensive instructions for deploying the Geo-Analytics API to various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Deployment Options](#deployment-options)
  - [Docker Deployment](#docker-deployment)
  - [Kubernetes Deployment](#kubernetes-deployment)
  - [Cloud Platform Deployment](#cloud-platform-deployment)
- [Post-Deployment](#post-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Rollback Procedures](#rollback-procedures)

## Prerequisites

Before deploying, ensure you have:

- Docker 20.10+ or Kubernetes 1.20+
- Access to your target deployment environment
- Environment-specific configuration files
- SSL/TLS certificates for production
- Database connection credentials
- API keys for external services

## Environment Variables

Required environment variables:

```bash
# Application Settings
APP_ENV=production|staging|development
APP_DEBUG=false
APP_PORT=8000
APP_HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/dbname
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# External Services
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn

# Feature Flags
ENABLE_METRICS=true
ENABLE_RATE_LIMITING=true
```

## Deployment Options

### Docker Deployment

#### Single Container

```bash
# Build the image
docker build -t geo-analytics-api:latest .

# Run the container
docker run -d \
  --name geo-analytics-api \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  --restart unless-stopped \
  geo-analytics-api:latest
```

#### Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    image: geo-analytics-api:latest
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  postgres:
    image: postgis/postgis:15-3.3
    environment:
      - POSTGRES_DB=geoanalytics
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  redis-data:
  postgres-data:
```

Deploy with:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

#### Basic Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: geo-analytics-api
  labels:
    app: geo-analytics-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: geo-analytics-api
  template:
    metadata:
      labels:
        app: geo-analytics-api
    spec:
      containers:
      - name: api
        image: your-registry/geo-analytics-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: geo-analytics-api
spec:
  selector:
    app: geo-analytics-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Create secrets:

```bash
kubectl create secret generic api-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=secret-key="your-secret-key"
```

Deploy:

```bash
kubectl apply -f k8s/deployment.yaml
```

#### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: geo-analytics-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: geo-analytics-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Cloud Platform Deployment

#### AWS (ECS/Fargate)

1. Create ECR repository:
```bash
aws ecr create-repository --repository-name geo-analytics-api
```

2. Build and push image:
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker build -t geo-analytics-api .
docker tag geo-analytics-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/geo-analytics-api:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/geo-analytics-api:latest
```

3. Create ECS task definition and service using AWS Console or CloudFormation.

#### Google Cloud Platform (Cloud Run)

```bash
# Build and submit
gcloud builds submit --tag gcr.io/PROJECT_ID/geo-analytics-api

# Deploy
gcloud run deploy geo-analytics-api \
  --image gcr.io/PROJECT_ID/geo-analytics-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="APP_ENV=production,DATABASE_URL=..."
```

#### Azure (Container Instances)

```bash
# Create container registry
az acr create --resource-group myResourceGroup --name geoanalyticsacr --sku Basic

# Build and push
az acr build --registry geoanalyticsacr --image geo-analytics-api:latest .

# Deploy
az container create \
  --resource-group myResourceGroup \
  --name geo-analytics-api \
  --image geoanalyticsacr.azurecr.io/geo-analytics-api:latest \
  --dns-name-label geo-analytics-api \
  --ports 8000 \
  --environment-variables APP_ENV=production
```

## Post-Deployment

### Database Migrations

Run database migrations after deployment:

```bash
# Using Docker
docker exec geo-analytics-api alembic upgrade head

# Using Kubernetes
kubectl exec -it deployment/geo-analytics-api -- alembic upgrade head
```

### Smoke Tests

Verify the deployment:

```bash
# Health check
curl https://your-api-domain.com/health

# API version
curl https://your-api-domain.com/api/version

# Test endpoint (if available)
curl https://your-api-domain.com/api/test
```

### Load Balancer Configuration

Configure your load balancer:

- Health check endpoint: `/health`
- Health check interval: 30 seconds
- Timeout: 10 seconds
- Unhealthy threshold: 3 failed checks
- Healthy threshold: 2 successful checks

## Monitoring and Maintenance

### Logging

View logs:

```bash
# Docker
docker logs -f geo-analytics-api

# Kubernetes
kubectl logs -f deployment/geo-analytics-api

# Docker Compose
docker-compose logs -f api
```

### Metrics

Monitor key metrics:

- Request rate and latency
- Error rates (4xx, 5xx)
- Database connection pool usage
- Memory and CPU usage
- Active connections

### Backup Procedures

```bash
# Database backup
pg_dump -h localhost -U user geoanalytics > backup_$(date +%Y%m%d).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
# Upload to S3 or other storage
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/
```

## Rollback Procedures

### Docker Rollback

```bash
# Stop current container
docker stop geo-analytics-api

# Start previous version
docker run -d --name geo-analytics-api geo-analytics-api:previous-tag
```

### Kubernetes Rollback

```bash
# Rollback to previous revision
kubectl rollout undo deployment/geo-analytics-api

# Rollback to specific revision
kubectl rollout undo deployment/geo-analytics-api --to-revision=2

# Check rollout status
kubectl rollout status deployment/geo-analytics-api
```

### Database Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check logs for errors
   - Verify environment variables
   - Ensure database is accessible

2. **High memory usage**
   - Adjust worker count
   - Increase memory limits
   - Check for memory leaks

3. **Database connection errors**
   - Verify connection string
   - Check network connectivity
   - Ensure database is running

4. **SSL/TLS issues**
   - Verify certificate validity
   - Check certificate chain
   - Ensure proper permissions

## Security Considerations

- Always use HTTPS in production
- Store secrets in environment variables or secret managers
- Regularly update dependencies
- Enable rate limiting
- Configure CORS properly
- Use non-root users in containers
- Scan images for vulnerabilities
- Keep backups encrypted

## Support

For deployment issues:
- Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
- Review logs and error messages
- Contact DevOps team
- Create an issue on GitHub
