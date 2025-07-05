from enum import Enum

class UserRoleChoice(str, Enum):
    admin = "admin"
    staff = "staff"
    user = "user"


class ClientGenderChoice(str, Enum):
    male = 'male'
    female = 'female'
    custom = 'custom'