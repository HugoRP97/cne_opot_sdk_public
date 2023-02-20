import os
from configparser import BasicInterpolation

#  We must consider that here the values from the .ini file have .ini values are predominant over environment variables
class EnvInterpolation(BasicInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)