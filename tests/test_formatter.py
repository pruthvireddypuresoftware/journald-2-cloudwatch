from unittest import TestCase
from unittest.mock import patch, mock_open

from .identity_doc import IDENTITY_DOC, IDENTITY_DOC_STR
from main import Format, IDENTITY_DOC_URL

class FormatterTest(TestCase):
    def test_default_formatting(self):
        ''' test formatting is same as default '''
        for fmt, kwargs in [
            ['string', {}],
            ['abc {d}', {'d': 123}],
            ['{b} {a}', {'a': 123, 'b': 456}],
            ['formatting {x:03}', {'x': 2}],
        ]:
            self.assertEqual(Format(fmt, **kwargs), fmt.format(**kwargs))

        self.assertRaises(KeyError, Format, '{a}')

    def test_formatting_defaults(self):
        ''' test the a|b|c fallthrough defaulting '''
        self.assertEqual(Format('xyz {a|b|c} 123', a=1, b=2, c=3), 'xyz 1 123')
        self.assertEqual(Format('xyz {a|b|c} 123', b=2, c=3), 'xyz 2 123')
        self.assertEqual(Format('xyz {a|b|c} 123', c=3), 'xyz 3 123')
        self.assertRaises(KeyError, Format, 'xyz {a|b|c} 123')

    def test_string_formatting(self):
        ''' test when key is a string '''
        self.assertEqual(Format('xyz {a|b|"hello"} 123', b=5), 'xyz 5 123')
        self.assertEqual(Format('xyz {a|b|"hello"} 123'), 'xyz hello 123')
        self.assertEqual(Format("xyz {a|b|'hello'} 123"), 'xyz hello 123')

    @patch('urllib.request.urlopen', mock_open(read_data=IDENTITY_DOC_STR))
    def test_identity_doc_formatting(self):
        ''' test variables in the identity doc '''
        self.assertEqual(Format('xyz {$instanceId}'), 'xyz ' + IDENTITY_DOC['instanceId'])
        self.assertEqual(Format('xyz {$region}'), 'xyz ' + IDENTITY_DOC['region'])
        self.assertEqual(Format('xyz {invalid|$region}'), 'xyz ' + IDENTITY_DOC['region'])

    @patch('urllib.request.urlopen', mock_open(read_data=IDENTITY_DOC_STR))
    def test_journald_vars(self):
        ''' test some convenience vars made from journald fields '''
        # test $unit
        self.assertEqual(Format('xyz {$unit}', _SYSTEMD_UNIT='systemd_unit', **{'$unit': 'not used'}), 'xyz systemd_unit')
        self.assertEqual(Format('xyz {$unit}', USER_UNIT='user_unit', _SYSTEMD_UNIT='not used', **{'$unit': 'not used'}), 'xyz user_unit')
        # test templated unit
        self.assertEqual(Format('xyz {$unit}', _SYSTEMD_UNIT='systemd_unit@arg.service', **{'$unit': 'not used'}), 'xyz systemd_unit.service')
        # test no unit name found
        self.assertEqual(Format('xyz {$unit}', **{'$unit': 'hello'}), 'xyz hello')
        # docker container
        self.assertEqual(Format('xyz {$docker_container}', _SYSTEMD_UNIT='docker.service', CONTAINER_NAME='container', **{'$docker_container': 'not used'}), 'xyz container')
        self.assertEqual(Format('xyz {$docker_container}', CONTAINER_NAME='container', **{'$docker_container': 'hello'}), 'xyz hello')
        self.assertEqual(Format('xyz {$docker_container}', _SYSTEMD_UNIT='docker.service', **{'$docker_container': 'hello'}), 'xyz hello')

    @patch('urllib.request.urlopen', mock_open(read_data=IDENTITY_DOC_STR))
    def test_default_special_vars(self):
        ''' test when $var not found '''
        self.assertEqual(Format('xyz {$other}', **{'$other': 'hello'}), 'xyz hello')
        self.assertRaises(KeyError, Format, 'xyz {$not_found}')
