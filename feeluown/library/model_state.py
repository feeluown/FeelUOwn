from enum import IntFlag


class ModelState(IntFlag):
    none = 0x00000000

    #: the model is created manually
    # the model identifier may not exist
    # the model fields values are not accurate
    artificial = 0x00000001

    #: the model identifier existence is proved
    # the model fields values are not accurate
    exists = 0x00000002

    #: the model identifier does not exist
    not_exists = 0x00000004

    #: the model identifier existence is proved and fields value are accurate
    # the model is a brief model
    cant_upgrade = exists | 0x00000010

    #: the model identifier existence is proved and fields value are accurate
    # the model is a normal model instead of a brief model
    upgraded = exists | 0x000000020
