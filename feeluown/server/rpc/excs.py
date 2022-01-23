class FuoProtocolError(Exception):
    pass


class FuoSyntaxError(FuoProtocolError):
    """fuo syntax error

    >>> e = FuoSyntaxError('invalid syntax', column=9, text="play 'fuo")
    >>> print(e.human_readabe_msg)
    invalid syntax
      play 'fuo
               ^
    """
    def __init__(self, *args, column=None, text=None):
        super().__init__(*args)
        # both column and text should be None or neither is None
        assert not (column is None) ^ (text is None)

        self.column = column
        self.text = text

    @property
    def human_readabe_msg(self):
        if self.column is not None:
            tpl = '{msg}\n  {text}\n  {arrow}'
            msg = tpl.format(text=self.text,
                             msg=str(self),
                             arrow=(self.column) * ' ' + '^')
            return msg
        return str(self)
