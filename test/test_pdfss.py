import doctest
from io import StringIO
from os.path import abspath, dirname, join
import unittest

import pdfss


HERE = abspath(dirname(__file__))


def datafile(*filename):
    return join(HERE, 'data', *filename)


def read_py(code):
    exec_globals = {}
    exec_locals = {}
    exec(code, exec_globals, exec_locals)
    return exec_locals


class PDF2TextTC(unittest.TestCase):

    def test(self):
        filepath = datafile('Lentilles.pdf')
        with open(filepath, 'rb') as stream:
            text_stream = pdfss.pdf2text(stream)

        text = text_stream.read()
        self.assertTrue(
            text.startswith('Galettes de lentilles\nDes lentilles'),
            text
        )


class DumpPDFStructureTC(unittest.TestCase):

    def test(self):
        filepath = datafile('Lentilles.pdf')
        output = StringIO()
        pdfss.dump_pdf_structure(filepath, file=output)

        text = output.getvalue()
        self.assertIn(
            r"<LTTextLineHorizontal 56.800,610.708,156.004,627.304 "
            r"'Galettes de lentilles\n'>",
            text
        )


class PyDumpTC(unittest.TestCase):

    def test(self):
        filepath = datafile('Lentilles.pdf')
        out = StringIO()
        pdfss.py_dump(filepath, out=out)

        exec_locals = read_py(out.getvalue())
        self.assertIn('page1', exec_locals)
        self.assertIn('page2', exec_locals)


class fake_ltobj:
    def __init__(self, text):
        self.lower_text = text.lower()


class DebugProcessorTC(unittest.TestCase):
    def test(self):
        state, ltobj = 'state', fake_ltobj('text data')

        def gen():
            sent_back = (yield state + '1', ltobj)
            self.assertEqual(sent_back, (True, 'new state'))

            sent_back = (yield state + '2', ltobj)
            self.assertEqual(sent_back, (False, 'end state'))

        processor = iter(pdfss.debug_processor(iter(gen()), {}))
        with self.assertLogs('lowatt') as cm:

            yielded = next(processor)
            self.assertEqual(yielded, (state + '1', ltobj))

            yielded = processor.send((True, 'new state'))
            self.assertEqual(yielded, (state + '2', ltobj))

            with self.assertRaises(StopIteration):
                processor.send((False, 'end state'))

        self.assertEqual(
            cm.output,
            [
                "INFO:lowatt.pdfss:[state1] 'text data'",
                "INFO:lowatt.pdfss:[state2] 'text data'"
            ]
        )


class SimpleLtobjProcessorTC(unittest.TestCase):
    def test(self):
        state, ltobj = 'state', fake_ltobj('text data')

        def gen():
            sent_back = (yield state + '1', ltobj)
            self.assertEqual(sent_back, (True, 'new state 1'))

            sent_back = (yield state + '2', ltobj)
            self.assertEqual(sent_back, (False, 'func state processed'))

            sent_back = (yield state + '1', ltobj)
            self.assertEqual(sent_back, (True, 'new state 2'))

        def func(state, ltobj, data):
            self.assertIn(state, ('state1', 'state2'))
            if state == 'state1':
                return False, 'func state recurs'
            return True, 'func state processed'

        processor = iter(pdfss.simple_ltobj_processor(func)(iter(gen()), {}))

        yielded = next(processor)
        self.assertEqual(yielded, ('func state recurs', ltobj))

        yielded = processor.send((True, 'new state 1'))
        self.assertEqual(yielded, ('func state recurs', ltobj))

        with self.assertRaises(StopIteration):
            processor.send((True, 'new state 2'))


def load_tests(loader, tests, ignore):
    tests.addTests(
        doctest.DocTestSuite('pdfss',
                             optionflags=doctest.NORMALIZE_WHITESPACE)
    )
    return tests


if __name__ == '__main__':
    unittest.main()
