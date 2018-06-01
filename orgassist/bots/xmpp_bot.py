
from sleekxmpp import ClientXMPP
from sleekxmpp.thirdparty import socks

from orgassist import templates
from . import Message
from . import log

class XmppBot:
    """
    Interfaces with Jabber and identifies bosses by JID and resource.
    """
    def __init__(self, connect_cfg):
        "Initialize XMPP bot"
        # (Sender JID, [local resource]) -> callback
        self.dispatch_map = {}

        self.jid = connect_cfg.jid
        self.connect(connect_cfg)

    def connect(self, config):
        "Connect to XMPP server"
        socks_cfg = config.get('socks_proxy', required=False)
        if socks_cfg is not None:
            # TODO: Doesn't work yet. Doesn't implement a makelist
            socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5,
                                  socks_cfg.get('host', assert_type=str),
                                  socks_cfg.get('port', assert_type=int),
                                  rdns=True)
            socket = socks.socksocket
        else:
            socket = None

        self.client = ClientXMPP(self.jid, config.password, socket=socket)
        proxy_cfg = config.get('http_proxy', required=False)
        if proxy_cfg is not None:
            self.client.use_proxy = True
            self.client.proxy_config = {
                'host': proxy_cfg.host,
                'port': proxy_cfg.get('port', assert_type=int),
                'username': proxy_cfg.get('username', required=False),
                'password': proxy_cfg.get('password', required=False),
            }
            print("Configured proxy", self.client.proxy_config)

        use_tls = config.get('tls', default=True)

        # Events
        self.client.add_event_handler("session_start", self._session_start)
        self.client.add_event_handler("message", self.message_dispatch)

        log.info("Initializing connection to XMPP")
        ip = config.get('ip', required=False)
        if ip is not None:
            print("port", config.port)
            port = config.get('port', default=5222, assert_type=int)
            self.client.connect((ip, port), use_tls=use_tls)
        else:
            self.client.connect(use_tls=use_tls)

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

        log.debug("Got message:")
        log.debug("From: %s, to: %s", from_jid, to_jid)
        log.debug("Body: %r", msg)

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
