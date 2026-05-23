#!/usr/bin/env python3
"""
🧠 Nexo 2.0 — Entry point
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.nexo_engine import main

if __name__ == "__main__":
    main()
