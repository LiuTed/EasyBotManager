from mcdreforged.api.command import *

from typing import List, Tuple, Type, Dict, Iterable

class MultipleArguments(ArgumentNode):
    def __init__(self, name: str, n_elements: int, type_restrictions: List[Type] = None) -> None:
        super().__init__(name)
        self.n_elements = n_elements
        if type_restrictions is None:
            self.type_restrictions = [str for _ in range(n_elements)]
        elif isinstance(type_restrictions, (list, tuple)):
            assert len(type_restrictions) == n_elements
            self.type_restrictions = type_restrictions
        else:
            self.type_restrictions = [type_restrictions for _ in range(n_elements)]

    def parse(self, text: str):
        ret = []
        char_read = 0
        for _ in range(self.n_elements):
            rest = command_builder_util.remove_divider_prefix(text[char_read:])
            char_read = len(text) - len(rest)
            if len(rest) == 0:
                raise CommandSyntaxError(
                    'Incomplete Arguments (Expect {} but got {})'.format(
                        self.n_elements, _
                    ),
                    char_read
                )
            s = command_builder_util.get_element(rest)
            char_read += len(s)
            try:
                cvt = self.type_restrictions[_](s)
            except ValueError:
                raise CommandSyntaxError(
                    'Invalid Argument {} in {} (Expect {} but got {})'.format(
                        s, self.get_name(), self.type_restrictions[_], type(s)
                    ),
                    char_read
                )
            ret.append(cvt)
        return ParseResult(ret, char_read)

class DumbNode(ArgumentNode):
    def __init__(self, name: str = '__dumb', return_context = None):
        super().__init__(name)
        self._suggestion_getter = None
        self.return_context = return_context
    
    def parse(self, text: str):
        return ParseResult(self.return_context, 0)
    
    def _get_suggestions(self, context: CommandContext) -> Iterable[str]:
        if self._suggestion_getter is not None:
            return super()._get_suggestions(context)
        else:
            ret = list(self._children_literal.keys())
            for child in self._children:
                with context.enter_child(child):
                    ret.extend(child._get_suggestions(context))
            return ret

class NLRA(ArgumentNode): # Named Literal and Retryable Argument
    def __init__(
        self,
        name: str,
        literal: str or Iterable[str],
        argument: 'ArgumentNode' or Iterable['ArgumentNode']
    ):
        super().__init__(name)
        if isinstance(literal, str):
            self._literals = {literal}
        elif isinstance(literal, Iterable):
            self._literals = set(literal)
        else:
            raise TypeError('NLRA: literal: Only str or Iterable[str] is accepted')
        for lit in self._literals:
            if not isinstance(lit, str):
                raise TypeError('NLRA: literal: Only str or Iterable[str] is accepted but got {}'.format(type(lit)))
        
        if isinstance(argument, ArgumentNode):
            self._arguments = {argument}
        elif isinstance(argument, Iterable):
            self._arguments = list(argument)
        else:
            raise TypeError('NLRA: argument: Only ArgumentNode or Iterable[ArgumentNode] is accepted')
        for arg in self._arguments:
            if not isinstance(arg, ArgumentNode):
                raise TypeError('NLRA: argument: Only ArgumentNode or Iterable[ArgumentNode] is accepted but got {}'.format(type(arg)))

        self._suggestion_getter = None

    def parse(self, text: str):
        s = command_builder_util.get_element(text)
        if s in self._literals:
            return ParseResult(s, len(s))

        char_read = 0
        first_error = None
        ret = None
        for arg in self._arguments:
            try:
                aret = arg.parse(text)
            except CommandSyntaxError as err:
                if first_error is None:
                    first_error = err
            except:
                raise
            else:
                ret = aret.value
                char_read = aret.char_read
                break
        else:
            raise CommandSyntaxError('Invalid Argument in {} (what: {})'.format(self.get_name(), first_error.message), char_read) from first_error
        return ParseResult(ret, char_read)
    
    def _get_suggestions(self, context: CommandContext) -> Iterable[str]:
        if self._suggestion_getter is not None:
            return super()._get_suggestions(context)
        else:
            ret = list(self._literals)
            for arg in self._arguments:
                with context.enter_child(arg):
                    ret.extend(arg._get_suggestions(context))
            return ret

class NamedArguments(ArgumentNode):
    def __init__(self, name: str, groups: Dict[str, ArgumentNode], allow_duplicate: str = 'raise'):
        super().__init__(name)
        if allow_duplicate not in ['disallow', 'ignore', 'overwrite', 'stop']:
            raise TypeError(
                '''Argument allow_duplicate for NamedArguments must be one of
                'disallow', 'ignore', 'overwrite', 'stop', but got {}
                '''.format(allow_duplicate)
            )
        self.parse_dict = groups
        self.allow_duplicate = allow_duplicate
        self.suggests(lambda: [s for s in self.parse_dict.keys()])
    
    def parse(self, text: str):
        ret = {}
        char_read = 0
        tlen = len(text)
        while char_read < tlen:
            rest = command_builder_util.remove_divider_prefix(text[char_read:])
            char_read = tlen - len(rest)
            if len(rest) == 0:
                break

            s = command_builder_util.get_element(rest)
            if s not in self.parse_dict:
                break
            if s in ret:
                if self.allow_duplicate == 'disallow':
                    raise CommandSyntaxError(
                        'Duplicated Argument {} in {}'.format(
                            s, self.get_name()
                        ),
                        char_read + len(s)
                    )
                elif self.allow_duplicate == 'stop':
                    break

            char_read += len(s)
            rest = command_builder_util.remove_divider_prefix(text[char_read:])
            char_read = tlen - len(rest)
            if char_read >= tlen:
                raise CommandSyntaxError(
                    'Incomplete Argument {} in {}'.format(s, self.get_name()),
                    tlen
                )

            try:
                child = self.parse_dict[s].parse(rest)
            except CommandSyntaxError as err:
                raise CommandSyntaxError(
                    'Error When Parsing Argument {} in {} (got {})'.format(
                        s, self.get_name(), rest
                    ),
                    char_read + err.char_read
                ) from err
            else:
                char_read += child.char_read
                if s in ret:
                    if self.allow_duplicate == 'overwrite':
                        ret[s] = child.value

        if ret == {}:
            raise CommandSyntaxError(
                'No Matching Argument in {}'.format(self.get_name()),
                char_read
            )
        else:
            return ParseResult(ret, char_read)





