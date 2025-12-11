from enum import Enum

class TwoFAMethods(str,Enum):
    totp = 'totp'
    sms = 'sms'

class TwoFactorAuthLogAttemptType(str, Enum):
    setup = "setup"
    verify = "verify"
    failed_attempt = "failed_attempt"
    disabled = "disable"