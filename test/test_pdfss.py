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


def _relayout(filename):
    filepath = datafile(filename)
    with open(filepath) as stream:
        p1 = read_py(stream.read())['page1']

    # set min_x to 12 to drop vertical text in the page left margin
    result = []
    for group in pdfss.relayout(p1, min_x=12):
        group_result = []
        result.append(group_result)

        for line in group:
            group_result.append([text_group.text
                                 for text_group in line.blocks])

    return result


class RelayoutTC(unittest.TestCase):
    maxDiff = None

    def test_1(self):
        result = _relayout('edf_c1_10080595767_p1.py')
        self.assertEqual(
            result,
            [
                [['1 / 14']],
                [['x']],
                [['d', 'ba']],
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
                [['Service 0,05 € /min'], ['+ prix appel']],
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
                     'recouvrement par facture de 40,00 € .'],
                    ['Les prochaines étapes'],
                    ['• Prochaine facture vers le 01/09/2018 (sauf résiliation '
                     'intervenue entre temps)'],
                ],
                [['I']],
                [['Electricité']],
            ]
        )

    def test_2(self):
        result = _relayout('edf_c2_10073292263_p1.py')
        self.assertEqual(
            result,
            [
                [['1 / 30']],
                [['h']],
                [['c', 'ba']],
                [
                    ['FLX05700098700057-07RI'],
                    ['Code EDI : 000000900'],
                    ['WAX DE SURF'],
                    ['99 RUE NIEVE'],
                    ['SERVICE COMPTABILITE'],
                    ['CS 61999'],
                    ['75014 PARIS CEDEX 99'],
                ],
                [
                    ['Vos contacts'],
                    ['Votre interlocuteur EDF'],
                    ['Relation Clientèle SIPPEREC'],
                    ['Par courrier'],
                    ['Relation Clientèle SIPPEREC'],
                    ['TSA 71004'],
                    ['92099 LA DEFENSE CEDEX'],
                    ['Par internet'],
                    ['e-mail : edfcollectivites-sipperec@edf.fr'],
                    ['www.edfcollectivites.fr'],
                    ['Par téléphone'],
                    ['Du lundi au vendredi de 8h à 18h'],
                    ['09 70 81 82 69'],
                    ['Urgence'],
                    ['N° de tél. dépannage : voir le détail de facturation'],
                    ['par site'],
                    ['Vos informations client'],
                    ['Vos références'],
                    ['Compte de facturation : 923422'],
                    ['Compte commercial : 1-2QG'],
                    ['Accord Cadre : Accord-cadre1lot7:201'],
                    ['N° EJ : 270'],
                    ['CSE : 15'],
                ],
                [['COPIE']],
                [['(service gratuit + prix d’appel)']],
                [
                    ['Facture du 26/02/2018'],
                    ['n° 1007329'],
                    ['Montant Hors TVA', '560 353,17 €'],
                    ['Montant TVA (payée sur les débits)', '112 070,63 €'],
                    ['Facture TTC', '672 423,80 €'],
                    ['Montant restant dû avant facture', '1 084 117,12 €'],
                    ["Des montants dûs antérieurs n'ont pas été totalement "
                     "réglés."],
                    ['Montant total à payer (TTC)', '1 756 540,92 €'],
                    ['à régler avant le 28/03/2018'],
                    ["Tout retard de paiement donnera lieu au versement "
                     "d'intérêts moratoires et d'une indemnité forfaitaire "
                     "pour"],
                    ['frais de recouvrement dans les conditions règlementaires '
                     'en vigueur.'],
                    ['Les prochaines étapes'],
                    ['• Prochaine facture vers le 26/03/2018 (sauf résiliation '
                     'intervenue entre temps)'],
                ],
                [['I']],
                [['Electricité']],
                [
                    ['Paiement par Prélèvement automatique'],
                    ["Vous serez prélevé d'un montant de", '1 756 540,92 €'],
                    ['à partir du :', '28/03/2018'],
                    ['sur le compte bancaire : FR XX XXXXX XXXXX '
                     '00002009999 XX'],
                ]
            ]
        )

    def test_3(self):
        result = _relayout('edf_c2_10073292263_p18.py')
        self.assertEqual(
            result,
            [
                [['18 / 30']],
                [
                    ['USINE DES ZONES'],
                    ['Détail de votre facture du 26/02/2018 n° 1007329'],
                    ['Données contrat', 'Données Point de Livraison'],
                    ['Contrat Electricité Structuré',
                     '9 ROUTE DE SAINT MARCELE 98765 LES AUTRE'],
                    ['Réf. de votre contrat 1-1Y9', 'WRAPPED'],
                    ['Prix non réglementés',
                     'Info. site personnalisée : 3795-SIP'],
                    ['Souscrit depuis le 13/07/2016'],
                    ['Venant à échéance le 31/12/2017'],
                    ['Groupe de sites : C2 5P-SDT'],
                ],
                [['COPIE']],
                [
                    ['Données de comptage',
                     'Puissance(s) souscrite(s) (kW ou kVA)'],
                    ['Identifiant de comptage : 021539999999 Type de '
                     'compteur : Compteur HTA SAPHIR',
                     'Operateur Heures de pointe',
                     '528'],
                    ['Pertes Joule : 1,000',
                     'Opérateur Heures pleines hiver', '528'],
                    ['Acheminement : Tarif HTA5 à Pointe Fixe Longue '
                     'Utilisation',
                     'Opérateur Heures creuses hiver',
                     '528'],
                    ['Puissance souscrite actuelle (kW ou kVA) : 528',
                     'Opérateur Heures pleines été',
                     '528'],
                    ['Changement de saison tarifaire: été du 01/04 au 31/10 et '
                     'hiver du 01/11 au '
                     '31/03',
                     'Opérateur Heures creuses été',
                     '528'],
                ],
                [
                    ['Index Acheminement (relevés/estimés)',
                     'index de début',
                     'index de fin',
                     'Puissances atteintes (kW ou kVA)'],
                    ['Pointe',
                     '10787 le 01/12/2017',
                     '55818 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Pointe',
                     '519'],
                    ['Heures Pleines Hiver',
                     '251088 le 01/12/2017',
                     '386186 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Pleines Hiver',
                     '522'],
                    ['Heures Creuses Hiver',
                     '184001 le 01/12/2017',
                     '323459 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Creuses Hiver',
                     '507'],
                    ['Heures Pleines Eté',
                     '832841 le 01/12/2017',
                     '832841 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Pleines Eté',
                     '0'],
                    ['Heures Creuses Eté',
                     '612464 le 01/12/2017',
                     '612464 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Creuses Eté',
                     '0'],
                ],
                [
                    ['Index Fourniture (relevés / estimés)',
                     'index de début', 'index de fin'],
                    ['Cadran EA1 : Heures Pleines Hiver -'],
                    ['Postes Marché'],
                    ['Cadran EA2 : Heures Creuses Hiver'],
                    ['- Postes Marché'],
                    ['Cadran EA3 : Heures Pleines Eté -'],
                    ['Postes Marché'],
                    ['Cadran EA4 : Heures Creuses Eté -'],
                    ['Postes Marché'],
                ], [
                    ['283836 le 01/12/2017', '393906 le 31/12/2017'],
                    ['485157 le 01/12/2017', '694675 le 31/12/2017'],
                    ['413142 le 01/12/2017', '413142 le 31/12/2017'],
                    ['709046 le 01/12/2017', '709046 le 31/12/2017'],
                ]

            ]
        )

    def test_4(self):
        result = _relayout('edf_c2_10073292263_p30.py')
        self.assertEqual(
            result,
            [
                [['30 / 30']],
                [
                    ['USINE TRAITEMENT'],
                    ['Détail de votre facture du 26/02/2018 n° 1007329'],
                    ['Données contrat', 'Données Point de Livraison'],
                    ['Contrat Electricité Structuré',
                     '98 AVENUE BAVEU LIMAS 75014 PARIS'],
                    ['Réf. de votre contrat 1-1Y9P',
                     'Info. site personnalisée : 3795-SIP_EL_13'],
                    ['Prix non réglementés'],
                    ['Venant à échéance le 31/12/2017'],
                    ['Groupe de sites : C2 5P-SDT'],
                ],
                [
                    ['COPIE'],
                ],
                [
                    ['Données de comptage',
                     'Puissance(s) souscrite(s) (kW ou kVA)'],
                    ['Identifiant de comptage : 021539000000 Type de compteur '
                     ': Compteur HTA SAPHIR',
                     'Operateur Heures de pointe', '585'],
                    ['Pertes Joule : 1,000',
                     'Opérateur Heures pleines hiver', '585'],
                    ['Acheminement : Tarif HTA5 à Pointe Fixe '
                     'Longue Utilisation',
                     'Opérateur Heures creuses hiver',
                     '585'],
                    ['Puissance souscrite actuelle (kW ou kVA) : 585',
                     'Opérateur Heures pleines été', '585'],
                    ['Changement de saison tarifaire: été du 01/04 au 31/10 '
                     'et hiver du 01/11 au 31/03',
                     'Opérateur Heures creuses été',
                     '585'],
                ],
                [
                    ['Index (relevés / estimés)',
                     'index de début',
                     'index de fin',
                     'Puissances atteintes (kW ou kVA)'],
                    ['Pointe',
                     '0 le 01/12/2017',
                     '14650 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Pointe',
                     '171'],
                    ['Heures Pleines Hiver',
                     '54895 le 01/12/2017',
                     '98439 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Pleines Hiver',
                     '170'],
                    ['Heures Creuses Hiver',
                     '39319 le 01/12/2017',
                     '84370 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Creuses Hiver',
                     '170'],
                    ['Heures Pleines Eté',
                     '183028 le 01/12/2017',
                     '183028 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Pleines Eté',
                     '0'],
                    ['Heures Creuses Eté',
                     '136815 le 01/12/2017',
                     '136815 le 31/12/2017',
                     'du 01/12/2017 au 31/12/2017 : Heures Creuses Eté',
                     '0'],
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
