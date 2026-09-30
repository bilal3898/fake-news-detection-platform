# Infrastructure Setup

This directory contains all the infrastructure configuration for deploying the Fake News Detection Platform using Docker and Kubernetes.

## 📁 Directory Structure

```
infrastructure/
├── Kubernetes/                    # Kubernetes manifests
│   ├── namespace.yaml            # Namespace configuration
│   ├── configmap.yaml            # Application configuration
│   ├── secrets.yaml              # Secrets (update with actual values)
│   ├── postgres-deployment.yaml  # PostgreSQL database
│   ├── mongodb-deployment.yaml   # MongoDB database
│   ├── redis-deployment.yaml     # Redis cache
│   ├── backend-deployment.yaml   # Backend API service
│   ├── frontend-deployment.yaml  # Frontend web service
│   ├── celery-deployment.yaml    # Celery workers and scheduler
│   ├── ingress.yaml              # Ingress configuration
│   ├── hpa.yaml                  # Horizontal Pod Autoscaling
│   ├── monitoring.yaml           # Prometheus monitoring
│   ├── kustomization.yaml        # Kustomize configuration
│   └── patches/                  # Environment-specific patches
│       ├── backend-prod.yaml
│       └── frontend-prod.yaml
├── scripts/                      # Deployment and management scripts
│   ├── deploy.sh                 # Main deployment script
│   ├── setup-cluster.sh          # Cluster setup script
│   ├── cleanup.sh                # Cleanup script
│   └── monitor.sh                # Monitoring script
├── Dockerfile.backend            # Backend Dockerfile
├── Dockerfile.frontend           # Frontend Dockerfile
├── docker-compose.yml            # Development Docker Compose
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or local)
- kubectl configured
- Docker installed
- Helm (for monitoring setup)

### 1. Setup Cluster

```bash
# For local development
./scripts/setup-cluster.sh local

# For AWS EKS
./scripts/setup-cluster.sh eks

# Install addons (NGINX Ingress, cert-manager)
./scripts/setup-cluster.sh addons
```

### 2. Update Secrets

Edit `infrastructure/Kubernetes/secrets.yaml` and replace the placeholder values with actual base64-encoded secrets:

```bash
# Generate base64 values
echo -n "your-secret-key" | base64
echo -n "your-jwt-secret" | base64
echo -n "your-news-api-key" | base64
```

### 3. Deploy Application

```bash
# Full deployment
./scripts/deploy.sh deploy

# Or step by step
./scripts/deploy.sh build    # Build and push images
./scripts/deploy.sh secrets  # Apply secrets
./scripts/deploy.sh migrate  # Run migrations
./scripts/deploy.sh verify   # Verify deployment
```

### 4. Monitor Deployment

```bash
# Check all resources
./scripts/monitor.sh all

# Check specific resources
./scripts/monitor.sh pods
./scripts/monitor.sh services
./scripts/monitor.sh logs
./scripts/monitor.sh metrics
```

## 🐳 Docker Development

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Building Images

```bash
# Build backend
docker build -f infrastructure/Dockerfile.backend -t fake-news-backend:latest .

# Build frontend
cd frontend
docker build -f ../infrastructure/Dockerfile.frontend -t fake-news-frontend:latest .
```

## ☸️ Kubernetes Configuration

### Namespaces

The application runs in the `fake-news-detection` namespace to isolate resources.

### Services

- **Backend**: API server on port 8000
- **Frontend**: Web interface on port 80
- **PostgreSQL**: Database on port 5432
- **MongoDB**: Document store on port 27017
- **Redis**: Cache on port 6379

### Ingress

The application uses NGINX Ingress Controller with SSL termination:

- **Main Site**: `https://fakenews-detection.com`
- **API**: `https://api.fakenews-detection.com`
- **Admin**: `https://admin.fakenews-detection.com`

### Autoscaling

Horizontal Pod Autoscaling is configured for:

- **Backend**: 3-10 replicas based on CPU/memory usage
- **Frontend**: 2-6 replicas based on CPU/memory usage
- **Celery Workers**: 2-8 replicas based on CPU/memory usage

### Monitoring

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **AlertManager**: Alert management

## 🔧 Configuration

### Environment Variables

Update `infrastructure/Kubernetes/configmap.yaml` with your environment-specific values:

```yaml
data:
  DATABASE_URL: "postgresql://postgres:password@postgres:5432/fake_news_db"
  MONGODB_URL: "mongodb://admin:password@mongodb:27017/fake_news?authSource=admin"
  LOG_LEVEL: "INFO"
  # ... other configurations
```

### Secrets

Update `infrastructure/Kubernetes/secrets.yaml` with sensitive data:

```yaml
data:
  SECRET-KEY: <BASE64_ENCODED_SECRET_KEY>
  JWT-SECRET-KEY: <BASE64_ENCODED_JWT_SECRET_KEY>
  NEWS-API-KEY: <BASE64_ENCODED_NEWS_API_KEY>
  # ... other secrets
```

### Resource Limits

Adjust resource requests and limits in deployment files based on your cluster capacity.

## 📊 Monitoring

### Prometheus Metrics

Access Prometheus at: `http://prometheus.fakenews-detection.com`

### Grafana Dashboards

Access Grafana at: `http://grafana.fakenews-detection.com`

Default credentials:
- Username: `admin`
- Password: `admin` (change on first login)

### Key Metrics

- **Response Time**: API response latency
- **Error Rate**: HTTP error percentages
- **Throughput**: Requests per second
- **Resource Usage**: CPU, memory, disk, network
- **Database Performance**: Query times, connection counts

## 🔒 Security

### SSL/TLS

SSL certificates are automatically managed by cert-manager using Let's Encrypt.

### Network Policies

Network policies are configured to restrict traffic between pods.

### RBAC

Role-based access control is configured for Kubernetes resources.

## 🚨 Troubleshooting

### Common Issues

1. **Pods not starting**
   ```bash
   kubectl describe pod <pod-name> -n fake-news-detection
   kubectl logs <pod-name> -n fake-news-detection
   ```

2. **Ingress not working**
   ```bash
   kubectl get ingress -n fake-news-detection
   kubectl describe ingress fake-news-ingress -n fake-news-detection
   ```

3. **Database connection issues**
   ```bash
   kubectl exec -it <postgres-pod> -n fake-news-detection -- psql -U postgres -d fake_news_db
   ```

### Cleanup

```bash
# Clean up deployment
./scripts/cleanup.sh namespace

# Clean up entire cluster
./scripts/cleanup.sh cluster

# Clean up everything
./scripts/cleanup.sh all
```

## 🔄 CI/CD Integration

### GitHub Actions

The deployment scripts can be integrated with GitHub Actions for automated deployments:

```yaml
- name: Deploy to Kubernetes
  run: |
    ./infrastructure/scripts/deploy.sh deploy
```

### GitLab CI

```yaml
deploy:
  script:
    - ./infrastructure/scripts/deploy.sh deploy
```

## 📈 Performance Optimization

### Database Optimization

- Use connection pooling
- Enable query caching
- Optimize indexes
- Monitor slow queries

### Application Optimization

- Enable Gzip compression
- Use CDN for static assets
- Implement caching strategies
- Optimize Docker image sizes

### Cluster Optimization

- Use appropriate instance types
- Enable cluster autoscaling
- Optimize resource requests/limits
- Use spot instances for cost savings

## 🌐 Multi-Environment Support

### Development

```bash
kubectl apply -k infrastructure/Kubernetes/overlays/development
```

### Staging

```bash
kubectl apply -k infrastructure/Kubernetes/overlays/staging
```

### Production

```bash
kubectl apply -k infrastructure/Kubernetes/overlays/production
```

## 📞 Support

For infrastructure-related issues:

1. Check the troubleshooting section
2. Review Kubernetes logs
3. Monitor resource usage
4. Check network connectivity
5. Verify configuration files

## 📝 Maintenance

### Regular Tasks

- Update container images
- Rotate secrets
- Backup databases
- Monitor resource usage
- Update Kubernetes versions

### Backup Strategy

- Database backups: Daily
- Configuration backups: Weekly
- Full cluster backups: Monthly

### Disaster Recovery

- Document recovery procedures
- Test backup restoration
- Maintain offline backups
- Plan for multi-region deployment
