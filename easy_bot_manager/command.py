from lib2to3.pytree import Base
from mcdreforged.api.command import *

from typing import List, Type

class MultipleArgument(ArgumentNode):
    def __init__(self, name: str, n_elements: int, type_restrictions: List[Type] = None) -> None:
        super().__init__(name)
        self.__name = name
        self.n_elements = n_elements
        if type_restrictions is None:
            self.type_restrictions = [str for _ in range(n_elements)]
        else:
            assert len(type_restrictions) == n_elements
            self.type_restrictions = type_restrictions

    def parse(self, text: str):
        ret = []
        char_read = 0
        for _ in range(self.n_elements):
            if text[char_read: char_read+1] == ' ':
                char_read += 1
            s = command_builder_util.get_element(text[char_read:])
            if s == '':
                raise CommandSyntaxError(
                    'Incomplete Arguments (Expect {} but got {})'.format(
                        self.n_elements, _
                    ),
                    char_read
                )
            char_read += len(s)
            try:
                cvt = self.type_restrictions[_](s)
            except BaseException:
                raise CommandSyntaxError(
                    'Invalid Argument {} in {} (Expect {} but got {})'.format(
                        s, self.__name, self.type_restrictions[_], type(s)
                    ),
                    char_read
                )
            ret.append(cvt)
        return ParseResult(ret, char_read)

