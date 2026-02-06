#!/usr/bin/env python3
"""
Dump the Pygramattic Reports JSON schema to stdout.
This allows AI agents to quickly inspect the data model without importing everything.
"""
import json
import sys
from pathlib import Path

# Add src to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from pygramattic_reports.config.settings import AppConfig
except ImportError as e:
    print(f"Error importing models: {e}", file=sys.stderr)
    sys.exit(1)

def main():
    try:
        # AppConfig is the root configuration containing Storage, Database, etc.
        schema = AppConfig.model_json_schema()
        print(json.dumps(schema, indent=2))
    except Exception as e:
        print(f"Error generating schema: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
