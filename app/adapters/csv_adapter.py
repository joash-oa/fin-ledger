import csv
import hashlib
import io
import itertools
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from app.core.exceptions import CsvFileParseException, ErrorCode
from app.core.mapping import AccountMapping

# Pattern is defined according to doc rules under Amounts section.
AMOUNT_PATTERN = re.compile(r"-?[0-9]+(\.[0-9]{1,2})?")

MAPPED_FIELDS = ["posted_at", "amount", "description", "running_balance", "raw_type"]

FlagType = Literal["empty_description", "empty_raw_type"]

# Defines what year/month/day indices are for each date format
DATE_FORMAT_INDICES = {
    "YYYY MM DD": (0, 1, 2),
    "MM DD YYYY": (2, 0, 1),
    "DD MM YYYY": (2, 1, 0),
}


@dataclass(frozen=True)
class ParsedRow:
    posted_at: date
    amount: int
    description: str
    running_balance: int
    raw_type: str | None
    row: int
    flags: tuple[FlagType, ...]


@dataclass(frozen=True)
class ParsedFile:
    """Rows are in chronological order and index is the position"""

    rows: tuple[ParsedRow, ...]
    file_hash: str


def convert_date(date_str: str, date_format: str) -> date:
    if date_format not in DATE_FORMAT_INDICES:
        raise ValueError(f"Invalid date format: {date_format!r}")

    date_vals = re.split(r"[^0-9]+", date_str)
    if len(date_vals) != 3:
        raise ValueError(f"Invalid date format: {date_str!r}")

    year_index, month_index, day_index = DATE_FORMAT_INDICES[date_format]
    if (
        len(date_vals[year_index]) != 4
        or len(date_vals[month_index]) not in (1, 2)
        or len(date_vals[day_index]) not in (1, 2)
    ):
        raise ValueError(f"Invalid date format: {date_str!r}")

    year, month, day = (
        int(date_vals[year_index]),
        int(date_vals[month_index]),
        int(date_vals[day_index]),
    )
    try:
        return date(year=year, month=month, day=day)
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str!r}") from None


def convert_amount(amount_str: str) -> int:
    if not AMOUNT_PATTERN.fullmatch(amount_str):
        raise ValueError(f"Invalid amount format: {amount_str!r}")
    return int(Decimal(amount_str) * 100)


class CsvAdapter:
    """Adapter for CSV files. Stateless, and is built once"""

    @staticmethod
    def _get_file_hash(file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def _convert_to_text(file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise CsvFileParseException(
                message="Invalid CSV format: Unsupported encoding",
                error_code=ErrorCode.INVALID_ENCODING,
            ) from None

    @staticmethod
    def _get_value_in_record(
        field_name: str, record: list[str], column_indices: dict[str, int]
    ) -> str:
        index = column_indices[field_name]
        if index >= len(record):
            return ""
        return record[index]

    @staticmethod
    def _parse_required_field[T](
        field_name: str,
        field_value: str,
        row_number: int,
        error_code: ErrorCode,
        converter: Callable[[str], T],
    ) -> T:
        if not field_value:
            raise CsvFileParseException(
                message=f"Required field {field_name!r} is missing.",
                error_code=ErrorCode.MISSING_VALUE,
                row=row_number,
                field=field_name,
            )

        try:
            converted_value = converter(field_value)
        except ValueError:
            raise CsvFileParseException(
                message=f"Parse {field_name!r} error: {field_value!r} given",
                error_code=error_code,
                row=row_number,
                field=field_name,
            ) from None

        return converted_value

    @staticmethod
    def _parse_header(header: list[str], mapping: AccountMapping) -> dict[str, int]:
        mapping_dict = mapping.model_dump()
        parsed_header = {}
        if all(not value for value in header):
            raise CsvFileParseException(
                message="No header row found in CSV file",
                error_code=ErrorCode.NO_ROWS,
            )

        for index, header_val in enumerate(header):
            header_val = header_val.strip()
            if header_val in parsed_header:
                continue
            parsed_header[header_val] = index

        column_indices = {}
        for column in MAPPED_FIELDS:
            if mapping_dict[column] not in parsed_header:
                raise CsvFileParseException(
                    message=f"No column named {mapping_dict[column]!r} (mapped to {column!r}).",
                    error_code=ErrorCode.MISSING_COLUMN,
                    row=1,
                    field=column,
                )

            column_indices[column] = parsed_header[mapping_dict[column]]

        return column_indices

    def _parse_record(
        self,
        column_indices: dict[str, int],
        record: list[str],
        row_number: int,
        mapping: AccountMapping,
    ) -> ParsedRow:
        posted_at_value = self._get_value_in_record(
            field_name="posted_at", record=record, column_indices=column_indices
        )
        posted_at = self._parse_required_field(
            field_name="posted_at",
            field_value=posted_at_value,
            row_number=row_number,
            error_code=ErrorCode.UNPARSEABLE_DATE,
            converter=lambda value: convert_date(value, mapping.date_format),
        )

        amount_value = self._get_value_in_record(
            field_name="amount", record=record, column_indices=column_indices
        )
        amount = self._parse_required_field(
            field_name="amount",
            field_value=amount_value,
            row_number=row_number,
            error_code=ErrorCode.UNPARSEABLE_AMOUNT,
            converter=convert_amount,
        )

        running_balance_value = self._get_value_in_record(
            field_name="running_balance", record=record, column_indices=column_indices
        )
        running_balance = self._parse_required_field(
            field_name="running_balance",
            field_value=running_balance_value,
            row_number=row_number,
            error_code=ErrorCode.UNPARSEABLE_AMOUNT,
            converter=convert_amount,
        )

        flags: list[FlagType] = []
        description = self._get_value_in_record(
            field_name="description", record=record, column_indices=column_indices
        )
        if not description:
            flags.append("empty_description")

        raw_type = self._get_value_in_record(
            field_name="raw_type", record=record, column_indices=column_indices
        )
        if not raw_type:
            raw_type = None
            flags.append("empty_raw_type")

        return ParsedRow(
            posted_at=posted_at,
            amount=amount,
            running_balance=running_balance,
            description=description,
            raw_type=raw_type,
            row=row_number,
            flags=tuple(flags),
        )

    def _parse_file(self, text: str, mapping: AccountMapping) -> list[ParsedRow]:
        text_stream = io.StringIO(text)

        csv_reader = csv.reader(text_stream)
        header = next(csv_reader, None)
        if not header:
            raise CsvFileParseException(
                message="No header row found in CSV file",
                error_code=ErrorCode.NO_ROWS,
            )

        column_indices = self._parse_header(header, mapping)
        parsed_rows = []
        for row_number, record in enumerate(csv_reader, start=2):
            normalized_record = [record_value.strip() for record_value in record]
            if all(not value for value in normalized_record):
                continue

            parsed_row = self._parse_record(
                column_indices=column_indices,
                record=normalized_record,
                row_number=row_number,
                mapping=mapping,
            )
            parsed_rows.append(parsed_row)

        if not parsed_rows:
            raise CsvFileParseException(
                message="Invalid CSV format: Blank rows",
                error_code=ErrorCode.NO_ROWS,
            )
        return parsed_rows

    @staticmethod
    def _normalize_ordering(
        file_rows: list[ParsedRow], row_order: Literal["asc", "desc"]
    ) -> list[ParsedRow]:
        for prev, current in itertools.pairwise(file_rows):
            if row_order == "asc" and current.posted_at < prev.posted_at:
                raise CsvFileParseException(
                    message=f"Dates are out of order for this file: Row {current.row} {current.posted_at} is earlier than Row {prev.row} {prev.posted_at}",
                    error_code=ErrorCode.DATES_OUT_OF_ORDER,
                    row=current.row,
                    field="posted_at",
                )

            if row_order == "desc" and current.posted_at > prev.posted_at:
                raise CsvFileParseException(
                    message=f"Dates are out of order for this file: Row {current.row} {current.posted_at} is later than Row {prev.row} {prev.posted_at}",
                    error_code=ErrorCode.DATES_OUT_OF_ORDER,
                    row=current.row,
                    field="posted_at",
                )

        ordered_rows = file_rows if row_order == "asc" else list(reversed(file_rows))
        return ordered_rows

    def parse(self, file_bytes: bytes, mapping: AccountMapping) -> ParsedFile:
        file_hash = self._get_file_hash(file_bytes)

        text = self._convert_to_text(file_bytes)

        parsed_rows = self._parse_file(text=text, mapping=mapping)

        ordered_rows = self._normalize_ordering(
            file_rows=parsed_rows, row_order=mapping.row_order
        )

        return ParsedFile(
            file_hash=file_hash,
            rows=tuple(ordered_rows),
        )
