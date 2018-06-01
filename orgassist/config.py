import os
import yaml

"""
Handle config files with beautiful API
"""

class ConfigError(Exception):
    "Error while parsing config - show message and quit"

class Config:
    """
    Nice API for a configuration
    """

    def __init__(self, data, partial=None, path=None):
        "Create config out of dictionary"
        self._data = data
        self._partial = partial
        self._config_path = path

    @staticmethod
    def from_file(path):
        "Create config by reading a file"
        with open(path) as f:
            data = yaml.load(f)
        return Config(data, path=path)

    def get(self, key, default=None, required=True,
            assert_type=None, wrap=True):
        """
        Get a key from config.

        - Key can use dots to navigate nested config parts.
        - If key doesn't exist and is not required - the default value is returned
        - If key is required - ConfigError is raised.
        - Changing default to non-None assumes value is not required.
        - If assert_type is not None, the value type is asserted checked.
        - If wrap is True - treat dicts as sub-configs
        """
        key_split = key.split('.')

        # Find the deepest dictionary with the required value
        current = self._data
        for key_part in key_split[:-1]:
            if key_part in current:
                current = current[key_part]
            else:
                if required is True and default is None:
                    msg = "Required config key '%s' not found at level '%s'"
                    raise ConfigError(msg % (self._key_desc(key), key_part))
                else:
                    return default

        if key_split[-1] not in current:
            if required is True and default is None:
                msg = "Required config key '%s' not found"
                raise ConfigError(msg % self._key_desc(key))
            else:
                return default

        value = current[key_split[-1]]
        if assert_type is not None and not isinstance(value, assert_type):
            msg = "Key '%s' has type %s, but should have type %s"
            raise ConfigError(msg % (self._key_desc(key), type(value), assert_type))

        if wrap is True:
            # Wrap dictionaries
            if isinstance(value, dict):
                return Config(value, partial=key, path=self._config_path)

            # Wrap lists of dictionaries
            elif isinstance(value, list):
                if not value:
                    return value
                if set(type(el) for el in value) == {dict}:
                    return [
                        Config(element, partial='%s[%d]' % (key, i), path=self._config_path)
                        for i, element in enumerate(value)
                    ]
        return value

    def interpret_path(self, path):
        """
        Paths are relative to the config file and can use ~ to refer to HOME
        """
        path = os.path.expanduser(path)
        path = os.path.join(self._config_path, path)
        return path

    def get_path(self, key, default=None, required=True):
        "Get a path from config. Expand user ~, $HOME variables"
        value = self.get(key, default=default,
                         required=required, assert_type=str)
        if value is not None:
            value = self.interpret_path(value)
        return value

    def items(self, wrap=True):
        "Dict-like interface with wrapping"
        for key, value in self._data.items():
            if isinstance(value, dict) and wrap:
                yield (key, Config(value, partial=key, path=self._config_path))
            else:
                yield (key, value)

    def __iter__(self):
        "Allow casting config to dictionary"
        return self._data.items().__iter__()

    def __bool__(self):
        "For checking if config is empty"
        return bool(self._data)

    def _key_desc(self, key):
        "Describe key correctly, even if config is partial"
        if self._partial is None:
            return key
        return "(%s).%s" % (self._partial, key)

    def __getattr__(self, key):
        "Proxy access to valid fields of config"
        return self.get(key, required=True)

    def __repr__(self):
        return '<Config partial=%s %r>' % (self._partial, self._data)
