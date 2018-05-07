# Kubernetes Namespace Cleaner

## Steps to deploy to kubernetes

- update <your pat> to your vsts pat in cleaner.yaml
- kubectl apply -f cleaner.yaml

## Steps to create container (uses a docker multistage build)

- docker build . -t tobyto/kube-namespace-cleaner
- docker push tobyto/kube-namespace-cleaner (or choose your own namespace)
