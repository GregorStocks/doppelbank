# Claude Coding Standards

## Import Rules

1. **Always use absolute imports** - Use `from doppelbank.bedrock.models import ...` instead of relative imports like `from .models import ...`

2. **All imports at the top** - Never scatter imports throughout the file. Group them logically at the top:
   - Standard library imports first
   - Third-party imports second  
   - Local project imports last
   - Each group separated by a blank line

## Example

```python
# Standard library
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Third-party
from google.protobuf import text_format
from google.protobuf.json_format import MessageToJson

# Local project
from doppelbank.bedrock.models import create_paycheck_event, save_events
from doppelbank.bedrock.generated import events_pb2
```

## Why These Rules?

- **Absolute imports** are more explicit and work better with IDEs and linters
- **Top-level imports** make code more readable and avoid import-time side effects
- **Consistent structure** makes the codebase easier to navigate and maintain

## Notes

- **Protobuf linter issues**: The linter may show errors for protobuf-generated classes (like `events_pb2.Event`), but the code works correctly at runtime. This is a known limitation with protobuf-generated code and type checkers. 