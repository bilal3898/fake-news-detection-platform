#!/bin/bash

# Fake News Detection Platform Deployment Script
# This script deploys the application to Kubernetes

set -e

# Configuration
NAMESPACE="fake-news-detection"
DOCKER_REGISTRY="your-registry.com"
DOCKER_TAG="latest"
ENVIRONMENT="production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "docker is not installed. Please install docker first."
        exit 1
    fi
    
    print_status "Dependencies check passed."
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Build backend image
    print_status "Building backend image..."
    docker build -f infrastructure/Dockerfile.backend -t ${DOCKER_REGISTRY}/fake-news-backend:${DOCKER_TAG} .
    
    # Build frontend image
    print_status "Building frontend image..."
    cd frontend
    docker build -f ../infrastructure/Dockerfile.frontend -t ${DOCKER_REGISTRY}/fake-news-frontend:${DOCKER_TAG} .
    cd ..
    
    # Push images
    print_status "Pushing images to registry..."
    docker push ${DOCKER_REGISTRY}/fake-news-backend:${DOCKER_TAG}
    docker push ${DOCKER_REGISTRY}/fake-news-frontend:${DOCKER_TAG}
    
    print_status "Images built and pushed successfully."
}

# Create namespace
create_namespace() {
    print_status "Creating namespace..."
    kubectl apply -f infrastructure/Kubernetes/namespace.yaml
    print_status "Namespace created successfully."
}

# Apply secrets
apply_secrets() {
    print_status "Applying secrets..."
    
    # Check if secrets file exists and has been updated
    if ! grep -q "<BASE64_ENCODED" infrastructure/Kubernetes/secrets.yaml; then
        kubectl apply -f infrastructure/Kubernetes/secrets.yaml
        print_status "Secrets applied successfully."
    else
        print_warning "Please update the secrets.yaml file with actual base64 encoded values before applying."
        print_warning "Skipping secrets application."
    fi
}

# Deploy databases
deploy_databases() {
    print_status "Deploying databases..."
    
    kubectl apply -f infrastructure/Kubernetes/postgres-deployment.yaml
    kubectl apply -f infrastructure/Kubernetes/mongodb-deployment.yaml
    kubectl apply -f infrastructure/Kubernetes/redis-deployment.yaml
    
    print_status "Waiting for databases to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=mongodb -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n ${NAMESPACE} --timeout=300s
    
    print_status "Databases deployed successfully."
}

# Deploy application
deploy_application() {
    print_status "Deploying application..."
    
    # Apply ConfigMaps
    kubectl apply -f infrastructure/Kubernetes/configmap.yaml
    
    # Deploy backend
    kubectl apply -f infrastructure/Kubernetes/backend-deployment.yaml
    
    # Deploy frontend
    kubectl apply -f infrastructure/Kubernetes/frontend-deployment.yaml
    
    # Deploy Celery workers
    kubectl apply -f infrastructure/Kubernetes/celery-deployment.yaml
    
    print_status "Waiting for application to be ready..."
    kubectl wait --for=condition=ready pod -l app=backend -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=frontend -n ${NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=celery-worker -n ${NAMESPACE} --timeout=300s
    
    print_status "Application deployed successfully."
}

# Apply ingress and monitoring
apply_ingress_monitoring() {
    print_status "Applying ingress and monitoring..."
    
    kubectl apply -f infrastructure/Kubernetes/ingress.yaml
    kubectl apply -f infrastructure/Kubernetes/hpa.yaml
    kubectl apply -f infrastructure/Kubernetes/monitoring.yaml
    
    print_status "Ingress and monitoring applied successfully."
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Get the backend pod name
    BACKEND_POD=$(kubectl get pods -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].metadata.name}')
    
    # Run migrations
    kubectl exec -n ${NAMESPACE} ${BACKEND_POD} -- python -m alembic upgrade head
    
    print_status "Database migrations completed."
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Check all pods are running
    kubectl get pods -n ${NAMESPACE}
    
    # Check services
    kubectl get services -n ${NAMESPACE}
    
    # Check ingress
    kubectl get ingress -n ${NAMESPACE}
    
    # Test backend health
    BACKEND_URL=$(kubectl get ingress fake-news-ingress -n ${NAMESPACE} -o jsonpath='{.spec.rules[1].host}')
    if curl -f http://${BACKEND_URL}/health > /dev/null 2>&1; then
        print_status "Backend health check passed."
    else
        print_error "Backend health check failed."
    fi
    
    print_status "Deployment verification completed."
}

# Main deployment function
main() {
    print_status "Starting deployment of Fake News Detection Platform..."
    
    check_dependencies
    build_and_push_images
    create_namespace
    apply_secrets
    deploy_databases
    deploy_application
    apply_ingress_monitoring
    run_migrations
    verify_deployment
    
    print_status "Deployment completed successfully!"
    print_status "Application is now available at: https://fakenews-detection.com"
    print_status "API is available at: https://api.fakenews-detection.com"
}

# Handle script arguments
case "${1:-}" in
    "build")
        build_and_push_images
        ;;
    "deploy")
        main
        ;;
    "secrets")
        apply_secrets
        ;;
    "migrate")
        run_migrations
        ;;
    "verify")
        verify_deployment
        ;;
    "cleanup")
        print_status "Cleaning up deployment..."
        kubectl delete namespace ${NAMESPACE}
        print_status "Cleanup completed."
        ;;
    *)
        echo "Usage: $0 {build|deploy|secrets|migrate|verify|cleanup}"
        echo "  build    - Build and push Docker images"
        echo "  deploy   - Full deployment"
        echo "  secrets  - Apply secrets only"
        echo "  migrate  - Run database migrations"
        echo "  verify   - Verify deployment"
        echo "  cleanup  - Clean up deployment"
        exit 1
        ;;
esac
