# Copyright 2012 Canonical Ltd.
# Written by:
#   Zygmunt Krynicki <zygmunt.krynicki@canonical.com>
# See COPYING for license

"""
call.tests
==========

Unit tests for the call package
"""

from collections import OrderedDict
from sys import version_info
from unittest import TestCase

from call import PythonCall


class CallTestMixIn:
    """
    Mix-In that automates most of PythonCall testing
    """

    @property
    def _fail_scenarios(self):
        return getattr(self, "_fail_scenarios_py{}{}".format(
            version_info.major, version_info.minor))

    def assertFailureMode(self, call, scenario):
        args, kwargs, expected_error = scenario
        with self.assertRaises(TypeError):
            try:
                call.apply(args, kwargs)
            except TypeError as exc:
                exc_native = exc
                raise
            else:
                exc_native = None
        with self.assertRaises(TypeError):
            try:
                call.resolve(args, kwargs)
            except TypeError as exc:
                exc_emulated = exc
                raise
            else:
                exc_emulated = None
        self.assertEqual(str(exc_native), str(exc_emulated))
        self.assertEqual(expected_error, str(exc_emulated))

    def test_apply(self):
        for scenario in self._success_scenarios:
            args, kwargs, expected = scenario
            observed = self.call.apply(args, kwargs)
            self.assertEqual(expected, observed)

    def test_bind(self):
        for scenario in self._success_scenarios:
            args, kwargs, expected = scenario
            observed = self.call.bind(args, kwargs)
            self.assertEqual(expected, observed)

    def test_resolve_failure(self):
        for scenario in self._fail_scenarios:
            self.assertFailureMode(self.call, scenario)


class TestFunctionWithoutArgs(TestCase, CallTestMixIn):

    call = PythonCall(lambda: locals())

    _success_scenarios = [
        ([], {}, {}),
    ]

    _fail_scenarios_py31 = [
        ([1], {},
         "<lambda>() takes no arguments (1 given)"),
        ([1, 2], {},
         "<lambda>() takes no arguments (2 given)"),
        ([1, 2], {'x': 1},
         "<lambda>() takes no arguments (3 given)"),
        ([1, 2], OrderedDict((('x', 1), ('y', 2))),
         "<lambda>() takes no arguments (4 given)"),
        ([1], {'x': 1},
         "<lambda>() takes no arguments (2 given)"),
        ([], OrderedDict((('x', 1), ('y', 2))),
         "<lambda>() takes no arguments (2 given)"),
    ]

    _fail_scenarios_py32 = _fail_scenarios_py31

    _fail_scenarios_py33 = [
        ([1], {},
         "<lambda>() takes 0 positional arguments but 1 was given"),
        ([1, 2], {},
         "<lambda>() takes 0 positional arguments but 2 were given"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], OrderedDict((('x', 1), ('y', 2))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 2))),
         "<lambda>() got an unexpected keyword argument 'x'"),
    ]

    def test_resolve_success(self):
        self.assertEqual(self.call.resolve([], {}),
                         ((), None, None, None))


class TestFunctionWithOneArg(TestCase, CallTestMixIn):

    call = PythonCall(lambda a: locals())

    _success_scenarios = [
        ([1], {}, {'a': 1}),
        ([], {'a': 1}, {'a': 1}),
    ]

    _fail_scenarios_py31 = [
        ([], {},
         "<lambda>() takes exactly 1 positional argument (0 given)"),
        ([1, 2], {},
         "<lambda>() takes exactly 1 positional argument (2 given)"),
        ([], {'x': 1}, "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
    ]

    _fail_scenarios_py32 = [
        ([], {},
         "<lambda>() takes exactly 1 argument (0 given)"),
        ([1, 2], {},
         "<lambda>() takes exactly 1 positional argument (2 given)"),
        ([], {'x': 1}, "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
    ]
    _fail_scenarios_py33 = [
        ([], {},
         "<lambda>() missing 1 required positional argument: 'a'"),
        ([1, 2], {},
         "<lambda>() takes 1 positional argument but 2 were given"),
        ([], {'x': 1}, "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
    ]

    def test_resolve_success(self):
        self.assertEqual(self.call.resolve([1], {}),
                         ((1,), None, None, None))
        self.assertEqual(self.call.resolve([], {'a': 1}),
                         ((1,), None, None, None))


class TestFunctionWithTwoArgs(TestCase, CallTestMixIn):

    call = PythonCall(lambda a, b: locals())

    _success_scenarios = [
        ([1, 2], {}, {'a': 1, 'b': 2}),
        ([1], {'b': 2}, {'a': 1, 'b': 2}),
        ([], {'a': 1, 'b': 2}, {'a': 1, 'b': 2})
    ]

    _fail_scenarios_py31 = [
        ([], {},
         "<lambda>() takes exactly 2 positional arguments (0 given)"),
        ([1], {},
         "<lambda>() takes exactly 2 positional arguments (1 given)"),
        ([1, 2, 3], {},
         "<lambda>() takes exactly 2 positional arguments (3 given)"),
        ([1, 2, 3], {'x': 1},
         "<lambda>() takes exactly 2 non-keyword positional arguments"
         " (3 given)"),
        ([1, 2, 3], {'a': 1},
         "<lambda>() takes exactly 2 non-keyword positional arguments"
         " (3 given)"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1], {'a': 1, 'b': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for keyword argument 'b'"),
    ]

    _fail_scenarios_py32 = [
        ([], {},
         "<lambda>() takes exactly 2 arguments (0 given)"),
        ([1], {},
         "<lambda>() takes exactly 2 arguments (1 given)"),
        ([1, 2, 3], {},
         "<lambda>() takes exactly 2 positional arguments (3 given)"),
        ([1, 2, 3], {'x': 1},
         "<lambda>() takes exactly 2 positional arguments (4 given)"),
        ([1, 2, 3], {'a': 1},
         "<lambda>() takes exactly 2 positional arguments (4 given)"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1], {'a': 1, 'b': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for keyword argument 'b'"),
    ]

    _fail_scenarios_py33 = [
        ([], {},
         "<lambda>() missing 2 required positional arguments: 'a' and 'b'"),
        ([1], {},
         "<lambda>() missing 1 required positional argument: 'b'"),
        ([1, 2, 3], {},
         "<lambda>() takes 2 positional arguments but 3 were given"),
        ([1, 2, 3], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2, 3], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
        ([1], {'a': 1, 'b': 1},
         "<lambda>() got multiple values for argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for argument 'b'"),
    ]

    def test_resolve_success(self):
        self.assertEqual(self.call.resolve([1, 2], {}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([1], {'b': 2}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([], {'a': 1, 'b': 2}),
                         ((1, 2), None, None, None))


class TestFunctionWithOneDefaultArg(TestCase, CallTestMixIn):

    call = PythonCall(lambda a=5: locals())

    _success_scenarios = [
        ([1], {}, {'a': 1}),
        ([], {}, {'a': 5}),
        ([], {'a': 3}, {'a': 3})
    ]

    _fail_scenarios_py31 = [
        ([1, 2], {},
         "<lambda>() takes at most 1 positional argument (2 given)"),
        ([1, 2], {'x': 1},
         ("<lambda>() takes at most 1 non-keyword positional argument"
          " (2 given)")),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
    ]

    _fail_scenarios_py32 = [
        ([1, 2], {},
         "<lambda>() takes at most 1 positional argument (2 given)"),
        ([1, 2], {'x': 1},
         "<lambda>() takes at most 1 positional argument (3 given)"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
    ]

    _fail_scenarios_py33 = [
        ([1, 2], {},
         "<lambda>() takes from 0 to 1 positional arguments but 2 were given"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
    ]

    def test_resolve_success(self):
        self.assertEqual(self.call.resolve([1], {}),
                         ((1,), None, None, None))
        self.assertEqual(self.call.resolve([], {'a': 1}),
                         ((1,), None, None, None))
        self.assertEqual(self.call.resolve([], {}),
                         ((5,), None, None, None))


class TestFunctionWithTwoArgumentsAndOneDefault(TestCase, CallTestMixIn):

    call = PythonCall(lambda a, b=5: locals())

    _success_scenarios = [
        ([1], {}, {'a': 1, 'b': 5}),
        ([1, 2], {}, {'a': 1, 'b': 2}),
        ([], {'a': 1, 'b': 2}, {'a': 1, 'b': 2}),
        ([], {'a': 1}, {'a': 1, 'b': 5}),
    ]

    _fail_scenarios_py31 = [
        ([], {},
         "<lambda>() takes at least 1 positional argument (0 given)"),
        ([1, 2, 3], {},
         "<lambda>() takes at most 2 positional arguments (3 given)"),
        ([1, 2, 3], {'x': 1},
         ("<lambda>() takes at most 2 non-keyword positional arguments"
          " (3 given)")),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for keyword argument 'b'"),
    ]

    _fail_scenarios_py32 = [
        ([], {},
         "<lambda>() takes at least 1 argument (0 given)"),
        ([1, 2, 3], {},
         "<lambda>() takes at most 2 positional arguments (3 given)"),
        ([1, 2, 3], {'x': 1},
         "<lambda>() takes at most 2 positional arguments (4 given)"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for keyword argument 'b'"),
    ]

    _fail_scenarios_py33 = [
        ([], {},
         "<lambda>() missing 1 required positional argument: 'a'"),
        ([1, 2, 3], {},
         "<lambda>() takes from 1 to 2 positional arguments but 3 were given"),
        ([1, 2, 3], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for argument 'b'"),
    ]

    def test_resolve_success(self):
        self.assertEqual(self.call.resolve([1, 2], {}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([1], {'b': 2}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([], {'a': 1, 'b': 2}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([1], {}),
                         ((1, 5), None, None, None))
        self.assertEqual(self.call.resolve([], {'a': 1}),
                         ((1, 5), None, None, None))


class TestFunctionWithTwoArgumentsAndTwoDefaults(TestCase, CallTestMixIn):

    call = PythonCall(lambda a=4, b=5: locals())

    _success_scenarios = [
        ([], {}, {'a': 4, 'b': 5}),
        ([], {'a': 1}, {'a': 1, 'b': 5}),
        ([], {'b': 1}, {'a': 4, 'b': 1}),
        ([], {'a': 1, 'b': 2}, {'a': 1, 'b': 2}),
        ([1], {}, {'a': 1, 'b': 5}),
        ([1, 2], {}, {'a': 1, 'b': 2}),
    ]

    _fail_scenarios_py31 = [
        ([1, 2, 3], {},
         "<lambda>() takes at most 2 positional arguments (3 given)"),
        ([1, 2, 3], {'x': 1},
         ("<lambda>() takes at most 2 non-keyword positional arguments"
          " (3 given)")),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for keyword argument 'b'"),
    ]

    _fail_scenarios_py32 = [
        ([1, 2, 3], {},
         "<lambda>() takes at most 2 positional arguments (3 given)"),
        ([1, 2, 3], {'x': 1},
         "<lambda>() takes at most 2 positional arguments (4 given)"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for keyword argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for keyword argument 'b'"),
    ]

    _fail_scenarios_py33 = [
        ([1, 2, 3], {},
         "<lambda>() takes from 0 to 2 positional arguments but 3 were given"),
        ([1, 2, 3], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([], OrderedDict((('x', 1), ('y', 1))),
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'x': 1},
         "<lambda>() got an unexpected keyword argument 'x'"),
        ([1, 2], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
        ([1], {'a': 1},
         "<lambda>() got multiple values for argument 'a'"),
        ([1, 2], {'b': 1},
         "<lambda>() got multiple values for argument 'b'"),
    ]

    def test_resolve_success(self):
        self.assertEqual(self.call.resolve([1, 2], {}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([1], {'b': 2}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([], {'a': 1, 'b': 2}),
                         ((1, 2), None, None, None))
        self.assertEqual(self.call.resolve([1], {}),
                         ((1, 5), None, None, None))
        self.assertEqual(self.call.resolve([], {'a': 1}),
                         ((1, 5), None, None, None))
        self.assertEqual(self.call.resolve([], {}),
                         ((4, 5), None, None, None))
