from . import templates

class Assistant:
    """
    """

    def __init__(self, name, cfg, scheduler):
        self.scheduler = scheduler
        self.name = name
        self.cfg = cfg
        self._validate_config()

    def _validate_config(self):
        "Simple config validation - fail early"
        assert 'org' in self.cfg
        assert 'opts' in self.cfg

        assert 'boss' in self.cfg
        assert 'jid' in self.cfg['boss']

    def register_xmpp_bot(self, bot):
        boss = self.cfg['boss']
        bot.add_dispatch(boss['jid'], boss.get('resource', None),
                         self.handle_message)

    def register_irc_bot(self, bot):
        raise NotImplementedError

    def handle_message(self, respond, sender, message):
        """
        Handle command sent by the Boss.
        """
        print("GOT MESSAGE!", respond, sender, message)

        respond(templates.get('DONT_UNDERSTAND'))
