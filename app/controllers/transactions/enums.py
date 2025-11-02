from enum import Enum

class NotificationStateChoice(Enum):
    read = 'read'
    delivered = 'delivered'
    undelivered = 'undelivered'

class TRXType(str, Enum):
    deposit = 'deposit'
    withdraw = 'withdraw'