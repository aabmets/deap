#
#   MIT License
#   
#   Copyright (c) 2022, Mattias Aabmets
#   
#   The contents of this file are subject to the terms and conditions defined in the License.
#   You may not use, modify, or distribute this file except in compliance with the License.
#   
#   SPDX-License-Identifier: MIT
#
from deap_er.creator import overrides as ovr
from copy import deepcopy
import pickle
import array
import numpy


# ====================================================================================== #
class TestNumpyOverrideClass:

    def test_numpy_override_instantiation(self):
        data = [x for x in range(0, 10)]
        obj = ovr._NumpyOverride(data)
        assert isinstance(obj, ovr._NumpyOverride)
        assert issubclass(ovr._NumpyOverride, numpy.ndarray)

    # -------------------------------------------------------- #
    def test_numpy_override_deepcopy(self):
        data = [x for x in range(0, 10)]
        obj = ovr._NumpyOverride(data)
        copy = deepcopy(obj)
        assert isinstance(copy, numpy.ndarray)
        assert all(obj == copy)
        assert obj.__dict__ == copy.__dict__

    # -------------------------------------------------------- #
    def test_numpy_override_pickling(self):
        data = [x for x in range(0, 10)]
        obj = ovr._NumpyOverride(data)
        jar = pickle.dumps(obj)
        copy = pickle.loads(jar)
        assert all(obj == copy)
        assert obj.__dict__ == copy.__dict__

    # -------------------------------------------------------- #
    def test_array_override_reduction(self):
        data = [x for x in range(0, 10)]
        obj = ovr._NumpyOverride(data)
        cls, args, state = obj.__reduce__()
        assert cls == ovr._NumpyOverride
        assert isinstance(args, tuple)
        assert isinstance(state, dict)


# ====================================================================================== #
class TestArrayOverrideClass:
    ovr._ArrayOverride.typecode = 'i'

    def test_array_override_instantiation(self):
        data = [x for x in range(0, 10)]
        obj = ovr._ArrayOverride(data)
        assert isinstance(obj, ovr._ArrayOverride)
        assert issubclass(ovr._ArrayOverride, array.array)

    # -------------------------------------------------------- #
    def test_array_override_deepcopy(self):
        data = [x for x in range(0, 10)]
        obj = ovr._ArrayOverride(data)
        copy = deepcopy(obj)
        assert isinstance(copy, array.array)
        assert obj == copy
        assert obj.__dict__ == copy.__dict__

    # -------------------------------------------------------- #
    def test_array_override_pickling(self):
        data = [x for x in range(0, 10)]
        obj = ovr._ArrayOverride(data)
        jar = pickle.dumps(obj)
        copy = pickle.loads(jar)
        assert obj == copy
        assert obj.__dict__ == copy.__dict__

    # -------------------------------------------------------- #
    def test_array_override_reduction(self):
        data = [x for x in range(0, 10)]
        obj = ovr._ArrayOverride(data)
        cls, args, state = obj.__reduce__()
        assert cls == ovr._ArrayOverride
        assert isinstance(args, tuple)
        assert isinstance(state, dict)
