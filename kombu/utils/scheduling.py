"""
    kombu.utils.scheduling
    ~~~~~~~~~~~~~~~~~~~~~~

    Consumer utilities.

"""
from __future__ import absolute_import

from itertools import count

from . import symbol_by_name

__all__ = ['FairCycle', 'priority_cycle', 'round_robin_cycle', 'sorted_cycle']


class FairCycle(object):
    """Consume from a set of resources, where each resource gets
    an equal chance to be consumed from."""

    def __init__(self, fun, resources, predicate=Exception):
        self.fun = fun
        self.resources = resources
        self.predicate = predicate
        self.pos = 0

    def _next(self):
        while 1:
            try:
                resource = self.resources[self.pos]
                self.pos += 1
                return resource
            except IndexError:
                self.pos = 0
                if not self.resources:
                    raise self.predicate()

    def get(self, **kwargs):
        for tried in count(0):  # for infinity
            resource = self._next()

            try:
                return self.fun(resource, **kwargs), resource
            except self.predicate:
                if tried >= len(self.resources) - 1:
                    raise

    def close(self):
        pass

    def __repr__(self):
        return '<FairCycle: {self.pos}/{size} {self.resources}>'.format(
            self=self, size=len(self.resources))


class round_robin_cycle(object):

    def __init__(self, it=None):
        self.items = it if it is not None else []

    def update(self, it):
        self.items[:] = it

    def consume(self, n):
        return self.items[:n]

    def rotate(self, last_used):
        """Move most recently used item to end of list."""
        items = self.items
        try:
            items.append(items.pop(items.index(last_used)))
        except ValueError:
            pass


class priority_cycle(round_robin_cycle):

    def rotate(self, last_used):
        pass


class sorted_cycle(priority_cycle):

    def consume(self, n):
        return sorted(self.items[:n])


CYCLE_ALIASES = {
    'priority': 'kombu.utils.scheduling:priority_cycle',
    'round_robin': 'kombu.utils.scheduling:round_robin_cycle',
    'sorted': 'kombu.utils.scheduling:sorted_cycle',
}


def cycle_by_name(name):
    return symbol_by_name(name, CYCLE_ALIASES)
