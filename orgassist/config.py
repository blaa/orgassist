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

    def __init__(self, data, partial=None, path=None, base=None):
        "Create config out of dictionary"
        self._data = data
        self._partial = partial
        self._config_path = path

        # Base level of config which gathers information on all read keys.
        self._base = base or self
        self._marked = set()

    @staticmethod
    def from_file(path):
        "Create a config by reading a file"
        with open(path) as handler:
            data = yaml.load(handler)
        return Config(data, path=path)

    @staticmethod
    def from_dict(data):
        "Create a config from a dictionary"
        return Config(data, path='<dict>')

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
        key_full = '%s.%s' % (self._partial, key) if self._partial else key

        # Find the deepest dictionary with the required value
        current = self._data
        for key_part in key_split[:-1]:
            if key_part in current:
                current = current[key_part]
            else:
                if default is not None or not required:
                    return default
                msg = "Required config key '%s' not found at level '%s'"
                raise ConfigError(msg % (self._key_desc(key), key_part))

        if key_split[-1] not in current:
            if default is not None or not required:
                return default
            msg = "Required config key '%s' not found"
            raise ConfigError(msg % self._key_desc(key))

        value = current[key_split[-1]]
        if assert_type is not None and not isinstance(value, assert_type):
            msg = "Key '%s' has type %s, but should have type %s"
            raise ConfigError(msg % (self._key_desc(key), type(value), assert_type))

        if wrap is True:
            # Wrap dictionaries
            if isinstance(value, dict):
                return Config(value, partial=key_full,
                              path=self._config_path, base=self._base)

            # Wrap lists of dictionaries (or handle an empty list)
            elif isinstance(value, list):
                types_inside = set(type(el) for el in value)
                if not value or types_inside == {dict}:
                    return [
                        Config(element, partial='%s[%d]' % (key_full, i),
                               path=self._config_path, base=self._base)
                        for i, element in enumerate(value)
                    ]

        # Direct, or unwrapped access - mark
        # It's our class. Stupid.
        # pylint: disable=protected-access
        self._base._mark(key, self._partial)

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
            key_full = '%s.%s' % (self._partial, key) if self._partial else key
            if isinstance(value, dict) and wrap:
                yield (key, Config(value, partial=key_full,
                                   path=self._config_path, base=self._base))
            else:
                yield (key, value)

    def _mark(self, key, partial):
        "Mark key as used"
        full_key = partial + '.' if partial else ''
        full_key += key
        self._marked.add(full_key)

    def get_unused(self):
        """
        Go through config keys and list those which weren't used
        """
        assert self._base == self, "Call get_unused on main config object"

        unused = []
        def analyze_level(level, partial=""):
            "Recursively analyse while storing data in `unused'"
            for key, value in level.items():
                key_full = "%s.%s" % (partial, key) if partial else key

                if key in self._marked:
                    # This key was used; direct value read
                    # or unwrapped dictionary read.
                    continue

                if isinstance(value, dict):
                    # Check access level deeper.
                    analyze_level(value, key_full)
                    continue
                elif isinstance(value, list) and value:
                    # Non empty list of dicts has wrapping too.
                    types_inside = set(type(el) for el in value)
                    if types_inside == {dict}:
                        # Check deeper
                        for i, entry in enumerate(value):
                            next_partial = "%s[%d]" % (key_full, i)
                            analyze_level(entry, next_partial)
                        continue

                # Normal key entry, or mixed list - check if was used.
                if key_full not in self._marked:
                    unused.append(key_full)

        analyze_level(self._data, "")
        return unused

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
