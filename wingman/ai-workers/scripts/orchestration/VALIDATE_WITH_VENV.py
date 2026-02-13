#!/usr/bin/env python3
"""
Run validation using the virtual environment
"""

import sys
import os

# Add venv to path
venv_path = os.path.join(os.getcwd(), 'autonomous_build', 'venv', 'lib', 'python3.13', 'site-packages')
sys.path.insert(0, venv_path)

# Now import and run the orchestrated validation
exec(open('ORCHESTRATED_VALIDATION.py').read())