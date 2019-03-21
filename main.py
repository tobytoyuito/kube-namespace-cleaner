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
    v1appsapi = client.AppsV1Api()
    max_namespace_inactive_days = os.environ['MAX_NAMESPACE_INACTIVE_HOURS']

    ns_whitelist = os.environ['NS_WHITELIST'].split(',')

    stale = conditions.AND(conditions.NotWhitelisted(ns_whitelist),
                           InactiveDeploymentCondition(v1appsapi, max_namespace_inactive_days))

    # reading environment variable
    vsts_token = os.environ['VSTS_PAT']

    cleanup_conditions = conditions.AND(
        AnnotationAllowCleanupIsTrueCondition(),
        conditions.OR(VSTSRefDeletedCondition(vsts_token), stale)
    )

    namespaces = v1api.list_namespace()
    cleaned = 0
    failed_cleanup = 0
    failed_check_condition = 0
    for namespace in namespaces.items:
        print("-- Checking namespace %s --" % namespace.metadata.name)

        try:
            # delete namespace if all conditions are met
            if cleanup_conditions(namespace):
                print("Cleaning up namespace %s" % namespace.metadata.name)
                try:
                    v1api.delete_namespace(namespace.metadata.name, client.V1DeleteOptions())
                    cleaned += 1
                except Exception as ex:
                    print("Failed to cleanup %s" % namespace.metadata.name)
                    print(str(ex))
                    failed_cleanup += 1
        except Exception as ex:
            print("Failed to check condition of %s" % namespace.metadata.name)
            print(str(ex))
            failed_check_condition += 1

    namespaces_failed = failed_cleanup + failed_check_condition

    print("Finish clean up script")
    return {
        'namespaces_cleaned' : cleaned,
        "namespaces_scanned" : len(namespaces.items),
        "namespaces_failed": namespaces_failed,
        "namespaces_failed_check_condition": failed_check_condition,
        "namespaces_failed_cleanup": failed_check_condition,
    }

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
