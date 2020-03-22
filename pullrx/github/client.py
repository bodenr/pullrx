import requests

from pullrx.github import creds


GITHUB_API_HOSTNAME = 'api.github.com'
GITHUB_V3_JSON_ACCEPT = 'application/vnd.github.v3+json'
GITHUB_DRAFT_PR_ACCEPT = 'application/vnd.github.shadow-cat-preview+json'


def default_context():
    return RequestContext(
        auth=creds.credentials_from_file_store(
            GITHUB_API_HOSTNAME).to_auth_tuple())


class RequestContext(object):

    def __init__(self, base_url=None, headers=None, timeout=5, auth=None):
        self.base_url = base_url or 'https://' + GITHUB_API_HOSTNAME + '/'
        if not self.base_url.endswith('/'):
            self.base_url += '/'

        self.headers = headers or {'Accept': GITHUB_V3_JSON_ACCEPT}
        if 'Accept' not in self.headers:
            self.headers['Accept'] = GITHUB_V3_JSON_ACCEPT

        self.timeout = timeout
        self.auth = auth
        # TODO: retries

    def build_url(self, url):
        if url.startswith('/'):
            url = url[1:]
        return self.base_url + url


class GithubClient(object):
    # https://developer.github.com/v3/

    def __init__(self, request_context=None):
        self._context = request_context or default_context()

    def _get(self, url, request_context, params=None):
        response = requests.get(url, params=params,
                                timeout=request_context.timeout,
                                headers=request_context.headers,
                                auth=request_context.auth)

        if response.status_code >= 300:
            response.raise_for_status()

        return response

    def get(self, url, request_context=None, params=None):
        context = request_context or self._context
        response = self._get(context.build_url(url), context,
                             params=params)
        return response.json()

    def list(self, url, request_context=None, params=None):
        context = request_context or self._context
        response = self._get(context.build_url(url), context, params=params)
        resources = response.json()

        while response.links.get('next'):
            response = self._get(response.links.get('next')['url'], context)
            resources.extend(response.json())

        return resources


class PullRequestClient(GithubClient):
    # https://developer.github.com/v3/pulls/
    
    def __init__(self, request_context=None, use_draft=True):
        super().__init__(request_context=request_context)
        if use_draft:
            self._context.headers['Accept'] = GITHUB_DRAFT_PR_ACCEPT

    def get(self, owner, repo, pull_number, request_context=None, params=None):
        url = "repos/%s/%s/pulls/%s" % (owner, repo, pull_number)
        return super().get(url, request_context=request_context, params=params)

    def list(self, owner, repo, request_context=None, params=None):
        url = "repos/%s/%s/pulls" % (owner, repo)
        return super().list(url, request_context=request_context, params=params)


class RepoClient(GithubClient):
    # https://developer.github.com/v3/repos/

    def __init__(self, request_context=None):
        super().__init__(request_context=request_context)

    def list_for_org(self, org, request_context=None, params=None):
        url = "orgs/%s/repos" % org
        return super().list(url, request_context=request_context, params=params)

    def list_for_user(self, username, request_context=None, params=None):
        url = "users/%s/repos" % username
        return super().list(url, request_context=request_context, params=params)
