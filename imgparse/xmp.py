"""Extract XMP data from images."""

import re


class CombinablePattern(re.Pattern):
    """Not sure what this will do yet."""

    def __init__(self):
        """Not sure what this will take yet."""
        pass

    def combined_with(self, other):
        """
        Not sure what this will do yet.

        :param other:
        :return:
        """
        pass


def compile_combinable(regex: str) -> CombinablePattern:
    """
    Not sure what this will do yet.

    :param regex:
    :return:
    """
    pattern = re.compile(regex)
    return CombinablePattern(pattern)
