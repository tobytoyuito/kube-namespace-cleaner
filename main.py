import os
import time
import json

from kubernetes import client, config
from conditions import AnnotationAllowCleanupIsTrueCondition
from conditions import InactiveDeploymentCondition
from conditions import VSTSRefDeletedCondition
import conditions

def clean():
    try:
        print("Loading in-cluster config")
        config.load_incluster_config()
    except Exception:
        print("Failed to load in-cluster config. Using KUBECONFIG/default config")
        config.load_kube_config()

    v1api = client.CoreV1Api()
    v1beta1api = client.AppsV1beta1Api()
    max_namespace_inactive_days = os.environ['MAX_NAMESPACE_INACTIVE_HOURS']

    ns_whitelist = os.environ['NS_WHITELIST'].split(',')

    stale = conditions.AND(conditions.NotWhitelisted(ns_whitelist),
                           InactiveDeploymentCondition(v1beta1api, max_namespace_inactive_days))

    # reading environment variable
    vsts_token = os.environ['VSTS_PAT']

    cleanup_conditions = conditions.AND(
        AnnotationAllowCleanupIsTrueCondition(),
        conditions.OR(VSTSRefDeletedCondition(vsts_token), stale)
    )

    namespaces = v1api.list_namespace()
    cleaned = 0
    for namespace in namespaces.items:
        print("-- Checking namespace %s --" % namespace.metadata.name)

        # delete namespace if all conditions are met
        if cleanup_conditions(namespace):
            print("Cleaning up namespace %s" % namespace.metadata.name)
            # real cleanup will be enable later once it's tested
            v1api.delete_namespace(namespace.metadata.name, client.V1DeleteOptions())
            cleaned += 1

    print("Finish clean up script")
    return {'namespaces_cleaned' : cleaned, "namespaces_scanned" :  len(namespaces.items)}

def main():
    start = time.time()
    eventdict = {'name' : 'kubernetes.namespacecleaner', 'time' : start, 'eventtype' : 'json'}
    try:
        stats = clean()
        eventdict.update(stats)
        eventdict['success'] = True
    except Exception as exception:
        eventdict["error"] = str(exception)
        eventdict["success"] = False
        raise exception
    finally:
        eventdict['ElapsedTime'] = time.time() - start
        print(json.dumps(eventdict))

if __name__ == '__main__':
    main()
