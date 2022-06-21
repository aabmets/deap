# ====================================================================================== #
#                                                                                        #
#   MIT License                                                                          #
#                                                                                        #
#   Copyright (c) 2022 - Mattias Aabmets, The DEAP Team and Other Contributors           #
#                                                                                        #
#   Permission is hereby granted, free of charge, to any person obtaining a copy         #
#   of this software and associated documentation files (the "Software"), to deal        #
#   in the Software without restriction, including without limitation the rights         #
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell            #
#   copies of the Software, and to permit persons to whom the Software is                #
#   furnished to do so, subject to the following conditions:                             #
#                                                                                        #
#   The above copyright notice and this permission notice shall be included in all       #
#   copies or substantial portions of the Software.                                      #
#                                                                                        #
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR           #
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,             #
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE          #
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER               #
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,        #
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE        #
#   SOFTWARE.                                                                            #
#                                                                                        #
# ====================================================================================== #
from deap_er.utils.deprecated import deprecated
from collections import defaultdict, deque
import copy
import abc
import re


__all__ = ['Terminal', 'Ephemeral', 'Primitive', 'PrimitiveTree',
           'PrimitiveSet', 'PrimitiveSetTyped']


# ====================================================================================== #
class Terminal(object):
    """
    Class that encapsulates terminal primitive in expression.
    Terminals can be values or 0-arity functions.
    """
    __slots__ = ('name', 'value', 'ret', 'conv_fct')

    # -------------------------------------------------------------------------------------- #
    def __init__(self, terminal, symbolic, ret):
        self.ret = ret
        self.value = terminal
        self.name = str(terminal)
        self.conv_fct = str if symbolic else repr

    # -------------------------------------------------------------------------------------- #
    @property
    def arity(self):
        return 0

    # -------------------------------------------------------------------------------------- #
    def format(self):
        return self.conv_fct(self.value)

    # -------------------------------------------------------------------------------------- #
    def __eq__(self, other):
        if type(self) is type(other):
            return all(getattr(self, slot) == getattr(other, slot)
                       for slot in self.__slots__)
        else:
            return NotImplemented


# ====================================================================================== #
class Ephemeral(Terminal):
    """
    Class that encapsulates a terminal which value is set
    when the object is created. This is an abstract base class.
    When subclassing, a staticmethod 'func' must be defined.
    To mutate the value, a new object has to be generated.
    """
    def __init__(self):
        Terminal.__init__(self, self.func(), symbolic=False, ret=self.ret)

    @staticmethod
    @abc.abstractmethod
    def func():
        raise NotImplementedError


# ====================================================================================== #
class Primitive:
    """
    Class that encapsulates a primitive and when called with arguments it
    returns the Python code to call the primitive with the arguments.
    """

    __slots__ = ('name', 'arity', 'args', 'ret', 'seq')

    # -------------------------------------------------------------------------------------- #
    def __init__(self, name, args, ret):
        self.name = name
        self.arity = len(args)
        self.args = args
        self.ret = ret
        args = ", ".join(map("{{{0}}}".format, list(range(self.arity))))
        self.seq = "{name}({args})".format(name=self.name, args=args)

    # -------------------------------------------------------------------------------------- #
    def format(self, *args):
        return self.seq.format(*args)

    # -------------------------------------------------------------------------------------- #
    def __eq__(self, other):
        if type(self) is type(other):
            return all(getattr(self, slot) == getattr(other, slot)
                       for slot in self.__slots__)
        else:
            return NotImplemented


# ====================================================================================== #
class PrimitiveSetTyped:
    """
    Class that contains the primitives which can be
    used to solve a Strongly Typed GP problem.
    """
    def __init__(self, name, in_types, ret_type, prefix="ARG"):
        self.name = name
        self.ins = in_types
        self.ret = ret_type

        self.terminals = defaultdict(list)
        self.primitives = defaultdict(list)
        self.context = {"__builtins__": None}
        self.arguments = list()
        self.mapping = dict()
        self.terms_count = 0
        self.prims_count = 0

        for i, type_ in enumerate(in_types):
            arg_str = "{prefix}{index}".format(prefix=prefix, index=i)
            self.arguments.append(arg_str)
            term = Terminal(arg_str, True, type_)
            self._add(term)
            self.terms_count += 1

    # -------------------------------------------------------------------------------------- #
    def rename_arguments(self, **kwargs):
        for i, old_name in enumerate(self.arguments):
            if old_name in kwargs:
                new_name = kwargs[old_name]
                self.arguments[i] = new_name
                self.mapping[new_name] = self.mapping[old_name]
                self.mapping[new_name].value = new_name
                del self.mapping[old_name]

    # -------------------------------------------------------------------------------------- #
    def _add(self, prim):
        def add_type(_dict, ret_type):
            if ret_type not in _dict:
                new_list = []
                for _type, list_ in list(_dict.items()):
                    if issubclass(_type, ret_type):
                        for item in list_:
                            if item not in new_list:
                                new_list.append(item)
                _dict[ret_type] = new_list

        add_type(self.primitives, prim.ret)
        add_type(self.terminals, prim.ret)

        self.mapping[prim.name] = prim
        if isinstance(prim, Primitive):
            for type_ in prim.args:
                add_type(self.primitives, type_)
                add_type(self.terminals, type_)
            dict_ = self.primitives
        else:
            dict_ = self.terminals

        for type_ in dict_:
            if issubclass(prim.ret, type_):
                dict_[type_].append(prim)

    # -------------------------------------------------------------------------------------- #
    def add_primitive(self, primitive, in_types, ret_type, name=None) -> None:
        cond_1 = name not in self.context
        cond_2 = self.context[name] is primitive

        if cond_1 or cond_2:
            raise ValueError(
                f'Primitives are required to have a unique name. '
                f'Consider using the argument \'name\' to rename your '
                f'second \'{name}\' primitive.'
            )

        if name is None:
            name = primitive.__name__
        prim = Primitive(name, in_types, ret_type)

        self._add(prim)
        self.context[prim.name] = primitive
        self.prims_count += 1

    # -------------------------------------------------------------------------------------- #
    def add_terminal(self, terminal, ret_type, name=None):
        if name not in self.context:
            raise ValueError(
                f'Terminals are required to have a unique name. '
                f'Consider using the argument \'{name}\' to rename your '
                f'second \'{name}\' terminal.'
            )

        symbolic = False
        if name is None and callable(terminal):
            name = terminal.__name__

        if name is not None:
            self.context[name] = terminal
            terminal = name
            symbolic = True
        elif terminal in (True, False):
            self.context[str(terminal)] = terminal

        prim = Terminal(terminal, symbolic, ret_type)
        self._add(prim)
        self.terms_count += 1

    # -------------------------------------------------------------------------------------- #
    def add_ephemeral_constant(self, name, ephemeral, ret_type):
        err_msg_1 = 'Ephemera with different functions should be named differently even between psets.'
        err_msg_2 = 'Ephemera with the same name and function should have the same type even between psets.'
        err_msg_3 = 'Ephemera should be named differently than classes defined in the gp module.'

        module_gp = globals()
        if name not in module_gp:
            attrs = {'func': staticmethod(ephemeral), 'ret': ret_type}
            class_ = type(name, (Ephemeral,), attrs)
            module_gp[name] = class_
        else:
            class_ = module_gp[name]
            if issubclass(class_, Ephemeral):
                if class_.func is not ephemeral:
                    raise TypeError(err_msg_1)
                elif class_.ret is not ret_type:
                    raise TypeError(err_msg_2)
            else:
                raise TypeError(err_msg_3)

        self._add(class_)
        self.terms_count += 1

    # -------------------------------------------------------------------------------------- #
    def add_adf(self, adf_set) -> None:
        prim = Primitive(
            adf_set.name,
            adf_set.ins,
            adf_set.ret
        )
        self._add(prim)
        self.prims_count += 1

    # -------------------------------------------------------------------------------------- #
    @property
    def terminal_ratio(self):
        return self.terms_count / float(self.terms_count + self.prims_count)

    # -------------------------------------------------------------------------------------- #
    addEphemeralConstant = deprecated('addEphemeralConstant', add_ephemeral_constant)
    renameArguments = deprecated('renameArguments', rename_arguments)
    terminalRatio = deprecated('terminalRatio', terminal_ratio)
    addPrimitive = deprecated('addPrimitive', add_primitive)
    addTerminal = deprecated('addTerminal', add_terminal)
    addADF = deprecated('addADF', add_adf)


# ====================================================================================== #
class PrimitiveSet(PrimitiveSetTyped):
    """
    Subclass of *PrimitiveSetTyped* without the type definition.
    """

    def __init__(self, name, arity, prefix="ARG"):
        args = [object] * arity
        super().__init__(name, args, object, prefix)

    # -------------------------------------------------------------------------------------- #
    def add_primitive(self, primitive, arity: int, name=None, *_):
        if not arity >= 1:
            raise ValueError('arity should be >= 1')
        args = [object] * arity
        super().add_primitive(primitive, args, object, name)

    # -------------------------------------------------------------------------------------- #
    def add_terminal(self, terminal, name=None, *_):
        super().add_terminal(terminal, object, name)

    # -------------------------------------------------------------------------------------- #
    def add_ephemeral_constant(self, name, ephemeral, *_):
        super().add_ephemeral_constant(name, ephemeral, object)

    # -------------------------------------------------------------------------------------- #
    addEphemeralConstant = deprecated('addEphemeralConstant', add_ephemeral_constant)
    addPrimitive = deprecated('addPrimitive', add_primitive)
    addTerminal = deprecated('addTerminal', add_terminal)


# ====================================================================================== #
class PrimitiveTree(list):
    """
    Tree specifically formatted for optimization of genetic programming operations.
    This class is a subclass of list, where the nodes are appended, or are assumed
    to have been appended, when creating an object of this class with a list of
    primitives and terminals. The nodes appended to the tree are required to have
    the *arity* attribute, which defines the arity of the primitive.
    """

    def __init__(self, content):
        list.__init__(self, content)

    # -------------------------------------------------------------------------------------- #
    def __deepcopy__(self, memo):
        new = self.__class__(self)
        new.__dict__.update(copy.deepcopy(self.__dict__, memo))
        return new

    # -------------------------------------------------------------------------------------- #
    def __setitem__(self, key, val):
        err_msg_1 = f'Invalid slice object: trying to assign a \'{key}\' in a tree of size {len(self)}.'
        err_msg_2 = f'Invalid slice assignment: insertion of an incomplete subtree is not allowed.'
        err_msg_3 = f'Invalid node replacement with a node of a different arity.'

        if isinstance(key, slice):
            if key.start >= len(self):
                raise IndexError(err_msg_1)
            total = val[0].arity
            for node in val[1:]:
                total += node.arity - 1
            if total != 0:
                raise ValueError(err_msg_2)
        elif val.arity != self[key].arity:
            raise ValueError(err_msg_3)
        list.__setitem__(self, key, val)

    # -------------------------------------------------------------------------------------- #
    def __str__(self):
        string = str()
        stack = list()
        for node in self:
            stack.append((node, []))
            while len(stack[-1][1]) == stack[-1][0].arity:
                prim, args = stack.pop()
                string = prim.format(*args)
                if len(stack) == 0:
                    break
                stack[-1][1].append(string)
        return string

    # -------------------------------------------------------------------------------------- #
    @classmethod
    def from_string(cls, string, pset):
        tokens = re.split("[ \t\n\r\f\v(),]", string)
        expr = list()
        ret_types = deque()
        for token in tokens:
            if token == '':
                continue
            if len(ret_types) != 0:
                type_ = ret_types.popleft()
            else:
                type_ = None

            if token in pset.mapping:
                primitive = pset.mapping[token]
                if type_ is not None and not issubclass(primitive.ret, type_):
                    raise TypeError(
                        f'Primitive {primitive} return type {primitive.ret} '
                        f'does not match the expected one: {type_}.'
                    )
                expr.append(primitive)
                if isinstance(primitive, Primitive):
                    ret_types.extendleft(reversed(primitive.args))
            else:
                try:
                    token = eval(token)
                except NameError:
                    raise TypeError(f'Unable to evaluate terminal: {token}.')
                if type_ is None:
                    type_ = type(token)
                if not issubclass(type(token), type_):
                    raise TypeError(
                        f'Terminal {token} type {type(token)} does '
                        f'not match the expected one: {type_}.'
                    )
                expr.append(Terminal(token, False, type_))
        return cls(expr)

    # -------------------------------------------------------------------------------------- #
    @property
    def height(self):
        stack = [0]
        max_depth = 0
        for elem in self:
            depth = stack.pop()
            max_depth = max(max_depth, depth)
            stack.extend([depth + 1] * elem.arity)
        return max_depth

    # -------------------------------------------------------------------------------------- #
    @property
    def root(self):
        return self[0]

    # -------------------------------------------------------------------------------------- #
    def search_subtree(self, begin):
        end = begin + 1
        total = self[begin].arity
        while total > 0:
            total += self[end].arity - 1
            end += 1
        return slice(begin, end)

    # -------------------------------------------------------------------------------------- #
    searchSubtree = deprecated('searchSubtree', search_subtree)
