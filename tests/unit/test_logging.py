"""Unit tests for structured logging and contextvars correlation."""

import json
import logging
import unittest
import uuid
from industrial_oracle.core.logging import (
    StructuredJSONFormatter,
    request_id_ctx,
    org_id_ctx,
    actor_id_ctx,
)


class TestStructuredLogging(unittest.TestCase):
    def setUp(self):
        self.formatter = StructuredJSONFormatter()

    def test_formatter_with_context(self):
        req_id = str(uuid.uuid4())
        org_id = str(uuid.uuid4())
        actor_id = str(uuid.uuid4())

        t1 = request_id_ctx.set(req_id)
        t2 = org_id_ctx.set(org_id)
        t3 = actor_id_ctx.set(actor_id)

        try:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="test_file.py",
                lineno=42,
                msg="Operation executed successfully.",
                args=(),
                exc_info=None,
            )
            output = self.formatter.format(record)
            data = json.loads(output)

            self.assertEqual(data["level"], "INFO")
            self.assertEqual(data["logger"], "test_logger")
            self.assertEqual(data["message"], "Operation executed successfully.")
            self.assertEqual(data["request_id"], req_id)
            self.assertEqual(data["organization_id"], org_id)
            self.assertEqual(data["actor_id"], actor_id)
            self.assertIn("timestamp", data)
        finally:
            request_id_ctx.reset(t1)
            org_id_ctx.reset(t2)
            actor_id_ctx.reset(t3)


if __name__ == "__main__":
    unittest.main()
