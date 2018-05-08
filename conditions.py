import datetime
from vsts.vss_connection import VssConnection
from msrest.authentication import BasicAuthentication

# has annotation 'allowCleanup': 'true'
class AnnotationAllowCleanupIsTrueCondition(object):
    def satisfy(self, namespace):
        """return true if it has 'allowCleanup': 'true' in annotations"""

        print("%s: Checking annotation condition." % namespace.metadata.name)
        annotations = namespace.metadata.annotations
        return annotations is not None and ('allowCleanup' in annotations) and annotations['allowCleanup'].lower() == 'true'

# no new deployment for days specified by MAX_AGE, default to 1
class InactiveDeploymentCondition(object):
    def __init__(self, api_client_v1beta1, max_inactive_days = 1):
        self.max_inactive_days = int(max_inactive_days)
        self.api_client = api_client_v1beta1

    def satisfy(self, namespace):
        """return true if no active deployments"""

        print("%s: Checking inactive condition." % namespace.metadata.name)
        deployments = self.api_client.list_namespaced_deployment(namespace.metadata.name)

        def is_active(deployment_condition):
            timezone = deployment_condition.last_update_time.tzinfo
            return (datetime.datetime.now(timezone) - deployment_condition.last_update_time).days <= self.max_inactive_days

        def checkdeployment(d):
            return any([is_active(c) for c in d.status.conditions])

        # at least one deployment is updated within max_inactive_days days, we consider this namespace active
        return not any([checkdeployment(d) for d in  deployments.items])

# branch is deleted in the given existing branches
class VSTSBranchDeletedCondition(object):
    def __init__(self, vsts_pat):
        """Form a VSTS Branch is deleted condition

        :param vsts_pat: VSTS Pat that has Code Reading permission
        """
        self.credentials = BasicAuthentication('', vsts_pat)
        self.vsts_base_url_key = "vsts_base_url"
        self.vsts_repository_id_key = "vsts_repository_id"
        self.branch_key = "branch"

    def satisfy(self, namespace):
        print("%s: Checking deleted branch condition." % namespace.metadata.name)
        
        if (
            namespace.metadata.annotations is None 
            or self.vsts_base_url_key not in namespace.metadata.annotations
            or self.vsts_repository_id_key not in namespace.metadata.annotations
            or self.branch_key not in namespace.metadata.annotations
        ):
            print("Can't find vsts info in %s" % namespace.metadata.name)
            return False

        # vsts_base_url -- a vsts base url like: https://your-acount.visualstudio.com/DefaultCollection
        vsts_base_url = namespace.metadata.annotations[self.vsts_base_url_key]
        vsts_repository_id = namespace.metadata.annotations[self.vsts_repository_id_key]
        branch_name = namespace.metadata.annotations[self.branch_key]

        connection = VssConnection(base_url=vsts_base_url, creds=self.credentials)
        client = connection.get_client('vsts.git.v4_0.git_client.GitClient')
        all_branches = [branch.name for branch in client.get_branches(vsts_repository_id)]
        return branch_name not in all_branches