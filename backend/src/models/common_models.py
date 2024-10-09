from enum import Enum


class ConsumerEnum(Enum):
    FAST_CHAT = 'FCH'
    SYSTEM = 'SYS'
    IMAGE = 'IMG'


class ProviderEnum(Enum):
    OPEN_AI = 'OAI'


def get_provider_choices():
    return [(member.value, member.name) for member in ProviderEnum]


def get_consumer_choices():
    return [(member.value, member.name) for member in ConsumerEnum]
