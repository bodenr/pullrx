from os import path
from urllib import parse


DEFAULT_CRED_FILE = path.expanduser('~') + '/.git-credentials'


class Credentials(object):

    def __init__(self, hostname, username, password, protocol='https'):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.protocol = protocol

    def to_auth_tuple(self):
        return self.username, self.password


def credentials_from_file_store(hostname, cred_file_path=DEFAULT_CRED_FILE, protocol='https'):
    # parse username and password from a .git-credentials compatible file
    # each line looks like: https://user:pass@example.com
    with open(cred_file_path, 'r') as cred_file:
        line = cred_file.readline().strip()
        if line:
            parts = parse.urlparse(line)
            if parts.scheme == protocol and parts.netloc:
                user_pass = parts.netloc.split('@')[0]
                cred_host = parts.netloc.split('@')[1]
                if cred_host == hostname:
                    return Credentials(hostname, user_pass.split(':')[0],
                                       user_pass.split(':')[1], protocol=protocol)

    raise PermissionError("No credentials found for %s//%s" % (protocol, hostname))
