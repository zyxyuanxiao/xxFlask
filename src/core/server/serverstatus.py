# -*- coding:utf-8 -*-


class ServerStatus(object):
    CLOSED = (0, 'closed')
    INIT = (1, 'init')
    OPEN = (2, 'open')
    CLOSING = (3, 'closing')
    UNKNOWN = (-1, 'unknown')
    VALID_STATUS = (CLOSED, INIT, OPEN, CLOSING)
    current = CLOSED

    @classmethod
    def status_by_code(cls, code):
        for s in cls.VALID_STATUS:
            if s[0] == code:
                return s
        return cls.UNKNOWN

    @classmethod
    def get(cls):
        return cls.current

    @classmethod
    def in_state(cls, status):
        return cls.current is status

    @classmethod
    def change(cls, status):
        if status not in cls.VALID_STATUS:
            raise Exception('unknown status')
        cls.current = status
