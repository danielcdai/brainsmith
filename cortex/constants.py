from enum import Enum


class ERROR_MESSAGES(str, Enum):
    def __str__(self) -> str:
        return super().__str__()
    
    DEFAULT = (
        lambda err="": f'{"Something went wrong :/" if err == "" else "[ERROR: " + str(err) + "]"}'
    )
    INVALID_CRED = "Invalid credentials, please check your oauth provider settings."