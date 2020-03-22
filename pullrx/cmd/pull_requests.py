import threading

from pullrx.github import client
from pullrx.mr import collections
from pullrx.store import mem


class PRListThread(threading.Thread):

    def __init__(self, org_name, repo_name, store_key_path, store,
                 request_context=None, request_params=None):
        super().__init__()
        self._org = org_name
        self._repo = repo_name
        self._key_path = store_key_path
        self._store = store
        self._context = request_context or client.default_context()
        self._params = request_params or {'state': 'all', 'per_page': '100'}

    def run(self):
        pr_client = client.PullRequestClient(self._context)
        prs = pr_client.list(self._org, self._repo, params=self._params)
        self._store.set_keyed_path(self._key_path, prs)


def org_repos(org_name):
    # all repos for the given org indexed by repo name
    repo_client = client.RepoClient(request_context=client.default_context())
    repos = repo_client.list_for_org(org_name)
    store = mem.MemoryStore(org_name + '/repos')
    store.update_from_array(repos, 'name')
    return store


def org_repos_with_prs(org_name):
    # all repos for the given org indexed by repo name with PRs in the pull_requests key of the repo dict
    named_repos = org_repos(org_name)
    pr_threads = []
    for repo_name in named_repos.keys():
        pr_thread = PRListThread(
            org_name, repo_name,
            mem.MemoryStore.build_keyed_path(repo_name, 'pull_requests'),
            named_repos)
        pr_thread.start()
        pr_threads.append(pr_thread)

    for t in pr_threads:
        t.join()

    return named_repos


def print_org_repos_summary(org_name):
    repo_store = org_repos_with_prs(org_name)
    print("Pull Request summary for %s organization" % org_name)
    print("%s total repos" % len(repo_store.keys()))
    print("------------------------")
    for repo_name, data in repo_store.items():
        pr_list = data['pull_requests']
        print("Repo name: %s" % repo_name)
        print("Total PRs (open+closed): %s" % len(pr_list))
        print("Total open PRs: %s" % (collections.sum_list(
            pr_list, lambda pr: pr['state'] == 'open')))
        print("Total closed PRs: %s" % (collections.sum_list(
            pr_list, lambda pr: pr['state'] == 'closed')))
        print("Total draft PRs: %s" % (collections.sum_list(
            pr_list, lambda pr: pr['draft'] is True)))
        print("---")


print_org_repos_summary('ramda')
