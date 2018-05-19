import logging
from sleekxmpp import ClientXMPP

from . import templates

log = logging.getLogger('xmpp-bot')

class XmppBot:
    """
    Interfaces with Jabber and identifies bosses by JID and resource.
    """

    def __init__(self, connect_cfg):
        "Initialize XMPP bot"
        # (Sender JID, [local resource]) -> callback
        self.dispatch_map = {}

        self.jid = connect_cfg.jid
        self.connect(connect_cfg.password)

    def connect(self, password):
        "Connect to XMPP server"
        self.client = ClientXMPP(self.jid, password)

        # Events
        self.client.add_event_handler("session_start", self._session_start)
        self.client.add_event_handler("message", self.message_dispatch)

        log.info("Initializing connection to XMPP")
        self.client.connect(use_tls=True)

    def _session_start(self, event):
        log.info('Starting XMPP session')
        self.client.send_presence()

    def add_dispatch(self, sender_jid, resource, callback):
        """
        Register callback to handle incoming messages from sender_jid
        directed to a given resource (can be None to mean "any").
        """
        key = (sender_jid, resource)
        if key in self.dispatch_map:
            raise Exception("Sender JID duplicated: %s" % sender_jid)
        self.dispatch_map[key] = callback

    def message_dispatch(self, msg):
        "Dispatch incoming message depending on the sender"
        print("message dispatch")
        if msg['type'] not in ('chat', 'normal'):
            log.warn('Unknown message type: %r %r', msg, msg['type'])
            return

        def respond(response):
            self.send_message(msg.get_from(), response)

        to_jid = msg.get_to()
        from_jid = msg.get_from()

        #to_jid.get_resource()
        # Destination resource
        #if '/' in msg.get_to():
        #    resource = msg.get_to().split('/')[1]
        #else:
        resource = to_jid.resource

        print("----------------------")
        print("From: ", from_jid, "To: ", to_jid)
        print("Body: %r" % msg)
        # Dispatch
        callback = self.dispatch_map.get((from_jid.bare, resource), None)
        if callback is None:
            callback = self.dispatch_map.get((from_jid.bare, None), None)

        if callback is None:
            respond(templates.get('DONT_KNOW'))

        callback(msg['body'], from_jid.full, respond)

    def send_message(self, jid, message):
        "Send a message"
        self.client.send_message(jid, message)

    def close(self):
        "Disconnect / close threads"
        self.client.abort()
