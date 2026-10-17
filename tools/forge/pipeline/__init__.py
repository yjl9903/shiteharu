"""Shared subtitle production modules; invoke through Forge with explicit config."""
from pathlib import Path
import sys

# Shared tool code is located from this file, including in unpacked deliveries.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
