# Create a documentation page on mw.o
# for a hook documented in docs/hooks.txt
# Authors:
#  Legoktm
#
# Released into the public domain
#
# syntax: python create_onwiki.py HookName

import os
import sys
import pywikibot
import requests


template = """
{{{{MediaWikiHook|name={name}|version={version}|args={args}|source={source}|summary={summary}}}}}

== Details ==

{details}
"""


def parse(text):
    """
    Parses docs/hooks.txt
    """
    text = text.split('events to the MediaWiki code.')[1]
    text = text.split('More hooks might')[0]
    text = text.strip()
    hooks = {}

    inhook = False
    cur_hook = {'vars': []}
    for line in text.splitlines():
        line = line.strip()

        if inhook:
            if line.startswith(('&', '$')):
                sp = line.split(':')
                if len(sp) == 1:
                    # False positive. This is the worst :/
                    cur_hook['desc'] += ' ' + line
                else:
                    #print sp
                    cur_hook['vars'].append({'name': sp[0], 'desc': sp[1].strip()})
            elif line:
                # Continuing the description...
                cur_hook['desc'] += ' ' + line
            elif not line:
                inhook = False
                hooks[cur_hook['name']] = cur_hook
                cur_hook = {'vars': []}

        elif line.startswith('\''):
            inhook = True
            #print line
            cur_hook['name'] = line.split('\'')[1]
            # Note: hook names can have :'s in them
            cur_hook['desc'] = line.split('\':')[1].lstrip()
    return hooks


def find_usage(name):
    """
    Attempt to find the script that calls this hook
    """
    for dirpath, dirnames, filenames in os.walk(os.path.expanduser('~/projects/mediawiki/vagrant/mediawiki/includes')):
        for fname in filenames:
            if fname.endswith('.php'):
                path = os.path.join(dirpath, fname)
                with open(path) as f:
                    for line in f.read().splitlines():
                        if name in line and 'wfRunHooks' in line:  # TODO: Improve this
                            return fname


def get_version_info(name):
    """
    This is ugly, but it works-ish.
    TODO: Rewrite this to use git blame or something.
    """
    latest = 23  # Assume this is master.
    while True:
        latest -= 1
        url = 'https://raw.github.com/wikimedia/mediawiki-core/REL1_{0}/docs/hooks.txt'.format(latest)
        r = requests.get(url)
        if "'{0}'".format(name) in r.text:
            continue
        else:
            return latest + 1


def format_template(source, name):
    """
    Returns the autogenerated wiki documentation
    @param source: text of docs/hooks.txt
    """
    info = parse(source)[name]
    # Probably not a good idea to guess the .0 part but oh well.
    version = '1.' + str(get_version_info(name)) + '.0'
    usage = find_usage(name) or ''
    args = ', '.join(n['name'] for n in info['vars'])
    details = ''
    for var in info['vars']:
        details += '* {0}: {1}\n'.format(var['name'], var['desc'])
    #print details
    text = template.format(
        name=name,
        version=version,
        source=usage,
        summary=info['desc'],
        args=args,
        details=details,
    )
    return text


def create_wikipage(source, name):
    """
    Creates the page if it doesn't already exist
    """
    site = pywikibot.Site('www', 'mediawiki', u'Legoktm')
    page = pywikibot.Page(site, u'Manual:Hooks/' + name)
    if page.exists():
        print 'Page already exists, aborting.'
    else:
        print 'Creating page...'
        temp = format_template(source, name)
        page.put(temp, 'Autogenerating hook documentation!')

if __name__ == '__main__':
    fname = os.path.expanduser('~/projects/mediawiki/vagrant/mediawiki/docs/hooks.txt')
    with open(fname) as f:
        text = f.read()

    create_wikipage(text, sys.argv[1])
