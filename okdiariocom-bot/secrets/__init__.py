import os.path


def get_secret(name):
    if os.path.isfile('/run/secrets/' + name):
        with open('/run/secrets/' + name, 'r') as content_file:
            return content_file.read().replace('\n', '')
    return os.getenv(name) or ''
