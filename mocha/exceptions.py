# -*- coding: utf-8 -*-
"""
exceptions.py

Raise Mocha specific exceptions
"""

class MochaError(Exception):
    """
    This exception is not reserved, but it used for all Mocha exception.
    It helps catch Core problems.
    """
    pass


class AppError(MochaError):
    """
    Use this exception in your application level.
    """
    pass


class ModelError(MochaError):
    """
    Use this exception in your model level.
    """
    pass




