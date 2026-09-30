#!/bin/bash
# Cleanup Script for Kubernetes Deployment

set -e

NAMESPACE="fake-news-detection"
CLUSTER_NAME="fake-news-cluster"

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

cleanup_namespace() {
    print_status "Cleaning up namespace..."
    kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
}

cleanup_cluster() {
    print_status "Cleaning up cluster..."
    if command -v kind &> /dev/null; then
        kind delete cluster --name ${CLUSTER_NAME}
    elif command -v minikube &> /dev/null; then
        minikube delete
    elif command -v aws &> /dev/null; then
        aws eks delete-cluster --name ${CLUSTER_NAME} --region us-west-2
    fi
}

case "${1:-}" in
    "namespace")
        cleanup_namespace
        ;;
    "cluster")
        cleanup_cluster
        ;;
    "all")
        cleanup_namespace
        cleanup_cluster
        ;;
    *)
        echo "Usage: $0 {namespace|cluster|all}"
        exit 1
        ;;
esac
