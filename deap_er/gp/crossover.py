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
from .dtypes import *
from collections import defaultdict
from functools import partial
from operator import eq, lt
import random


__all__ = ['cx_one_point', 'cx_one_point_leaf_biased']


# ====================================================================================== #
def cx_one_point(ind1: GPIndividual, ind2: GPIndividual) -> GPMates:
    """
    Randomly selects a crossover point in each individual and exchanges
    each subtree with the point as the root between each individual.

    :param ind1: The first individual to mate.
    :param ind2: The second individual to mate.
    :return: Two mated individuals.

    :type ind1: :ref:`GPIndividual <datatypes>`
    :type ind2: :ref:`GPIndividual <datatypes>`
    :rtype: :ref:`GPMates <datatypes>`
    """
    if len(ind1) < 2 or len(ind2) < 2:
        return ind1, ind2

    types1 = defaultdict(list)
    types2 = defaultdict(list)
    if ind1.root.ret == object:
        types1[object] = list(range(1, len(ind1)))
        types2[object] = list(range(1, len(ind2)))
        common_types = [object]
    else:
        for idx, node in enumerate(ind1[1:], 1):
            types1[node.ret].append(idx)
        for idx, node in enumerate(ind2[1:], 1):
            types2[node.ret].append(idx)
        common_types = set(types1.keys()).intersection(set(types2.keys()))

    if len(common_types) > 0:
        type_ = random.choice(list(common_types))

        index1 = random.choice(types1[type_])
        index2 = random.choice(types2[type_])
        slice1 = ind1.search_subtree(index1)
        slice2 = ind2.search_subtree(index2)
        ind1[slice1], ind2[slice2] = ind2[slice2], ind1[slice1]

    return ind1, ind2


# -------------------------------------------------------------------------------------- #
def cx_one_point_leaf_biased(ind1: GPIndividual, ind2: GPIndividual,
                             term_prob: float) -> GPMates:
    """
    Randomly selects a crossover point in each individual and exchanges
    each subtree with the point as the root between each individual.

    :param ind1: The first individual to mate.
    :param ind2: The second individual to mate.
    :param term_prob: The probability of selecting
        a terminal node as the crossover point.
    :return: Two mated individuals.

    :type ind1: :ref:`GPIndividual <datatypes>`
    :type ind2: :ref:`GPIndividual <datatypes>`
    :rtype: :ref:`GPMates <datatypes>`
    """
    if len(ind1) < 2 or len(ind2) < 2:
        return ind1, ind2

    terminal_op = partial(eq, 0)
    primitive_op = partial(lt, 0)
    arity_op1 = terminal_op if random.random() < term_prob else primitive_op
    arity_op2 = terminal_op if random.random() < term_prob else primitive_op

    types1 = defaultdict(list)
    types2 = defaultdict(list)

    for idx, node in enumerate(ind1[1:], 1):
        if arity_op1(node.arity):
            types1[node.ret].append(idx)

    for idx, node in enumerate(ind2[1:], 1):
        if arity_op2(node.arity):
            types2[node.ret].append(idx)

    common_types = set(types1.keys()).intersection(set(types2.keys()))

    if len(common_types) > 0:
        type_ = random.sample(common_types, 1)[0]

        index1 = random.choice(types1[type_])
        index2 = random.choice(types2[type_])
        slice1 = ind1.search_subtree(index1)
        slice2 = ind2.search_subtree(index2)
        ind1[slice1], ind2[slice2] = ind2[slice2], ind1[slice1]

    return ind1, ind2
