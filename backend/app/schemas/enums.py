from enum import IntEnum


class MessageType(IntEnum):
    SYNC = 0
    AWARENESS = 1
    OTHER = 2
    # QUERY_AWARENESS = 2


class SyncMessagetype(IntEnum):
    SYNCSTEP1 = 0
    SYNCSTEP2 = 1
    UPDATE = 2
