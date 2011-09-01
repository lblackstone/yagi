import httplib2

import yagi.config
import yagi.log
import yagi.serializer.atom

with yagi.config.defaults_for('atompub') as default:
    pass

LOG = yagi.log.logger


def topic_url(key):
    host = yagi.config.get('atompub', 'host') or '127.0.0.1'
    port = yagi.config.get('atompub', 'port', default=80)
    if yagi.config.get_bool('atompub', 'use_https'):
        scheme = 'https'
    else:
        scheme = 'http'
    return '%s://%s:%s/%s' % (scheme, host, port, key)


def notify(notifications):
    auth_user = yagi.config.get('atompub', 'user', default=None)
    auth_key = yagi.config.get('atompub', 'key', default=None)
    conn = httplib2.Http()
    if auth_user and auth_key:
        conn.add_credentials(auth_user, auth_key)
    for notification in notifications:
        yagi.serializer.atom.dumps(notifications)
        notification_body = yagi.serializer.atom.dumps([notification])
        headers = {'Content-Type': 'application/atom+xml'}
        conn.follow_all_redirects = True
        try:
            endpoint = topic_url(notification['event_type'])
            LOG.info('Sending message to %s' % endpoint)
            resp, content = conn.request(endpoint, 'POST',
                                     body=notification_body, headers=headers)
            if resp.status != 201:
                LOG.error('ATOM Pub resource create failed for %s' % topic_url)

        except Exception, e:
            LOG.error('Error sending notification to ATOM Pub resource%s\n\n%s'
                     % (topic_url, e))
            raise
