# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Test configuration for pytest
"""

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
sys.path.insert(0, src_path)