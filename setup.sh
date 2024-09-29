#!/bin/bash

export PYTHONPATH=$PWD

echo "Running initialization scripts..."
python setup/check_setup.py
