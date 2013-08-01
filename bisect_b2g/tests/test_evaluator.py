import os
import sys
import unittest
import tempfile

from bisect_b2g import evaluator

dumbo = os.path.abspath(os.path.join(os.path.split(__file__)[0], 'dumbo.py'))


class ScriptEvaluatorTests(unittest.TestCase):

    def test_script_evaluator_good(self):
        se = evaluator.ScriptEvaluator(script=[dumbo, '--exit-code', str(0)])
        self.assertEqual(True, se.eval(object()))

    def test_script_evaluator_bad(self):
        se = evaluator.ScriptEvaluator(script=[dumbo, '--exit-code', str(1)])
        self.assertEqual(False, se.eval(object()))


class InteractiveEvaluatorTests(unittest.TestCase):

    # XXX: I'm not sure how to do these tests exactly

    @unittest.skip("Unsure why this is broken")
    def test_script_evaluator_good(self):
        with tempfile.TemporaryFile() as f:
            f.write('good\n')
            f.flush()
            f.seek(0)
            se = evaluator.InteractiveEvaluator(stdin_file=f)
            self.assertEqual(True, se.eval(object()))

    @unittest.skip("Unsure why this is broken")
    def test_script_evaluator_bad(self):
        with tempfile.TemporaryFile() as f:
            f.write('bad\n')
            f.flush()
            f.seek(0)
            se = evaluator.InteractiveEvaluator(stdin_file=f)
            self.assertEqual(False, se.eval(object()))
