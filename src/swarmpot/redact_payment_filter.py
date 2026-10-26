import logging
import re

PAYMENT_PARAM = re.compile(r"([?&]payment=)[^&\s]*")


class RedactPaymentFilter(logging.Filter):
    """Hides the `payment` query parameter in uvicorn access logs: until it settles it is spendable."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(
                PAYMENT_PARAM.sub(r"\1[redacted]", arg) if isinstance(arg, str) else arg for arg in record.args
            )
        return True
