from kubernetes import client, config
from conditions import AnnotationAllowCleanupIsTrueCondition, InactiveDeploymentCondition, VSTSBranchDeletedCondition
import os

def main():
    try:
        print("Loading in-cluster config")
        config.load_incluster_config()
    except:
        print("Failed to load in-cluster config. Using KUBECONFIG, if not specified, default config")
        config.load_kube_config()

    v1api = client.CoreV1Api()
    v1beta1api = client.AppsV1beta1Api()

    # reading environment variable
    vsts_token = os.environ['VSTS_PAT'] #throw if empty?
    max_namespace_inactive_days = os.environ['MAX_NAMESPACE_INACTIVE_DAYS']

    cleanup_conditions = [
        AnnotationAllowCleanupIsTrueCondition(),
        InactiveDeploymentCondition(v1beta1api, max_namespace_inactive_days), 
        VSTSBranchDeletedCondition(vsts_token),
    ]

    namespaces = v1api.list_namespace()
    for namespace in namespaces.items:
        print("-- Checking namespace %s --" % namespace.metadata.name)
        
        # clean up if all of the conditions are met
        # map in 3.x python is lazy, so it'll stop once one condition returns false
        #hmm though all took a function like map. Could also use list comprehensions
        cleanup = all([c.satisfy(namespace) for c in cleanup_conditions])
        
        # delete namespace
        if cleanup:
            print("Cleaning up namespace %s" % namespace.metadata.name)
            # real cleanup will be enable later once it's tested
            v1api.delete_namespace(namespace.metadata.name, client.V1DeleteOptions())

    print("Finish clean up script")


if __name__ == '__main__':
    main()
