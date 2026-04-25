"""
Lightweight Logging Mixin
=========================

Simple logging mixin for vellum classes.

Standard-library-only implementation that requires no external dependencies.
"""

import logging


class LoggingMixin:
    """Lightweight logging mixin for vellum classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(f"vellum.{self.__class__.__name__}")
