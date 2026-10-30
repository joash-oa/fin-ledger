from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_ENCODING = "invalid_encoding"
    NO_ROWS = "no_rows"
    MISSING_COLUMN = "missing_column"
    MISSING_VALUE = "missing_value"
    UNPARSEABLE_DATE = "unparseable_date"
    UNPARSEABLE_AMOUNT = "unparseable_amount"
    DATES_OUT_OF_ORDER = "dates_out_of_order"


class DuplicateEmailException(Exception):
    pass


class InvalidCredentialsException(Exception):
    pass


class InvalidSessionException(Exception):
    pass


class UserNotFoundException(Exception):
    pass


class DuplicateAccountException(Exception):
    pass


class AccountNotFoundException(Exception):
    pass


class CsvFileParseException(Exception):
    def __init__(
        self, message: str, error_code: ErrorCode, row: int | None, field: str | None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.row = row
        self.field = field
