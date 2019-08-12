r"""
fuo 请求解析器
~~~~~~~~~~~~~~~~~~~~

ps: 和常见的编程语言不一样，fuo 请求语法和 shell 命令的语法更相似，
理论上，我们可以参考 optparse 来实现解这个解析器，
但是第一作者(cosven)对 optparse 没啥太大的兴趣，而对编程语言的 parser
比较感冒，于是就以下面这种形式实现了这个 Parser。

上下文无关文法::

    expr: cmd (value)* (cmd_option)? (req_option)?
    req_option: REQ_DELIMETER options
    cmd_option: LBRACKET options RBRACKET
    options: ((option_expr)(COMMA option_expr)*)?
    option_expr: NAME (EQ value)
    values: (value)*
    value: NAME | STRING | INTEGER | FLOAT | FURI | UNQUOTE_STRING
    cmd: NAME

``search faint [artist="linkin park"]  #: json``

parse tree::

                                 expr
       /       /                  |                        \
      cmd    value            cmd_option                req_option
       |       |          /       |        \                 |      \
    'NAME'   STRING  LBRACKET option_expr RBRACKET   REQ_DELIMETER option_expr
       |       |        /    /    |     \      \              |        |
    'search' 'faint' '['  NAME   EQ   value    ']'           '#:'     NAME
                            |     |     |                              |
                        'artist' '='  STRING                         'json'
                                        |
                                   'linkin park'
"""

from .excs import FuoSyntaxError
from .lexer import Lexer
from .lexer import (
    TOKEN_NAME, TOKEN_FURI, TOKEN_STRING, TOKEN_UNQUOTE_STRING,
    TOKEN_INTEGER, TOKEN_FLOAT, TOKEN_COMMA,
    TOKEN_LBRACKET, TOKEN_RBRACKET, TOKEN_EQ, TOKEN_REQ_DELIMETER,
    TOKEN_HEREDOC_OP, TOKEN_HEREDOC_WORD,
)
from .data_structure import Request


class _EOF(Exception):
    pass


class Parser:
    """fuo 请求语法分析器

    使用递归下降思想实现，自顶向下，LL(1)。
    """

    def __init__(self, source):
        self.tokens = Lexer().tokenize(source)
        self._source = source

        self._end_column = len(self._source) - 1
        self._current_token = None  # one lookahead token

    def parse(self):
        cmd = self._parse_cmd()
        req = Request(cmd)
        try:
            req.cmd_args = self._parse_values()
            req.cmd_options = self.parse_cmd_options()
            req.options = self._parse_req_options()
            req.has_heredoc, req.heredoc_word = self._parse_heredoc()
        except _EOF:
            # 上述步骤出现 EOF 都属于正常情况
            pass
        else:
            # 检测是否剩余 token
            try:
                token = self._next_token()
            except _EOF:
                pass
            else:
                self._error(token.column)
        return req

    def _error(self, column):
        raise FuoSyntaxError('invalid syntax',
                             column=column,
                             text=self._source)

    def _next_token(self):
        token = self._current_token
        if token is None:
            try:
                token = next(self.tokens)
            except StopIteration:
                raise _EOF
        self._current_token = None
        return token

    def _parse_cmd(self):
        """
        cmd: NAME

        成功返回值，失败抛出 FuoSyntaxError 异常
        """
        try:
            token = self._next_token()
        except _EOF:
            raise FuoSyntaxError('invalid syntax: empty request')
        else:
            if token.type_ != TOKEN_NAME:
                self._error(token.column)
            return token.value

    def _parse_value(self):
        """
        value: NAME | STRING | INTEGER | FLOAT | FURI

        成功则返回值，否则返回 None
        """
        valid_types = (TOKEN_NAME, TOKEN_STRING, TOKEN_INTEGER,
                       TOKEN_FLOAT, TOKEN_FURI, TOKEN_UNQUOTE_STRING)
        try:
            token = self._next_token()
        except _EOF:
            return None
        else:
            if token.type_ in valid_types:
                return token.value
            self._current_token = token
            return None

    def _parse_values(self):
        """
        values: (value)*
        """
        values = []
        while 1:
            value = self._parse_value()
            if value is None:
                break
            values.append(value)
        return values

    def _parse_option_expr(self):
        """
        option_expr: NAME (EQ value)

        成功返回 (k,v) 元组，失败返回 (None, None)
        """
        token = self._next_token()
        if token.type_ == TOKEN_NAME:
            try:
                next_token = self._next_token()
            except _EOF:
                return token.value, True
            else:
                if next_token.type_ == TOKEN_EQ:
                    value = self._parse_value()
                    if value is None:
                        self._error(self._current_token.column)
                    elif value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    return token.value, value
                else:
                    self._current_token = next_token
                    return token.value, True
        self._current_token = token
        return None, None

    def _parse_options(self):
        """
        options: ((option_expr)(COMMA option_expr)*)?
        """
        options = {}
        while 1:
            k, v = self._parse_option_expr()
            if k is None:
                break
            options[k] = v
            try:
                next_token = self._next_token()
            except _EOF:
                break
            else:
                if next_token.type_ == TOKEN_COMMA:
                    continue
            self._current_token = next_token
            break
        return options

    def parse_cmd_options(self):
        """
        cmd_options: LBRACKET ((option_expr)(COMMA option_expr)*)? RBRACKET
        """
        token = self._next_token()
        if token.type_ != TOKEN_LBRACKET:
            self._current_token = token
            return {}
        cmd_options = self._parse_options()
        next_token = self._next_token()  # 消费 RBRACKET
        assert next_token.type_ == TOKEN_RBRACKET
        return cmd_options

    def _parse_req_options(self):
        next_token = self._next_token()  # 消费 REQ_DELIMETER
        if next_token.type_ != TOKEN_REQ_DELIMETER:
            self._current_token = next_token
            return {}
        return self._parse_options()

    def _parse_heredoc(self):
        token = self._next_token()
        if token.type_ != TOKEN_HEREDOC_OP:
            self._current_token = token
            return False, None
        try:
            next_token = self._next_token()
        except _EOF:
            self._error(self._end_column)
        else:
            assert next_token.type_ == TOKEN_HEREDOC_WORD
            return True, next_token.value
