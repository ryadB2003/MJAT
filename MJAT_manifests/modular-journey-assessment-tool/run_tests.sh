#!/bin/bash
# Run tests with correct Python path

export PYTHONPATH="$(pwd)"
python tests/test_engagement.py
