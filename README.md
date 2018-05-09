# Kubernetes Namespace Cleaner

This is a python script to delete old namespace that are no longer use based on following 3 conditions:
1. namespace has allowCleanup in its annotations (prevent default/kube-system from being clean up)
2. namespace is inactive (no new deployment or deployment update for over a certain times, default is 1 day)
3. namespace's associated branch is deleted in VSTS (all vsts info are from the namespace's annotations)

Condition 1 and 3 require change to the namespace's annotation. We need to get the annotation to our base yamls.

This script is built into a docker image in https://hub.docker.com/r/tobyto/kube-namespace-cleaner/. The image size is 124MB.

And then you can deploy this image to your kubernetes cluster as a cronjob by following [these steps](#steps-to-deploy-to-kubernetes). It'll run daily to clean up the namespace.

## Steps to deploy to kubernetes

- update <your pat> to your vsts pat in cleaner.yaml
- kubectl apply -f cleaner.yaml

## Steps to create container (uses a docker multistage build)

- docker build . -t tobyto/kube-namespace-cleaner
- docker push tobyto/kube-namespace-cleaner (or choose your own namespace)
