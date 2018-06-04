from kubernetes import client, config
from conditions import AnnotationAllowCleanupIsTrueCondition, InactiveDeploymentCondition, VSTSRefDeletedCondition
import os

def clean():
    try:
        print("Loading in-cluster config")
        config.load_incluster_config()
    except:
        print("Failed to load in-cluster config. Using KUBECONFIG, if not specified, default config")
        config.load_kube_config()

    v1api = client.CoreV1Api()
    v1beta1api = client.AppsV1beta1Api()

    # reading environment variable
    vsts_token = os.environ['VSTS_PAT']
    max_namespace_inactive_days = os.environ['MAX_NAMESPACE_INACTIVE_HOURS']

    cleanup_conditions = [
        AnnotationAllowCleanupIsTrueCondition(),
        #InactiveDeploymentCondition(v1beta1api, max_namespace_inactive_days), 
        VSTSRefDeletedCondition(vsts_token),
    ]

    namespaces = v1api.list_namespace()
    cleaned = 0
    for namespace in namespaces.items:
        print("-- Checking namespace %s --" % namespace.metadata.name)
        
        # clean up if all of the conditions are met
        cleanup = all(c.satisfy(namespace) for c in cleanup_conditions)
        
        # delete namespace
        if cleanup:
            print("Cleaning up namespace %s" % namespace.metadata.name)
            # real cleanup will be enable later once it's tested
            v1api.delete_namespace(namespace.metadata.name, client.V1DeleteOptions())
            cleaned += 1

    print("Finish clean up script")
    return { 'namespaces_cleaned' : cleaned, "namespaces_scanned" :  namespaces.items:}

def main():
    start = time.time()
    eventdict = { 'name' : 'aeva.cleaner', 'time' : start, 'eventtype' : 'json'}
    try
        stats = clean()
        eventdict.update(stats)
        eventdict['succes'] = True
     except Exception as e:
            result["error"] =  str(e)
            result["success"] = False
            raise e
    finally
            eventdict['ElapsedTime'] = time.time() - start
            print(json.dumps(eventdict))
    
if __name__ == '__main__':
    main()

