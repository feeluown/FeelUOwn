import re
import sys
from collections import namedtuple, deque

from .excs import FuoSyntaxError


# 注：下面很多正则都是从 jinja2/lexer.py 和 pygments/lexer.py 拷贝过来
TOKEN_NAME = sys.intern('name')
TOKEN_FURI = sys.intern('furi')  # fuo uri
TOKEN_STRING = sys.intern('string')
TOKEN_UNQUOTE_STRING = sys.intern('unquote-string')
TOKEN_WHITESPACE = sys.intern('whitespace')
TOKEN_INTEGER = sys.intern('integer')
TOKEN_FLOAT = sys.intern('float')
TOKEN_COMMA = sys.intern('comma')
TOKEN_LBRACKET = sys.intern('lbracket')
TOKEN_RBRACKET = sys.intern('rbracket')
TOKEN_EQ = sys.intern('eq')
TOKEN_REQ_DELIMETER = sys.intern('req_delimeter')
TOKEN_HEREDOC_OP = sys.intern('heredoc_op')
TOKEN_HEREDOC_WORD = sys.intern('heredoc_word')

name_re = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
whitespace_re = re.compile(r'\s+')
string_re = re.compile(r"('([^'\\]*(?:\\.[^'\\]*)*)'"
                       r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)
furi_re = re.compile(r'fuo://[/\w+\d+]*')
unquote_string_re = re.compile(r'[\w-]+')
integer_re = re.compile(r'\d+')
float_re = re.compile(r'(?<!\.)\d+\.\d+')
newline_re = re.compile(r'(\r\n|\r|\n)')
comma_re = re.compile(r',')
lbracket_re = re.compile(r'\[')
rbracket_re = re.compile(r'\]')
req_delimeter_re = re.compile(r'#:')
equal_re = re.compile(r'=')
heredoc_op_re = re.compile(r'<<')
heredoc_word_re = re.compile(r'EOF|END')

Token = namedtuple('Token', ['column', 'type_', 'value'])

base_rules = [
    (TOKEN_FURI, furi_re),
    (TOKEN_NAME, name_re),
    (TOKEN_WHITESPACE, whitespace_re),
    (TOKEN_FLOAT, float_re),
    (TOKEN_INTEGER, integer_re),
    (TOKEN_STRING, string_re),
    (TOKEN_UNQUOTE_STRING, unquote_string_re),
    (TOKEN_EQ, equal_re),
]

root_rules = base_rules + [
    (TOKEN_LBRACKET, lbracket_re),
    (TOKEN_REQ_DELIMETER, req_delimeter_re),
    (TOKEN_HEREDOC_OP, heredoc_op_re),
]

bracket_rules = base_rules + [
    (TOKEN_COMMA, comma_re),
    (TOKEN_RBRACKET, rbracket_re),
]

req_rules = base_rules + [
    (TOKEN_COMMA, comma_re),
    (TOKEN_HEREDOC_OP, heredoc_op_re),
]

heredoc_rules = [
    (TOKEN_WHITESPACE, whitespace_re),
    (TOKEN_HEREDOC_WORD, heredoc_word_re),
]

state_rules = {
    'root': root_rules,
    'bracket': bracket_rules,
    'req': req_rules,
    'heredoc': heredoc_rules,
}


def get_state_expect(state):
    if state == 'bracket':
        return ']'
    raise ValueError('state: %s has no need' % str(state))


class Lexer:
    """fuo 协议请求的词法分析器

    >>> list(token.value for token in Lexer().tokenize('play fuo://local'))
    ['play', 'fuo://local']
    >>> text = "play 'fuo://local/songs1 # 晴天 - 周杰伦'"
    >>> list(token.value for token in Lexer().tokenize(text))
    ['play', 'fuo://local/songs1 # 晴天 - 周杰伦']
    >>> text2 = "search 哈哈 [artist=喵]  #: less"
    >>> list(token.value for token in Lexer().tokenize(text2))
    ['search', '哈哈', '[', 'artist', '=', '喵', ']', '#:', 'less']
    """

    def tokenize(self, source):
        def err(msg, column):
            raise FuoSyntaxError(msg, text=source, column=column)

        pos = 0
        # 栈是 lexer 实现时常用的一个数据结构
        # 在处理括号是否闭合等场景十分有用，很多 lexer
        # 实现时会给 token 带上 #pop 标记，这个标记也是用来配合栈的
        state_stack = deque()
        state = 'root'
        while 1:
            for rule in state_rules[state]:
                type_, regex = rule
                m = regex.match(source, pos)
                if m is None:
                    continue
                value = m.group()
                if type_ == TOKEN_STRING:
                    value = value[1:-1]
                elif type_ == TOKEN_INTEGER:
                    value = int(value)
                elif type_ == TOKEN_FLOAT:
                    value = float(value)
                token = Token(pos, type_, value)

                if type_ == TOKEN_LBRACKET:
                    state_stack.append(state)
                    state = 'bracket'
                elif type_ == TOKEN_REQ_DELIMETER:
                    if state != 'root':
                        expect = get_state_expect(state)
                        err("expected token '%s' at pos %d" % (expect, pos), pos)
                    state_stack.append(state)
                    state = 'req'
                elif type_ == TOKEN_RBRACKET:
                    if state != 'bracket':
                        err("unexpected token ']' at pos %d" % pos, pos)
                    state = state_stack.pop()
                elif type_ == TOKEN_HEREDOC_OP:
                    if state not in ('root', 'req'):
                        err("unexpected token '<<' at pos %d" % pos)
                    state = 'heredoc'
                if token.type_ != TOKEN_WHITESPACE:
                    yield token
                pos = m.end()
                break
            else:
                if pos == len(source):
                    if state not in ('root', 'req', 'heredoc'):
                        expect = get_state_expect(state)
                        err("expected token '%s', but end of line reached" % expect, pos)
                    else:
                        break
                else:
                    err("unexpected token '%s' at pos %d" % (source[pos], pos), pos)
