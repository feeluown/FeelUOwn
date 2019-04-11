class FuoProtocolError(Exception):
    pass


class FuoSyntaxError(FuoProtocolError):
    """fuo syntax error

    >>> e = FuoSyntaxError(column=9, text="play 'fuo")
    >>> print(e.human_readabe_msg)
    FuoSyntaxError:
      > play 'fuo
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
        basic_msg = self.__class__.__name__ + ':'
        if str(self):
            basic_msg += ' ' + str(self)
        if self.column is not None:
            tpl = '{msg}\n  > {text}\n    {arrow}'
            msg = tpl.format(text=self.text,
                             msg=basic_msg,
                             arrow=(self.column) * ' ' + '^')
            return msg
        return basic_msg
