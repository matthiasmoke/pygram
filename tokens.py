from enum import Enum

class Tokens(Enum):
    IF = "<IF>"
    END_IF = "<END_IF>"
    ELSE = "<ELSE>"
    FOR = "<FOR>"
    END_FOR = "<END_FOR>"
    WHILE = "<WHILE>"
    END_WHILE = "<END_WHILE>"
    RETURN = "<RETURN>"
    RAISE = "<RAISE>"
    TRY = "<TRY>"
    END_TRY = "<END_TRY>"
    EXCEPT = "<EXCEPT>"
    END_EXCEPT = "<END_EXCEPT>"
    FINALLY = "<FINALLY>"
    END_FINALLY = "<END_FINALLY>"
    DEF = "<DEF>"
    END_DEF = "<END_DEF>"
    ASYNC = "<ASYNC>"
    AWAIT = "<AWAIT>"
    WITH = "<WITH>"
    END_WITH = "<END_WITH>"
    PASS = "<PASS>"
    ASSERT = "<ASSERT>"
    BREAK = "<BREAK>"



