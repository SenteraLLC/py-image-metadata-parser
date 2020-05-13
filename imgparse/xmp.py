import re
import typing


class CombinablePattern(re.Pattern):

    def __init__(self):
        pass

    def combined_with(self, other):
        pass


def compile_combinable(regex):
    pattern = re.compile(regex)
    return CombinablePattern(pattern)
