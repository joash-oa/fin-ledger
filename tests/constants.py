from datetime import UTC, datetime, timedelta
from uuid import UUID

TEST_USER_ID = UUID("93acb7e4-5d9f-404c-98b5-d0a626eacf09")
TEST_SESSION_TOKEN = "test_session_token"
TEST_EMAIL_ADDRESS = "test_email@email.com"
TEST_PASSWORD = "TEST_password-123"
TEST_FIRST_NAME = "test_first"
TEST_LAST_NAME = "test_last"
TEST_MAX_COOKIE_AGE = 3600
TEST_SESSION_ID = UUID("89cbd911-fff3-407e-ab3f-6b2eed2fbe1a")
TEST_NOW = datetime(2026, 9, 22, 12, tzinfo=UTC)
TEST_CREATED_AT = TEST_NOW - timedelta(hours=2)
TEST_LAST_ACTIVITY_AT = TEST_NOW - timedelta(minutes=2)

TEST_ACCOUNT_ID = UUID("fc913108-be71-42b3-8315-d9204d654700")
TEST_ACCOUNT_NAME = "test_account"
TEST_ACCOUNT_INSTITUTION = "test_institution"
TEST_ACCOUNT_TYPE = "checking"
TEST_MASKED_NUMBER = "1234"
# TEST_ACCOUNT_BALANCE = 2000

TEST_POSTED_AT = "test_posted_at"
TEST_AMOUNT = "test_amount"
TEST_DESCRIPTION = "test_description"
TEST_RUNNING_BALANCE = "test_running_balance"
TEST_RAW_TYPE = "test_raw_type"
TEST_DATE_FORMAT = "test_date_format"
TEST_ROW_ORDER = "asc"
