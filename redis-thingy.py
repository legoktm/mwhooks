#!/usr/bin/python
import create_onwiki
import json
import gerrit
import logging
import pipes
import redis
import subprocess
import yaml
import os

with open(os.path.expanduser('~/.config.yaml')) as f:
    config = yaml.load(f)

REDIS_DB = config['redis']['db']
REDIS_HOST = config['redis']['host']
PREFIX = config['sync']['github']['redis_prefix']
CLIENT_KEY = PREFIX  # We use the same thing for now

logging.basicConfig(
    format='%(asctime)s %(message)s',
    filename=os.path.expanduser('~/logs'),
    level=logging.INFO
)

if __name__ == '__main__':
    logging.info('Attempting to Redis connection to %s', REDIS_HOST)
    red = redis.StrictRedis(host=REDIS_HOST, db=REDIS_DB)
    logging.info('Redis connection to %s succeded', REDIS_HOST)

    while True:
        data = json.loads(red.brpop(CLIENT_KEY)[1])
        if not 'type' in data :
            logging.debug('No type for event')
            continue
        if not 'change' in data:
            logging.debug('No change for event')
            continue
        if data['type'] != 'change-merged':
            logging.debug('Change was not a merge')
            continue
        if data['change']['project'] != 'mediawiki/core':
            logging.debug('Change was not for mediawiki/core')
            continue
        if not 'patchset' in data:
            logging.debug('No patchset for event')
            continue
        if not 'docs/hooks.txt' in gerrit.get_files_changed(data['change']['id']):
            logging.debug('Change did not affect hooks.txt')
            continue
        logging.info('Found a merge modifying hooks.txt!')
        logging.debug(json.dumps(data))
        hookstxt = gerrit.get_file_content(data['change']['id'], 'docs/hooks.txt')

        #figure out what the new hook added was...
        name = ''  # FIXME
        logging.info('New hook is: "{0}"'.format(name))
        logging.info('Creating wikipage for hook')
        create_onwiki.create_wikipage(hookstxt, name)
        logging.info('Created wikipage for hook!')
        # Leave a comment
        # I totally stole this from gerrit-patch-uploader
        msg = 'A stub template for this hook has been created at <https://www.mediawiki.org/wiki/Manual:Hooks/{0}>. ' \
              'Please verify all the information there is correct, and improve it if necessary. Thanks!'.format(name)
        sha1 = data['patchset']['revision']
        msg = pipes.quote(msg)
        sha1 = pipes.quote(sha1)
        logging.info('Leaving comment on the changeset')
        p = subprocess.Popen(['ssh', 'gerrit', 'gerrit review %s -m %s' % (sha1, msg)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.communicate()
        if p.returncode != 0:
            logging.error('Comment was not added successfully')
        else:
            logging.info('Left a comment on the change!')