import unittest
import math

from bisect_b2g.evaluator import Evaluator
from bisect_b2g.bisection import Bisection
from bisect_b2g.repository import Rev

from mock import Mock, call


class ConsistentEvaluator(Evaluator):

    def __init__(self, result):
        Evaluator.__init__(self)
        self.result = result

    def eval(self, x):
        return self.result


class GoneTooFar(Exception):
    pass


class OrderedEvaluator(Evaluator):

    def __init__(self, order, count):
        Evaluator.__init__(self)
        assert len(order) >= round(math.log(count, 2))
        for x in order:
            assert x is True or x is False
        self.order = order
        self.index = 0

    def eval(self, test):
        if self.index > len(self.order) - 1:
            raise GoneTooFar(self.index)
        value = self.order[self.index]
        self.index += 1
        return value


class MetaTestEvaluators(unittest.TestCase):

    def test_consistent_evaluator(self):
        evaluator = ConsistentEvaluator(True)
        self.assertTrue(evaluator.eval(None))
        self.assertTrue(evaluator.eval(None))

    def test_ordered_evaluator(self):
        order = [True, False, True, False]
        evaluator = OrderedEvaluator(order, 16)
        for i in order:
            self.assertEqual(i, evaluator.eval(None))
        self.assertRaises(GoneTooFar,
                          evaluator.eval,
                          None)


class BisectionTest(unittest.TestCase):

    def build_history(self, items):
        return [[Rev(x, self.project, None)] for x in items]

    def build_varied_assets(self, trues, count):
        assert len(trues) <= round(math.log(count, 2))
        order = [True if x in trues else False for x in range(count)]
        history = self.build_history(range(len(order)))
        return OrderedEvaluator(order, len(order)), history

    def validate_calls(self, order_list):
        calls = [call(x) for x in order_list]
        self.project.set_rev.assert_has_calls(calls)

    def setUp(self):
        self.project = Mock(
            name='name',
            url='https://example.com',
            local_path='local_path',
            good='good',
            bad='bad',
            vcs='git',
        )

        self.history = self.build_history(range(10))

    def test_all_good(self):
        all_good = Bisection(
            [self.project], self.history,
            ConsistentEvaluator(True))
        self.assertEqual(
            self.history[len(self.history) - 1][0].hash,
            all_good.found[0].hash)
        self.assertEqual(len(self.history) - 1, all_good.found_i)
        self.assertEqual(all_good.order, all_good.pass_i)
        self.validate_calls([5, 7, 8, 9])

    def test_all_bad(self):
        all_bad = Bisection(
            [self.project], self.history,
            ConsistentEvaluator(False))
        self.assertEqual(
            self.history[0][0].hash,
            all_bad.found[0].hash)
        self.assertEqual(0, all_bad.found_i)
        self.assertEqual([], all_bad.pass_i)
        self.assertEqual([5, 2, 1, 0], all_bad.order)
        self.validate_calls(all_bad.order)

    def test_true_on_2_of_10(self):
        trues = (2,)
        count = 10
        evaluator, history = self.build_varied_assets(trues, count)
        bisect = Bisection([self.project], history, evaluator)
        self.validate_calls(bisect.order)
        self.assertEqual(1, bisect.found_i)
        self.assertEqual([5, 2, 1], bisect.order)

    def test_true_on_1_and_2_of_10(self):
        trues = (1, 2)
        count = 10
        evaluator, history = self.build_varied_assets(trues, count)
        bisect = Bisection([self.project], history, evaluator)
        self.validate_calls(bisect.order)
        self.assertEqual(3, bisect.found_i)
        self.assertEqual([5, 2, 3, 4], bisect.order)
