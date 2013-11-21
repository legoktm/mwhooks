import base64
import json
import requests


def make_request(url):
    url = 'https://gerrit.wikimedia.org/r/' + url
    r = requests.get(url)
    try:
        valid_json = r.text[5:]
        return json.loads(valid_json)
    except ValueError:
        # It's base64?
        return base64.decodestring(r.text)


def get_files_changed(changeid, rev='current'):
    """
    Returns a dict like:
    {
    "AbuseFilter.php": {
        "lines_inserted": 4,
        "lines_deleted": 1
    }

    If the value is 0, the key is ommitted

    """
    url = 'changes/{0}/revisions/{1}/files/'.format(changeid, rev)
    data = make_request(url)
    return data


def get_file_content(changeid, path, rev='current'):
    url = 'changes/{0}/revisions/{1}/files/{2}/content'.format(changeid, rev, path)
    return make_request(url)

#get_file_content('I1eac8c8466bed79a1ee0479ecfe2038d3e77f949', 'hooks.txt')