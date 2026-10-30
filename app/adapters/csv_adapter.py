from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.core.mapping import AccountMapping


@dataclass(frozen=True)
class ParsedRow:
    posted_at: date
    amount: int
    description: str
    running_balance: int
    raw_type: str | None
    row: int
    flags: tuple[Literal["empty_description", "empty_raw_type"], ...]


@dataclass(frozen=True)
class ParsedFile:
    """Rows are in chronological order and index is the position"""

    rows: tuple[ParsedRow, ...]
    file_hash: str


def convert_date(date_str: str, date_format: str) -> date: ...


def convert_amount(amount_str: str) -> int: ...


class CsvAdapter:
    """Adapter for CSV files. Stateless, and is built once"""

    def _get_file_hash(self, file_bytes: bytes) -> str: ...

    def _convert_to_text(self, file_bytes: bytes) -> str: ...

    def _parse_file(self, text: str, mapping: AccountMapping) -> list[ParsedRow]: ...

    def _normalize_ordering(
        self, file_rows: list[ParsedRow], row_order: Literal["asc", "desc"]
    ) -> list[ParsedRow]: ...

    def parse(self, file_bytes: bytes, mapping: AccountMapping) -> ParsedFile: ...
