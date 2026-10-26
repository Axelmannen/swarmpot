import logging

from swarmpot.redact_payment_filter import RedactPaymentFilter


def test_payment_query_parameter_is_redacted() -> None:
    record = logging.LogRecord(
        "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d', ("127.0.0.1", "GET", "/api/proxy?url=x&payment=c2VjcmV0&method=GET", "1.1", 200), None
    )

    RedactPaymentFilter().filter(record)

    assert record.getMessage() == '127.0.0.1 - "GET /api/proxy?url=x&payment=[redacted]&method=GET HTTP/1.1" 200'
