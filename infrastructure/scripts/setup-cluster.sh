#!/bin/bash
# Kubernetes Cluster Setup Script

set -e

CLUSTER_NAME="fake-news-cluster"
REGION="us-west-2"

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

setup_eks_cluster() {
    print_status "Setting up EKS cluster..."
    aws eks create-cluster --name ${CLUSTER_NAME} --region ${REGION} --kubernetes-version 1.28 --nodegroup-name ${CLUSTER_NAME}-workers --node-type t3.medium --nodes 3 --nodes-min 1 --nodes-max 6 --managed
    aws eks update-kubeconfig --region ${REGION} --name ${CLUSTER_NAME}
}

setup_local_cluster() {
    print_status "Setting up local cluster..."
    if command -v kind &> /dev/null; then
        kind create cluster --name ${CLUSTER_NAME}
    elif command -v minikube &> /dev/null; then
        minikube start --cpus=2 --memory=4096
    else
        echo "Install kind or minikube"
        exit 1
    fi
}

install_addons() {
    print_status "Installing addons..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml
}

case "${1:-}" in
    "eks")
        setup_eks_cluster
        ;;
    "local")
        setup_local_cluster
        ;;
    "addons")
        install_addons
        ;;
    *)
        echo "Usage: $0 {eks|local|addons}"
        exit 1
        ;;
esac
