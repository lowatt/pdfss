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


class RelayoutTC(unittest.TestCase):
    maxDiff = None

    def test(self):
        filepath = datafile('edf_c1_10080595767_p1.py')
        with open(filepath) as stream:
            p1 = read_py(stream.read())['page1']

        # set min_x to 12 to drop vertical text in the page left margin
        result = []
        for group in pdfss.relayout(p1, min_x=12):
            group_result = []
            result.append(group_result)

            for line in group:
                group_result.append([text_group.text
                                     for text_group in line.groups])

        self.assertEqual(
            result,
            [
                [['1 / 14']],
                [['x']],
                [['a']],
                [['d', 'b']],
                [
                    ['Vos contacts'],
                    ['Votre interlocuteur EDF'],
                    ['RC Grandes - Entreprises et Collectivités'],
                    ['Par courrier'],
                    ['Direction Commerciale Régionale'],
                    ['TSA 70102'],
                    ['33070 BORDEAUX CEDEX'],
                    ['Par internet'],
                    ['e-mail : edfentreprises-sud-ouest-31@edf.fr'],
                    ['www.edfentreprises.fr'],
                    ['Par téléphone'],
                    ['Du lundi au vendredi de 8h à 18h'],
                    ['Urgence'],
                    ['N° de tél. dépannage : voir le détail de facturation'],
                    ['par site'],
                    ['Vos informations client'],
                    ['Vos références'],
                    ['Compte de facturation : 520861'],
                    ['Compte commercial : 1-37XU'],
                ],
                [
                    ['FLX22390212900027-07RS'],
                    ['NOTRE CLIENT'],
                    ['42 RUE DU GRAS'],
                    ['31560 NAILLOUX'],
                ],
                [['COPIE']],
                [['Service 0,05 €', '/min'], ['+ prix appel']],
                [['0 812 041 533']],
                [
                    ['Facture du 01/08/2018'],
                    ['n° 1008059'],
                    ['Montant Hors TVA', '-1 882,35 €'],
                    ['Montant TVA (payée sur les débits)', '-386,88 €'],
                    ['Facture TTC', '-2 269,23 €'],
                    ['Montant total (TTC)', '-2 269,23 €'],
                    ['Compte tenu de la situation de votre compte, '
                     'un montant de 2 269,23 €'],
                    ['en votre faveur vous sera remboursé sous 15 jours.'],
                    ['A défaut de paiement à la date prévue, le montant TTC '
                     'dû sera majoré de pénalités pour retard au taux'],
                    ["annuel de 10,00 % et d'une indemnité pour frais de "
                     'recouvrement par facture de 40,00 €',
                     '.'],
                    ['Les prochaines étapes'],
                    ['•'],
                ],
                [['I']],
                [['Electricité']],
                [
                    ['Prochaine facture vers le 01/09/2018 (sauf résiliation '
                     'intervenue entre temps)'],
                ],
            ]
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
