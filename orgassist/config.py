import yaml

class Config:

    VALID_KEYS = [
        'instances',
        'xmpp',
        'defaults',
    ]

    def __init__(self, path):

        with open(path) as f:
            self._data = yaml.load(f)

        self.validate()

    def validate(self):
        "Validate config file structure"
        # TODO: Fail on error.

    def __getattr__(self, key):
        "Proxy access to valid fields of config"
        if key in self.VALID_KEYS:
            return self._data[key]
        return super().__getattribute__(self, key)
