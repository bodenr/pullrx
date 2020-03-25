import datetime
import json
import pytz
import threading

from dateutil import relativedelta
from dateutil import parser

from pullrx.github import client
from pullrx.mr import collections
from pullrx.store import mem


# NOTE: this module is just a scratchpad / playground

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


class OrgPRs(object):

    def __init__(self, org_name, list_of_prs=None):
        self.org_name = org_name
        self.prs = list_of_prs or []

    def default_file_name(self):
        return "/tmp/%s_prs.json" % self.org_name

    def save(self, file_name=None):
        file_name = file_name or self.default_file_name()
        with open(file_name, 'w') as f:
            json.dump({
                'org_name': self.org_name,
                'pull_requests': self.prs
            }, f)

    def load(self, file_name=None):
        file_name = file_name or self.default_file_name()
        with open(file_name) as f:
            data = json.load(f)
            self.org_name = data['org_name']
            self.prs = data['pull_requests']


def org_repos(org_name):
    # all repos for the given org indexed by repo name
    repo_client = client.RepoClient(request_context=client.default_context())
    repos = repo_client.list_for_org(org_name)
    store = mem.MemoryStore(org_name + '/repos')
    store.update_from_list(repos, 'name')
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


def org_prs_to_file(org_name, file_name=None):
    repos_with_prs = org_repos_with_prs(org_name)
    org_prs = OrgPRs(org_name)
    for repo_name, repo_data in repos_with_prs.items():
        org_prs.prs.extend(repo_data['pull_requests'])

    org_prs.save(file_name=file_name)
    print("%s pull requests saved to %s" % (org_name, file_name or org_prs.default_file_name()))


def print_org_repos_summary(org_name):
    repo_store = org_repos_with_prs(org_name)
    org_prs = collections.collect_dict_keys(['pull_requests'], *repo_store.values())
    print("Pull Request summary for %s organization" % org_name)
    print("%s total repos" % len(repo_store.keys()))
    print("%s total PRs (open+closed)" % len(org_prs))
    print("%s total open PRs" % collections.sum_list(org_prs, lambda pr: pr['state'] == 'open'))
    print("%s total closed PRs" % collections.sum_list(org_prs, lambda pr: pr['state'] == 'closed'))
    print("%s total draft PRs" % collections.sum_list(org_prs, lambda pr: pr['draft'] is True))
    print("\nBreakdown by repo")
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


def save_org_prs_to_file(org_name, file_name=None):
    org_prs_to_file(org_name, file_name=file_name)


def munk_with_time():
    t1 = '2011-04-10T20:09:31Z'
    t2 = '2011-04-10T20:09:31Z'
    print(t1 < t2)

    d1 = parser.parse(t1)
    print("github fmt: %s" % d1)
    now = datetime.datetime.utcnow()
    last_week = now + relativedelta.relativedelta(weeks=-1)
    print("now: %s" % now)
    print("a week ago: %s" % last_week)


def print_ramda_repo_summary():
    print_org_repos_summary('ramda')


def org_pull_requests_list(org_name, cache_file=None):
    org_pulls = OrgPRs(org_name)
    try:
        org_pulls.load(file_name=cache_file)
    except FileNotFoundError:
        save_org_prs_to_file(org_name, file_name=cache_file)
        org_pulls.load(file_name=cache_file)

    return org_pulls.prs


class WeeklyPulls(object):

    def __init__(self, relative_day=relativedelta.MO):
        self._relative_day = relative_day
        self._weekly_pulls = {}

    def add_pull(self, pull_data):
        merged = pull_data.get('merged_at')
        created = pull_data.get('created_at')

        if merged:
            merged_week = parser.parse(merged).date() + relativedelta.relativedelta(weekday=self._relative_day(-1))
            if merged_week not in self._weekly_pulls:
                self._weekly_pulls[merged_week] = {
                    'merged': 0,
                    'created': 0
                }
            self._weekly_pulls[merged_week]['merged'] += 1

        if created:
            created_week = parser.parse(created).date() + relativedelta.relativedelta(weekday=self._relative_day(-1))

            if created_week not in self._weekly_pulls:
                self._weekly_pulls[created_week] = {
                    'merged': 0,
                    'created': 0
                }
            self._weekly_pulls[created_week]['created'] += 1

    def __str__(self):
        rep = ""
        for week_of in sorted(self._weekly_pulls.keys(), reverse=True):
            pull_stats = self._weekly_pulls[week_of]
            rep += "Week of %s... Created: %s, Merged: %s\n" % (week_of, pull_stats['created'], pull_stats['merged'])

        return rep


def org_pull_requests_week_over_week(org_name):
    pulls = org_pull_requests_list(org_name)
    sorted_by_creation = sorted(pulls, key=lambda pr_data: pr_data['created_at'], reverse=True)
    earliest = parser.parse(sorted_by_creation[-1]['created_at'])
    now = datetime.datetime.now(tz=pytz.UTC)

    print("Weekly Pull Request summary for %s organization" % org_name)
    print("------------")
    print("Total PRs (open+closed+draft): %s" % len(pulls))
    print("Full date range: %s through %s" % (earliest.date(), now.date()))
    print("------------")

    weekly_pulls = WeeklyPulls()
    for pull in pulls:
        weekly_pulls.add_pull(pull)

    print(weekly_pulls)


org_pull_requests_week_over_week('ramda')
