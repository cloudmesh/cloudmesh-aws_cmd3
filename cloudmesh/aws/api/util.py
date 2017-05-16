

class append_docstring(object):

    def __init__(self, docstr):
        self._doc = docstr


    def __call__(self, fn):
        if not fn.__doc__:
            fn.__doc__ = ''

        fn.__doc__ = fn.__doc__ + self._doc
        return fn
