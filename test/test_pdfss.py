import doctest
from io import StringIO
from os.path import abspath, dirname, join
import unittest

import pdfss


HERE = abspath(dirname(__file__))


def datafile(*filename):
    return join(HERE, 'data', *filename)


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


def load_tests(loader, tests, ignore):
    tests.addTests(
        doctest.DocTestSuite('pdfss',
                             optionflags=doctest.NORMALIZE_WHITESPACE)
    )
    return tests


if __name__ == '__main__':
    unittest.main()
