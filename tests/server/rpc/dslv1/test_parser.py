from unittest import TestCase
from feeluown.server.dslv1 import Parser
from feeluown.server.excs import FuoSyntaxError


class TestParser(TestCase):
    """
    FIXME: 由于懒得构造 Token 序列，所以下面的测试都不正交
    """
    def test_read_cmd_error(self):
        text = "'hello world'"
        with self.assertRaises(FuoSyntaxError):
            Parser(text).parse()

    def test_no_token(self):
        with self.assertRaises(FuoSyntaxError):
            Parser('').parse()

    def test_parse_cmd_furi(self):
        source = "play fuo://local/songs/1"
        parser = Parser(source)
        request = parser.parse()
        self.assertEqual(request.cmd, 'play')
        self.assertEqual(request.cmd_args, ['fuo://local/songs/1'])

    def test_parse_cmd_unquote_string(self):
        source = "play 晴天"
        parser = Parser(source)
        request = parser.parse()
        self.assertEqual(request.cmd, 'play')
        self.assertEqual(request.cmd_args, ['晴天'])

    def test_parse_cmd_options_1(self):
        """test if parser can find error in option expr"""
        source = "status [artist=]"
        parser = Parser(source)
        with self.assertRaises(FuoSyntaxError):
            parser.parse()

    def test_parse_cmd_options_2(self):
        """test if parser parse success"""
        source = "play 晴天 [artist=周杰伦] "
        parser = Parser(source)
        request = parser.parse()
        self.assertEqual(request.cmd, 'play')
        self.assertEqual(request.cmd_args, ['晴天'])
        self.assertEqual(request.cmd_options, {'artist': '周杰伦'})

    def test_parse_cmd_options_3(self):
        """test if ok when there is no cmd option"""
        req = Parser('p []').parse()
        self.assertEqual(req.cmd, 'p')
        self.assertEqual(req.cmd_options, {})

    def test_parse_cmd_options_4(self):
        """test if ok when there is no cmd option"""
        source = 'p [a,b=c]'
        req = Parser(source).parse()
        self.assertEqual(req.cmd, 'p')
        self.assertEqual(req.cmd_options, {'a': True, 'b': 'c'})

    def test_parse_value_true_to_True(self):
        source = "p [a=true] "
        req = Parser(source).parse()
        self.assertEqual(req.cmd_options, {'a': True})

    def test_parse_value_false_to_False(self):
        source = "p [a=false] "
        req = Parser(source).parse()
        self.assertEqual(req.cmd_options, {'a': False})

    def test_parse_req_options(self):
        source = "play hay [artist='miao'] #: json"
        req = Parser(source).parse()
        self.assertEqual(req.options, {'json': True})

    def test_parse_req_options_2(self):
        """test if ok when there is empty req option """
        source = "play #:"
        req = Parser(source).parse()
        self.assertEqual(req.options, {})

    def test_token_after_req(self):
        source = "play #: miao miao"
        with self.assertRaises(FuoSyntaxError):
            Parser(source).parse()

    def test_parse_heredoc(self):
        source = "play << EOF"
        req = Parser(source).parse()
        self.assertEqual(req.has_heredoc, True)
        self.assertEqual(req.heredoc_word, 'EOF')
