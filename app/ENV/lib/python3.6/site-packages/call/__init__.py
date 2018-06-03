# Copyright 2012 Canonical Ltd.
# Written by:
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
# See COPYING for license

"""
call
====

Pure-python implementation of python call semantics for python 3.1, python 3.2
and python 3.3. This allows to check how arguments would have been applied to a
function without actually calling the function. Replicated behavior includes
exactly identical exceptions and error messages

Thus module is useful in python research with typed function call annotations
"""

from collections import namedtuple
from inspect import getfullargspec
from sys import version_info
from abc import ABCMeta, abstractmethod

__version__ = (0, 1, 0, "dev", 0)

__all__ = ["PythonCall"]

# Unique object that is used by the implementation to find "empty" values where
# None is a legal, non-empty value already.
Unfilled = object()


# Return value of PythonCall.resolve()
call_resolution = namedtuple("call_resolution",
                             "slots varargs varkw kwonlyargs")


class _PythonCall(metaclass=ABCMeta):

    def __init__(self, func):
        """
        Construct a wrapper that can call the specified function
        """
        self._func = func
        self._spec = getfullargspec(func)

    def bind(self, args, kwargs):
        """
        Bind arguments and keyword arguments to the encapsulated function.

        Returns a dictionary of parameters (named according to function
        parameters) with the values that were bound to each name.
        """
        spec = self._spec
        resolution = self.resolve(args, kwargs)
        params = dict(zip(spec.args, resolution.slots))
        if spec.varargs:
            params[spec.varargs] = resolution.varargs
        if spec.varkw:
            params[spec.varkw] = resolution.varkw
        if spec.kwonlyargs:
            params.update(resolution.kwonlyargs)
        return params

    @abstractmethod
    def resolve(self, args, kwargs):
        """
        Resolve how arguments are bound to parameters.

        This is the lower-level equivalent of bind(). Using resolve() allows
        for finer grained validation (for unit testing) and may be needed in
        some cases where the fine segregation is needed to implement a
        decorator.

        Unlike bind(), resolve() returns a named tuple:
            (slots, varargs, varkw, kwonlyargs)

        The elements of that tuple are discussed below:

            slots:
                A tuple of values for each parameter that a function accepts.
                All slots are "full", either by consuming values from args and
                kwargs or from function defaults.
            varargs:
                A tuple of leftover arguments that is normally assigned to a
                parameter with the *identifier syntax. When the function does
                not accept variable argument list this value is always None.
            varkw:
                A dictionary of leftover keyword arguments that is normally
                assigned to a parameter with the **identifier syntax. When the
                function does not accept variable keyword dictionary this value
                is always None.
            kwonlyargs:
                A dictionary of keyword-only arguments. This is unique to
                python 3. Those arguments are similar to positional arguments
                (by not being consumed by varargs or varkw) but can be _only_
                specified by name (using the name=value syntax). When the
                function does not accept keyword only arguments this value is
                always None.

        See pydoc3 CALLS for implementation details
        """

    def apply(self, args, kwargs):
        """
        Replicate a call to the encapsulated function.

        Unlike func(*args, **kwargs) the call is deterministic in the order
        kwargs are being checked by python. In other words, it behaves exactly
        the same as if typed into the repl prompt.

        This is usually only a problem when a function is given two invalid
        keyword arguments. In such cases func(*args, **kwargs) syntax will
        result in random error on either of those invalid keyword arguments.
        This is most likely caused by a temporary dictionary created by the
        runtime.

        For testing a OderedDictionary instance may be passed as kwargs.  In
        such case the call, and the error message, is fully deterministic.

        This function is implemented with eval()
        """
        # Construct helper locals that only contain the function to call as
        # 'func', all positional arguments as 'argX' and all keyword arguments
        # as 'kwX'
        _locals = {'func': self._func}
        if args is not None:
            _locals.update({
                "arg{}".format(index): args[index]
                for index, value in enumerate(args)})
        if kwargs is not None:
            # Explicitly build a list of keyword arguments so that we never
            # traverse kwargs more than once
            kw_list = list(kwargs.keys())
            _locals.update({
                "kw{}".format(index): kwargs[key]
                for index, key in enumerate(kw_list)})
        # Construct the call expression string by carefully
        # placing each positional and keyword arguments in right
        # order that _exactly_ matches how apply() was called.
        params = []
        if args is not None:
            params.extend([
                "arg{}".format(index)
                for index in range(len(args))])
        if kwargs is not None:
            params.extend([
                "{}=kw{}".format(key, index)
                for index, key in enumerate(kw_list)])
        expr = "func({})".format(", ".join(params))
        return eval(expr, globals(), _locals)

    @abstractmethod
    def _raise_args_mismatch(self, args, kwargs):
        pass


class PythonCall_py31(_PythonCall):
    """
    Wrapper that can call a function with python 3.1 calling semantics
    """

    def resolve(self, args, kwargs):
        func = self._func
        spec = self._spec
        # Check if the function accepts positional arguments
        if spec.args == []:
            slots = None
        else:
            slots = [Unfilled] * len(spec.args)
        # Check if the function accepts a variable argument list
        if spec.varargs is None:
            # Report excess positional arguments as TypeError
            if len(args) > len(spec.args):
                self._raise_args_mismatch(args, kwargs)
            varargs = None
        else:
            # Convert excess positional arguments to variable argument list
            varargs = tuple(args[len(spec.args):])
        # Check if the function accepts keyword arguments
        if spec.varkw is None:
            varkw = None
        else:
            varkw = {}
        # Check if the function accepts keyword-only arguments
        if spec.kwonlyargs == []:
            kwonlyargs = None
        else:
            kwonlyargs = {}
        # Consume positional arguments and fill in the leftmost slots
        for index in range(min(len(args), len(spec.args))):
            slots[index] = args[index]
        # Consume keyword arguments
        for kwname in list(kwargs.keys()):
            value = kwargs[kwname]
            # First attempt to resolve each keyword argument as normal function
            # argument by looking up the slot it names
            try:
                index = spec.args.index(kwname)
            except ValueError:
                # Keyword arguments that don't map to a slot are either
                # collected to keyword arguments or (UNIMPLEMENTED) passed as
                # keyword-only arguments
                if kwname in spec.kwonlyargs:
                    kwonlyargs[kwname] = value
                elif varkw is not None:
                    varkw[kwname] = value
                else:
                    if len(spec.args) == 0:
                        self._raise_args_mismatch(args, kwargs)
                    raise TypeError(
                        "%s() got an unexpected keyword argument %r" % (
                            func.__name__, kwname))
            else:
                # Keyword arguments might attempt to provide a value to slot
                # already covered by positional arguments, this is a TypeError
                if slots[index] is Unfilled:
                    slots[index] = value
                else:
                    raise TypeError(
                        "%s() got multiple values for keyword argument %r" % (
                            func.__name__, kwname))
        # Any unfilled slots are assigned with default values
        # The values are copied right-to-left here
        if spec.defaults is not None:
            for index1, value in enumerate(reversed(spec.defaults), 1):
                if slots[len(spec.args) - index1] is Unfilled:
                    slots[len(spec.args) - index1] = value
        # Any unfilled slot at this time is a TypeError
        if slots is not None and (any(slot is Unfilled for slot in slots)):
            self._raise_args_mismatch(args, kwargs)
        # Any unfilled keyword-only arguments are assigned with default values
        if spec.kwonlydefaults is not None:
            kwonlyargs.update(spec.kwonlydefaults)
        # Any missing keyword-only arguments is a TypeError
        for kwname in spec.kwonlyargs:
            if kwname not in kwonlyargs:
                raise TypeError(
                    "%s() needs keyword-only argument %s" % (
                        func.__name__, kwname))
        # All done, return the values for function application
        if slots is None:
            slots = ()
        else:
            slots = tuple(slots)
        return call_resolution(slots, varargs, varkw, kwonlyargs)

    def _raise_args_mismatch(self, args, kwargs):
        spec = self._spec
        func = self._func.__name__
        given = len(args) + len(kwargs)
        allowed = len(spec.args)
        keyword = ""
        if len(spec.args) != 0 and kwargs:
            keyword = "non-keyword "
            given -= len(kwargs)
        if len(spec.args) == 0:
            msg = "{func}() takes no arguments ({given} given)"
        elif len(args) > len(spec.args) and spec.defaults is None:
            msg = ("{func}() takes exactly {allowed} {keyword}positional"
                   " argument{s} ({given} given)")
        elif len(args) < len(spec.args) and spec.defaults is None:
            msg = ("{func}() takes exactly {allowed} {keyword}positional"
                   " argument{s} ({given} given)")
        elif len(args) > len(spec.args) and spec.defaults is not None:
            msg = ("{func}() takes at most {allowed} {keyword}positional"
                   " argument{s} ({given} given)")
        elif len(args) < len(spec.args) and spec.defaults is not None:
            allowed = len(spec.args) - len(spec.defaults)
            msg = ("{func}() takes at least {allowed} {keyword}positional"
                   " argument{s} ({given} given)")
        else:
            raise NotImplementedError(spec, args, kwargs)
        s = "s" if allowed > 1 else ""
        raise TypeError(msg.format(
            func=func, allowed=allowed, keyword=keyword, s=s, given=given))


class PythonCall_py32(PythonCall_py31):
    """
    Wrapper that can call a function with python 3.2 calling semantics
    """

    def _raise_args_mismatch(self, args, kwargs):
        spec = self._spec
        func = self._func.__name__
        given = len(args) + len(kwargs)
        allowed = len(spec.args)
        if len(spec.args) == 0:
            msg = "{func}() takes no arguments ({given} given)"
        elif len(args) > len(spec.args) and spec.defaults is None:
            msg = ("{func}() takes exactly {allowed} positional argument{s}"
                   " ({given} given)")
        elif len(args) < len(spec.args) and spec.defaults is None:
            msg = ("{func}() takes exactly {allowed} argument{s}"
                   " ({given} given)")
        elif len(args) > len(spec.args) and spec.defaults is not None:
            msg = ("{func}() takes at most {allowed} positional argument{s}"
                   " ({given} given)")
        elif len(args) < len(spec.args) and spec.defaults is not None:
            allowed = len(spec.args) - len(spec.defaults)
            msg = ("{func}() takes at least {allowed} argument{s}"
                   " ({given} given)")
        else:
            raise NotImplementedError(spec, args, kwargs)
        s = "s" if allowed > 1 else ""
        raise TypeError(msg.format(
            func=func, allowed=allowed, s=s, given=given))


class PythonCall_py33(_PythonCall):
    """
    Wrapper that can call a function with python 3.3 calling semantics
    """

    def resolve(self, args, kwargs):
        func = self._func
        spec = self._spec
        # Check if the function accepts positional arguments
        if spec.args == []:
            slots = None
        else:
            slots = [Unfilled] * len(spec.args)
        # Check if the function accepts keyword arguments
        if spec.varkw is None:
            varkw = None
        else:
            varkw = {}
        # Check if the function accepts keyword-only arguments
        if spec.kwonlyargs == []:
            kwonlyargs = None
        else:
            kwonlyargs = {}
        # Consume positional arguments and fill in the leftmost slots
        for index in range(min(len(args), len(spec.args))):
            slots[index] = args[index]
        # Consume keyword arguments
        for kwname in (list(kwargs.keys())):
            value = kwargs[kwname]
            # First attempt to resolve each keyword argument as normal function
            # argument by looking up the slot it names
            try:
                index = spec.args.index(kwname)
            except ValueError:
                # Keyword arguments that don't map to a slot are either
                # collected to keyword arguments or (UNIMPLEMENTED) passed as
                # keyword-only arguments
                if kwname in spec.kwonlyargs:
                    kwonlyargs[kwname] = value
                elif varkw is not None:
                    varkw[kwname] = value
                else:
                    raise TypeError(
                        "{}() got an unexpected keyword argument {!r}".format(
                            func.__name__, kwname))
            else:
                # Keyword arguments might attempt to provide a value to slot
                # already covered by positional arguments, this is a TypeError
                if slots[index] is Unfilled:
                    slots[index] = value
                else:
                    raise TypeError(
                        "{}() got multiple values for argument {!r}".format(
                            func.__name__, kwname))
        # Any unfilled slots are assigned with default values
        # The values are copied right-to-left here
        if spec.defaults is not None:
            for index1, value in enumerate(reversed(spec.defaults), 1):
                if slots[len(spec.args) - index1] is Unfilled:
                    slots[len(spec.args) - index1] = value
        # Any unfilled slot at this time is a TypeError
        if slots is not None:
            missing_slots = [
                spec.args[index]
                for index in range(len(spec.args))
                if slots[index] is Unfilled]
            if missing_slots:
                if len(missing_slots) == 1:
                    missing_slot_names = repr(missing_slots[0])
                else:
                    missing_slot_names = ', '.join([
                        repr(slot_name)
                        for slot_name in missing_slots[:1]])
                    missing_slot_names += " and %r" % missing_slots[-1]
                raise TypeError(
                    "{func}() missing {missing} required positional"
                    " argument{s}: {missing_slot_names}".format(
                        func=func.__name__,
                        missing=len(missing_slots),
                        s="" if len(missing_slots) == 1 else "s",
                        missing_slot_names=missing_slot_names))
        # Check if the function accepts a variable argument list
        if spec.varargs is None:
            # Report excess positional arguments as TypeError
            if len(args) > len(spec.args):
                self._raise_args_mismatch(args, kwargs)
            varargs = None
        else:
            # Convert excess positional arguments to variable argument list
            varargs = tuple(args[len(spec.args):])
        # Any unfilled keyword-only arguments are assigned with default values
        if spec.kwonlydefaults is not None:
            kwonlyargs.update(spec.kwonlydefaults)
        # Any missing keyword-only arguments is a TypeError
        for kwname in spec.kwonlyargs:
            if kwname not in kwonlyargs:
                raise TypeError(
                    "%s() needs keyword-only argument %s" % (
                        func.__name__, kwname))
        # All done, return the values for function application
        if slots is None:
            slots = ()
        else:
            slots = tuple(slots)
        return call_resolution(slots, varargs, varkw, kwonlyargs)

    def _raise_args_mismatch(self, args, kwargs):
        spec = self._spec
        func = self._func.__name__
        given = len(args) + len(kwargs)
        allowed = len(spec.args)
        required = allowed
        if spec.defaults is not None:
            required -= len(spec.defaults)
        was = "was" if given == 1 else "were"
        if len(args) > len(spec.args) and spec.defaults is None:
            msg = ("{func}() takes {allowed} positional argument{s}"
                   " but {given} {was} given")
        elif len(args) < len(spec.args) and spec.defaults is None:
            msg = ("{func}() takes exactly {allowed} argument{s}"
                   " ({given} given)")
        elif len(args) > len(spec.args) and spec.defaults is not None:
            msg = ("{func}() takes from {required} to {allowed}"
                   " positional argument{s} but {given} {was} given")
        elif len(args) < len(spec.args) and spec.defaults is not None:
            allowed = len(spec.args) - len(spec.defaults)
            msg = ("{func}() takes at least {allowed} argument{s}"
                   " but {given} {was} given")
        else:
            raise NotImplementedError(spec, args, kwargs)
        if allowed != required:
            s = "s"
        else:
            s = "" if allowed == 1 else "s"
        raise TypeError(msg.format(
            func=func, required=required, allowed=allowed, s=s, was=was,
            given=given))


if version_info.major == 3 and version_info.minor == 1:
    PythonCall = PythonCall_py31
elif version_info.major == 3 and version_info.minor == 2:
    PythonCall = PythonCall_py32
elif version_info.major == 3 and version_info.minor == 3:
    PythonCall = PythonCall_py33
else:
    raise NotImplementedError(
        "PythonCall is not supported in python {}".format(version_info))
