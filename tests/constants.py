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
