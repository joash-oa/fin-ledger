import hashlib
from datetime import date
from pathlib import Path

import pytest

from app.adapters.csv_adapter import CsvAdapter, ParsedRow, convert_amount, convert_date
from app.core.exceptions import CsvFileParseException, ErrorCode
from tests.factories import get_valid_mapping, make_csv_file


def get_csv_file_bytes(filename):
    file = Path(__file__).parent / "fixtures" / filename
    return file.read_bytes()


@pytest.fixture
def expected_rows() -> tuple[ParsedRow, ...]:
    return (
        ParsedRow(
            posted_at=date(2026, 9, 1),
            amount=250000,
            description="Payroll",
            running_balance=1200000,
            raw_type="ACH_CREDIT",
            row=2,
            flags=(),
        ),
        ParsedRow(
            posted_at=date(2026, 9, 2),
            amount=-50000,
            description="Con Edison",
            running_balance=1150000,
            raw_type="ACH_DEBIT",
            row=3,
            flags=(),
        ),
        ParsedRow(
            posted_at=date(2026, 9, 5),
            amount=-8542,
            description="Whole Foods Market",
            running_balance=1141458,
            raw_type="DEBIT_CARD",
            row=4,
            flags=(),
        ),
    )


def test_parse_file_success(expected_rows):
    file_bytes = get_csv_file_bytes("checking_basic.csv")
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert file_hash == parsed_file.file_hash
    assert parsed_file.rows == expected_rows


@pytest.mark.parametrize(
    "amount_str, expected_cents",
    [
        ("0.29", 29),
        ("1.15", 115),
        ("12.5", 1250),
        ("1234", 123400),
        ("-12.5", -1250),
        ("0.07", 7),
        ("-0.07", -7),
    ],
)
def test_valid_amount_conversion(amount_str: str, expected_cents: int):
    cents = convert_amount(amount_str)
    assert cents == expected_cents


@pytest.mark.parametrize(
    "amount_str",
    [
        "(12.50)",
        "$12.50",
        "1,250.00",
        "+12.50",
        "12.505",
        ".50",
        "5.",
        "abc",
        "1.2.3",
        "-",
    ],
)
def test_invalid_amount_conversion(amount_str: str):
    with pytest.raises(ValueError):
        _ = convert_amount(amount_str)


@pytest.mark.parametrize(
    "date_str, date_format, expected_date",
    [
        ("2026-03-12", "YYYY MM DD", date(2026, 3, 12)),
        ("2026/03/12", "YYYY MM DD", date(2026, 3, 12)),
        ("2026.03.12", "YYYY MM DD", date(2026, 3, 12)),
        ("01-05-2026", "MM DD YYYY", date(2026, 1, 5)),
        ("01/05/2026", "MM DD YYYY", date(2026, 1, 5)),
        ("01.05.2026", "MM DD YYYY", date(2026, 1, 5)),
        ("04-11-2026", "DD MM YYYY", date(2026, 11, 4)),
        ("04/11/2026", "DD MM YYYY", date(2026, 11, 4)),
        ("04.11.2026", "DD MM YYYY", date(2026, 11, 4)),
        ("2026-6-8", "YYYY MM DD", date(2026, 6, 8)),
    ],
)
def test_valid_date_conversion(date_str: str, date_format: str, expected_date: date):
    converted_date = convert_date(date_str, date_format)
    assert converted_date == expected_date


@pytest.mark.parametrize(
    "date_str, date_format",
    [
        ("12/2026/13", "YYYY MM DD"),
        ("2026-11-12", "MM DD YYYY"),
        ("2026-133", "DD MM YYYY"),
        ("2027.02.31", "YYYY MM DD"),
        ("2026-13-01", "YYYY MM DD"),
        ("31-04-2026", "DD MM YYYY"),
        ("2026/03/00", "YYYY MM DD"),
        ("03/12/26", "MM DD YYYY"),
        ("2026-03-12x", "YYYY MM DD"),
        ("abc", "YYYY MM DD"),
    ],
)
def test_invalid_date_conversion(date_str: str, date_format: str):
    with pytest.raises(ValueError):
        _ = convert_date(date_str, date_format)


def test_invalid_encoding_error():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-01,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-02,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(
        lines, encoding="cp1252"
    )  # é is 0xE9 in cp1252, which is invalid UTF-8

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.INVALID_ENCODING
    assert exc_info.value.row is None
    assert exc_info.value.field is None


def test_header_with_no_rows_error():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = ["Date,Amount,Description,Current balance,Type,Status"]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.NO_ROWS
    assert exc_info.value.row is None
    assert exc_info.value.field is None


def test_empty_file_raises_no_rows_error():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=b"", mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.NO_ROWS
    assert exc_info.value.row is None
    assert exc_info.value.field is None


def test_file_with_header_and_blank_rows():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "",
        "",
    ]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.NO_ROWS
    assert exc_info.value.row is None
    assert exc_info.value.field is None


def test_missing_columns_error():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Amount,Description,Current balance,Type,Status",
        "2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.MISSING_COLUMN
    assert exc_info.value.row == 1
    assert exc_info.value.field == "posted_at"


@pytest.mark.parametrize(
    "missing_field_line, mapping_key",
    [
        (",-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted", "posted_at"),
        ("2026-09-02,-14.00,Café Grumpy,,ACH_DEBIT,Posted", "running_balance"),
        ("2026-09-02,,Café Grumpy,11986.00,ACH_DEBIT,Posted", "amount"),
        ("2026-09-02,   ,Café Grumpy,11986.00,ACH_DEBIT,Posted", "amount"),
        ("2026-09-02,-14.00,Café Grumpy", "running_balance"),
    ],
)
def test_missing_value_error(missing_field_line: str, mapping_key: str):
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-01,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        missing_field_line,
    ]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.MISSING_VALUE
    assert exc_info.value.row == 3
    assert exc_info.value.field == mapping_key


def test_unparseable_date_error():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-08-41,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-02,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.UNPARSEABLE_DATE
    assert exc_info.value.row == 2
    assert exc_info.value.field == "posted_at"


def test_unparseable_amount_error():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-01,$2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-02,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.UNPARSEABLE_AMOUNT
    assert exc_info.value.row == 2
    assert exc_info.value.field == "amount"


def test_dates_out_of_order_error_with_row_order_asc():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-04,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-02,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.DATES_OUT_OF_ORDER
    assert exc_info.value.row == 3
    assert exc_info.value.field == "posted_at"


def test_dates_out_of_order_error_with_row_order_desc():
    mapping = get_valid_mapping().model_copy(update={"row_order": "desc"})
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-04,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-06,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    with pytest.raises(CsvFileParseException) as exc_info:
        csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)

    assert exc_info.value.error_code == ErrorCode.DATES_OUT_OF_ORDER
    assert exc_info.value.row == 3
    assert exc_info.value.field == "posted_at"


def test_blank_rows_skipped_but_counted():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-01,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "",
        "2026-09-02,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
        "",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows

    assert len(parsed_rows) == 2
    assert parsed_rows[0].row == 2
    assert parsed_rows[1].row == 4


def test_delimiter_only_row_is_blank():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-01,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        ",,,,,",
        "2026-09-02,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows

    assert len(parsed_rows) == 2
    assert parsed_rows[0].row == 2
    assert parsed_rows[1].row == 4


def test_quoted_newline_is_one_row():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-01,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        '2026-09-01,-16.99,"Netflix \n Subscription",11983.01,Debit,Posted',
        "2026-09-02,-14.00,Café Grumpy,11969.01,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows

    assert len(parsed_rows) == 3
    assert parsed_rows[0].row == 2
    assert parsed_rows[1].row == 3
    assert parsed_rows[2].row == 4
    assert "\n" in parsed_rows[1].description


def test_file_row_asc():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-05,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-18,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
        "2026-09-22,-16.99,Netflix Subscription,11969.01,Debit,Posted",
    ]
    file_bytes = make_csv_file(lines)
    dates = [date(2026, 9, 5), date(2026, 9, 18), date(2026, 9, 22)]

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows
    parsed_dates = [row.posted_at for row in parsed_rows]

    assert len(parsed_rows) == 3
    assert dates == parsed_dates
    assert [parsed_row.row for parsed_row in parsed_rows] == [2, 3, 4]


def test_file_row_desc():
    mapping = get_valid_mapping().model_copy(update={"row_order": "desc"})
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-22,-16.99,Netflix Subscription,11969.01,Debit,Posted",
        "2026-09-18,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
        "2026-09-05,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
    ]
    file_bytes = make_csv_file(lines)
    dates = [date(2026, 9, 5), date(2026, 9, 18), date(2026, 9, 22)]

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows
    parsed_dates = [row.posted_at for row in parsed_rows]

    assert len(parsed_rows) == 3
    assert dates == parsed_dates
    assert [parsed_row.row for parsed_row in parsed_rows] == [4, 3, 2]


def test_file_same_day_rows_keep_their_order():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-18,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-18,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows

    assert len(parsed_rows) == 2
    assert [parsed_row.row for parsed_row in parsed_rows] == [2, 3]
    assert parsed_rows[0].posted_at == parsed_rows[1].posted_at == date(2026, 9, 18)


def test_empty_description_flag():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-18,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-18,-14.00,,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows

    assert len(parsed_rows) == 2
    assert parsed_rows[0].flags == ()
    assert parsed_rows[1].description == ""
    assert parsed_rows[1].flags == ("empty_description",)


def test_empty_raw_type_flag():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-18,2500.00,Payroll,12000.00,,Posted",
        "2026-09-18,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
        "2026-09-22,-14.00,Café Grumpy,11986.00",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows

    assert len(parsed_rows) == 3
    assert parsed_rows[1].flags == ()
    assert parsed_rows[0].flags == ("empty_raw_type",)
    assert parsed_rows[0].raw_type is None
    assert parsed_rows[2].flags == ("empty_raw_type",)
    assert parsed_rows[2].raw_type is None


def test_row_with_both_flags():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-18,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-18,-14.00,,11986.00,,Posted",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows

    assert len(parsed_rows) == 2
    assert parsed_rows[0].flags == ()
    assert len(parsed_rows[1].flags) == 2
    assert parsed_rows[1].flags == ("empty_description", "empty_raw_type")
    assert parsed_rows[1].description == ""
    assert parsed_rows[1].raw_type is None


def test_parse_file_strips_header_row_whitespace():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "  Date ,Amount,Description,Current balance,Type,Status",
        "2026-09-18,2500.00,Payroll,12000.00,ACH_CREDIT,Posted",
        "2026-09-22,-14.00,Café Grumpy,11986.00,ACH_DEBIT,Posted",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows
    expected_dates = [date(2026, 9, 18), date(2026, 9, 22)]

    assert len(parsed_rows) == 2
    assert [row.posted_at for row in parsed_rows] == expected_dates


def test_parse_file_strips_field_whitespace():
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    lines = [
        "Date,Amount,Description,Current balance,Type,Status",
        "2026-09-01 , 2500.00 , Payroll , 12000.00 , ACH_CREDIT",
    ]
    file_bytes = make_csv_file(lines)

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    parsed_rows = parsed_file.rows
    expected_rows = (
        ParsedRow(
            posted_at=date(2026, 9, 1),
            amount=250000,
            description="Payroll",
            running_balance=1200000,
            raw_type="ACH_CREDIT",
            row=2,
            flags=(),
        ),
    )

    assert expected_rows == parsed_rows


def test_file_hashes_correctly():
    file_bytes = get_csv_file_bytes("checking_basic.csv")
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    assert file_hash == parsed_file.file_hash

    changed_file_bytes = file_bytes + b"\n"
    changed_parsed_file = csv_adapter.parse(
        file_bytes=changed_file_bytes, mapping=mapping
    )

    assert file_hash != changed_parsed_file.file_hash
    assert parsed_file.rows == changed_parsed_file.rows


def test_file_hash_with_bom():
    file_bytes = get_csv_file_bytes("checking_basic.csv")
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    parsed_file = csv_adapter.parse(file_bytes=file_bytes, mapping=mapping)
    assert file_hash == parsed_file.file_hash

    bom_file_bytes = b"\xef\xbb\xbf" + file_bytes
    bom_parsed_file = csv_adapter.parse(file_bytes=bom_file_bytes, mapping=mapping)

    assert file_hash != bom_parsed_file.file_hash
    assert parsed_file.rows == bom_parsed_file.rows


def test_bom_before_mapped_first_header_parses(expected_rows):
    file_bytes = get_csv_file_bytes("checking_basic.csv")
    mapping = get_valid_mapping()
    csv_adapter = CsvAdapter()

    bom_file_bytes = b"\xef\xbb\xbf" + file_bytes
    bom_parsed_file = csv_adapter.parse(file_bytes=bom_file_bytes, mapping=mapping)

    assert expected_rows == bom_parsed_file.rows
