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

# no new deployment for days specified by MAX_AGE, default to 5
class InactiveDeploymentCondition(object):
    def __init__(self, api_client_v1beta1, max_inactive_days = 5):
        self.max_inactive_days = int(max_inactive_days)
        self.api_client = api_client_v1beta1

    def satisfy(self, namespace):
        """return true if no active deployments"""

        print("%s: Checking inactive condition." % namespace.metadata.name)
        deployments = self.api_client.list_namespaced_deployment(namespace.metadata.name)

        def is_active(deployment_condition):
            timezone = deployment_condition.last_update_time.tzinfo
            return (datetime.datetime.now(timezone) - deployment_condition.last_update_time).days <= self.max_inactive_days

        # at least one deployment is updated within max_inactive_days days, we consider this namespace active
        active = any(map(lambda d: any(map(lambda c: is_active(c), d.status.conditions)), deployments.items))

        return not active

# branch is deleted in the given existing branches
class VSTSBranchDeletedCondition(object):
    def __init__(self, vsts_pat):
        """Form a VSTS Branch is deleted condition

        :param vsts_pat: VSTS Pat that has Code Reading permission
        """
        self.credentials = BasicAuthentication('', vsts_pat)

    def satisfy(self, namespace):
        print("%s: Checking deleted branch condition." % namespace.metadata.name)
        # vsts_base_url -- a vsts base url like: https://your-acount.visualstudio.com/DefaultCollection
        vsts_base_url = namespace.metadata.annotations["vsts_base_url"]
        vsts_repository_id = namespace.metadata.annotations["vsts_repository_id"]

        connection = VssConnection(base_url=vsts_base_url, creds=self.credentials)
        self.client = connection.get_client('vsts.git.v4_0.git_client.GitClient')
        self.branches = set([branch.name for branch in self.client.get_branches(vsts_repository_id)])
        return namespace.metadata.name not in self.branches