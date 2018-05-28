import logging
from sleekxmpp import ClientXMPP

from orgassist import templates
from . import Message

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
        if msg['type'] not in ('chat', 'normal'):
            log.warning('Unknown message type: %r %r', msg, msg['type'])
            return

        to_jid = msg.get_to()
        from_jid = msg.get_from()
        resource = to_jid.resource

        def respond(response):
            "Closure to simplify responding"
            self.send_message(from_jid, response)

        print("----------------------")
        print("From: ", from_jid, "To: ", to_jid)
        print("Body: %r" % msg)

        # Dispatch direct (to resource) or generic (to JID)
        callback = self.dispatch_map.get((from_jid.bare, resource), None)
        if callback is None:
            callback = self.dispatch_map.get((from_jid.bare, None), None)

        # If unknown - ignore
        if callback is None:
            respond(templates.get('DONT_KNOW'))
            return

        # Construct a Message using bot-generic API
        message = Message(msg['body'], from_jid.full, respond)

        callback(message)

    def send_message(self, jid, message):
        "Send a message"
        self.client.send_message(jid, message)

    def close(self):
        "Disconnect / close threads"
        self.client.abort()
