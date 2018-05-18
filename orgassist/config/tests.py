import unittest
from .config import Config, ConfigError

# pylint: disable=protected-access

class TestConfig(unittest.TestCase):
    "Test Config class"

    def setUp(self):
        "Create config"
        test_data = {
            'key_int': 42,
            'key_str': '42',
            'key_lst': [1, 2, 3],
            'key_dict': {
                'a': 1,
                'b': 2,
                'c': 3,
            },

            'key_lst_emb': [
                {'a': 1},
                {'b': 2},
                {'c': 3},
            ],

            'key_lst_mixed': [
                {'a': 1},
                [1, 2, 3],
                42,
            ],

            'deep': {
                'deeper': {
                    'deepest': 1,
                }
            }
        }
        self.config = Config.from_dict(test_data)

    def test_basic_get(self):
        "Test getting values from config"

        value = self.config.get('key_int', assert_type=int)
        self.assertEqual(value, 42)

        with self.assertRaises(ConfigError):
            self.config.get('key_int', assert_type=str)

        with self.assertRaises(ConfigError):
            self.config.get('key_invalid', required=True)

        value = self.config.get('key_invalid', required=False)
        self.assertIsNone(value)

        value = self.config.get('key_invalid', default=24)
        self.assertEqual(value, 24)

        value = self.config.get('key_lst', assert_type=list)
        self.assertTrue(isinstance(value, list))
        self.assertIn(1, value)
        self.assertIn(2, value)

    def test_embedded_get(self):
        "Test reading embedded dicts"
        value = self.config.get('key_dict', assert_type=dict)
        # Wrapped will be Config - not dict
        self.assertTrue(isinstance(value, Config))

        # Same with a dot-access
        value = self.config.key_dict
        self.assertTrue(isinstance(value, Config))

        # Various getting methods
        self.assertEqual(value.a, 1)
        self.assertEqual(value.get('b'), 2)

        # Can get multiple levels deep
        value = self.config.get('key_dict.a', assert_type=int)
        self.assertEqual(value, 1)

        value = self.config.get('key_dict',
                                assert_type=dict,
                                wrap=False)
        # Will be a dict if we disable wrapping
        self.assertTrue(isinstance(value, dict))

        value = self.config.get('key_lst_emb', assert_type=list)

        # List of configs
        self.assertTrue(isinstance(value, list))
        self.assertTrue(isinstance(value[0], Config))
        self.assertEqual(value[0].a, 1)

        self.assertEqual(value[0]._partial, 'key_lst_emb[0]')

    def test_deep(self):
        "Test behaviour of deep dictionaries"

        value = self.config.deep.deeper
        self.assertEqual(value.deepest, 1)
        self.assertEqual(value._partial,
                         'deep.deeper')
        unused = self.config.get_unused()
        self.assertNotIn('deep.deeper.deepest', unused)


    def test_marking(self):
        "Test marking of used values"

        # Mark few
        value = self.config.key_int
        value = self.config.key_dict.a
        self.config.get('key_dict').get('c')

        unused = self.config.get_unused()

        # What wasn't touched?
        self.assertIn('key_str', unused)

        # key_dict was read wrapped - so shouldn't be marked as unused
        self.assertNotIn('key_dict', unused)

        # And should be marked as used.
        self.assertNotIn('key_dict', self.config._marked)

        self.assertIn('key_dict.b', unused)

        # After reading whole dict unwrapped - it's marked as a whole
        self.config.get('key_dict', wrap=False)
        self.assertIn('key_dict', self.config._marked)

        # Embedded dict in list is completely unused now:
        self.assertIn('key_lst_emb[0].a', unused)
        self.assertIn('key_lst_emb[1].b', unused)

        # Touch embedded value
        value = self.config.get('key_lst_emb')[0]
        value.get('a')

        # And now isn't, but 'b' still is.
        unused = self.config.get_unused()
        self.assertNotIn('key_lst_emb[0].a', unused)
        self.assertIn('key_lst_emb[1].b', unused)

        # If I read it whole unwrapped - all get used
        value = self.config.get('key_lst_emb', wrap=False)
        unused = self.config.get_unused()
        self.assertNotIn('key_lst_emb', unused)
        self.assertNotIn('key_lst_emb[1].b', unused)

        # Mixed was never used
        self.assertIn('key_lst_mixed', unused)
