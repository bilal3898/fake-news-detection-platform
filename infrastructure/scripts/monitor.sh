#!/bin/bash
# Monitoring Script for Kubernetes Deployment

set -e

NAMESPACE="fake-news-detection"

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

show_pods() {
    print_status "Pods status:"
    kubectl get pods -n ${NAMESPACE}
}

show_services() {
    print_status "Services status:"
    kubectl get services -n ${NAMESPACE}
}

show_logs() {
    print_status "Backend logs:"
    kubectl logs -n ${NAMESPACE} -l app=backend --tail=50
}

show_metrics() {
    print_status "Resource usage:"
    kubectl top pods -n ${NAMESPACE}
}

case "${1:-}" in
    "pods")
        show_pods
        ;;
    "services")
        show_services
        ;;
    "logs")
        show_logs
        ;;
    "metrics")
        show_metrics
        ;;
    "all")
        show_pods
        show_services
        show_metrics
        ;;
    *)
        echo "Usage: $0 {pods|services|logs|metrics|all}"
        exit 1
        ;;
esac
