from enum import Enum

class Tokens(Enum):
    IF = "<IF>"
    ENDIF = "<ENDIF>"
    ELSE = "<ELSE>"
    FOR = "<FOR>"
    ENDFOR = "<ENDFOR>"
    WHILE = "<WHILE>"
    ENDWHILE = "<ENDWHILE>"
    RETURN = "<RETURN>"
    RAISE = "<RAISE>"
    TRY = "<TRY>"
    EXCEPT = "<EXCEPT>"

    PASS = "<PASS>"
    ASSERT = "<ASSERT>"
    BREAK = "<BREAK>"



