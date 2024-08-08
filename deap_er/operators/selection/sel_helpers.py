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
import numpy


__all__ = ['assign_crowding_dist', 'uniform_reference_points']


# ====================================================================================== #
def assign_crowding_dist(individuals: list) -> None:
    """
    Assigns a crowding distance to each individual's fitness.
    The crowding distance can be retrieved via the *crowding_dist*
    attribute of each individual's fitness. The individuals
    are modified in-place.

    :param individuals: A list of individuals with Fitness attributes.
    :return: Nothing.
    """

    if len(individuals) == 0:
        return

    distances = [0.0] * len(individuals)
    crowd = [(ind.fitness.values, i) for i, ind in enumerate(individuals)]
    n_obj = len(individuals[0].fitness.values)

    for i in range(n_obj):
        crowd.sort(key=lambda element: element[0][i])
        distances[crowd[0][1]] = float("inf")
        distances[crowd[-1][1]] = float("inf")
        if crowd[-1][0][i] == crowd[0][0][i]:
            continue
        norm = n_obj * float(crowd[-1][0][i] - crowd[0][0][i])
        for prev, cur, next_ in zip(crowd[:-2], crowd[1:-1], crowd[2:]):
            distances[cur[1]] += (next_[0][i] - prev[0][i]) / norm

    for i, dist in enumerate(distances):
        individuals[i].fitness.crowding_dist = dist


# -------------------------------------------------------------------------------------- #
def uniform_reference_points(objectives: int, ref_ppo: int = 4,
                             scaling: float = None) -> numpy.ndarray:
    """
    Generates reference points uniformly on the hyperplane
    intersecting each axis at 1. The scaling factor is used
    to combine multiple layers of reference points.

    :param objectives: Number of objectives.
    :param ref_ppo: Number of reference points per objective, optional.
    :param scaling: Scaling factor, optional.
    :return: Uniform reference points.
    """
    def _recursive(ref, ovs, left, total, depth) -> list:
        points = []
        if depth == ovs - 1:
            ref[depth] = left / total
            points.append(ref)
        else:
            for i in range(left + 1):
                ref[depth] = i / total
                rc = ref.copy()
                li = left - i
                d1 = depth + 1
                result = _recursive(rc, ovs, li, total, d1)
                points.extend(result)
        return points
    
    zeros = numpy.zeros(objectives)
    ref_points = _recursive(zeros, objectives, ref_ppo, ref_ppo, 0)
    ref_points = numpy.array(ref_points)

    if scaling is not None:
        ref_points *= scaling
        ref_points += (1 - scaling) / objectives

    return ref_points
