"""
Module to create singletons in case they are needed
"""


class Singleton(type):
    """ This is a Singleton metaclass. All classes affected by this metaclass
    have the property that only one instance is created for each set of arguments
    passed to the class constructor."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
