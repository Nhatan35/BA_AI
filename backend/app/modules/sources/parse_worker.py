"""Private parser protocol; stderr and document/library exceptions never reach API/logs."""

import base64
import json
import sys

from app.modules.sources.parsers import Limits, ParseFailure, StructuredParser


def main():
    try:
        payload = json.load(sys.stdin)
        parsed = StructuredParser(payload["extension"]).parse(
            base64.b64decode(payload["content"]), Limits(**payload["limits"])
        )
        result = {"status": "PARSED", **parsed}
    except ParseFailure as error:
        result = {"status": error.status, "error": error.code}
    except Exception:
        result = {"status": "FAILED", "error": "CORRUPT_OR_UNREADABLE"}
    sys.stdout.write(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
