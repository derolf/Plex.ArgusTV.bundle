# -*- coding: utf-8 -*-

import functools

class Log:
    class O:
        pass
    log = O()
    @classmethod
    def Error(cls, s):
        cls.log.log.Error(s)
        pass
    @classmethod
    def Info(cls, s):
        cls.log.log.Info(s)
        pass
    @classmethod
    def Debug(cls, s):
        cls.log.log.Info(s)
        pass

def log_exception(func):
    """
    Decorates a function to log exceptions as errors. Exceptions are also raised again.
    :param logger:
    :return:
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            Log.Error(e)
            raise e
    return wrapper
