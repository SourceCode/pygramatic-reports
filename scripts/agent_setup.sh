#!/bin/bash
set -e

echo "🤖 Agent Setup Protocol Initiated..."

# 1. Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    exit 1
fi

# 2. Check for Virtual Environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate Virtual Environment
source .venv/bin/activate

# 4. Install Dependencies
echo "⬇️ Installing dependencies..."
./.venv/bin/pip install -e ".[dev,test]"

# 5. Verify Installation
echo "✅ Verifying installation..."
./.venv/bin/python3 -c "import pygramattic_reports; print(f'Pygramattic Reports {pygramattic_reports.__version__} ready.')"

echo "🎉 Agent Setup Complete. Environment is ready."
