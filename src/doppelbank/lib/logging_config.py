"""
Centralized logging configuration for the doppelbank application.

This module provides a consistent logging setup that can be used across
all entry points (bedrock, detritus, veneer) and other modules.
"""

import logging
import os
from typing import Optional


def configure_logging(level: Optional[str] = None, module_name: Optional[str] = None) -> None:
    """
    Configure logging for the doppelbank application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). 
               If None, reads from LOG_LEVEL environment variable or defaults to INFO.
        module_name: Optional module name to include in log format for better identification.
    """
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level, logging.INFO)
    
    # Create format string with optional module name
    if module_name:
        format_str = f"%(asctime)s - {module_name} - %(name)s - %(levelname)s - %(message)s"
    else:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure basic logging
    logging.basicConfig(
        level=numeric_level,
        format=format_str,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True  # Override any existing configuration
    )