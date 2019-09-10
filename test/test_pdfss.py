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
    def ltchar_filter(ltchar):
        if ltchar.x0 < 12:
            return False
        if ltchar.fontname == 'PictosSIMM':
            return False
        if ltchar.fontsize > 100:
            return False

        return True

    filepath = datafile(filename)
    with open(filepath) as stream:
        p1 = read_py(stream.read())['page1']

    # set min_x to 12 to drop vertical text in the page left margin
    result = []
    for group in pdfss.relayout(
            p1, ltchar_filter=ltchar_filter,
            skip_text={
                "A défaut de paiement à la date prévue, le",
                "montant TTC dû sera majoré de",
                'pénalités pour retard au taux annuel de',
                "10,05 % et d'une indemnité pour frais de",
                "recouvrement par facture de 40,00 € .",
                "Retrouvez l'ensemble de nos offres",
                ",",
                "des tarifs et autres informations sur la",
                "gestion de votre énergie sur",
                "www.edfentreprises.fr",

                'TVA si',
                'différente',
                'ifférente',
                'du taux',
                'normal',

                '5,50 %',
            },
    ):
        group_result = []
        result.append(group_result)

        for line in group:
            group_result.append([text_group.text
                                 for text_group in line.blocks])

    return result


class RelayoutTC(unittest.TestCase):
    maxDiff = None

    def test_edf_c1_10074973936_p5(self):
        result = _relayout('edf_c1_10074973936_p5.py')
        self.assertEqual(
            result,
            [
                [['5 / 20']],
                [
                    ['BALON OVALE'],
                    ['Détail de votre facturation par site du 02/04/2018 '
                     'n° 1007497'],
                    ['Données contrat', 'Données Point de Livraison'],
                    ['Contrat électricité Prix Fixe',
                     'LE POULAYER 31560 NAILLOUX'],
                    ['Réf. de votre contrat 1-19O',
                     'Réf Acheminement Electricité : 3000161170'],
                    ['Prix non réglementés', 'Code site : 1'],
                    ['Souscrit depuis le 01/11/2015'],
                    ['Venant à échéance le 30/10/2018'],
                    ['Groupe de sites : C3 5P-SDT'],
                ],
                [['Document à conserver 10 ans']],
                [['Urgence'], ['Dépannage Electricité Enedis']],
                [['Service 0,05 € /appel'], ['+ prix appel']],
                [['0 811 010 211']],
                [['Evolution de la consommation facturée en kWh']],
                [['32071']],
                [['31353']],
                [['Volume de kWh'], ['( année en cours )']],
                [['28660']],
                [['28096']],
                [['24896', '24969']],
                [['24008', '23598', '23505']],
                [['21433', '21736']],
                [['Relevé']],
                [['17418']],
                [['15912']],
                [
                    ['Fév 17', 'Mar 17',
                     'Avr 17', 'Mai 17',
                     'Juin 17',
                     'Juil 17',
                     'Aou 17', 'Sept 17 Oct 17', 'Nov 17', 'Déc 17',
                     'Jan 18',
                     'Fév 18'],
                ],
                [
                    ['Total EDF Electricité', '1 336,27 €', 'HT'],
                    ['Abonnement électricité (HT)',
                     'Période',
                     'Prix unitaire HT',
                     '48,38 €', 'Taux de TVA'],
                    ['Abonnement',
                     'du 01/04/2018 au 30/04/2018',
                     '48,38 € /mois',
                     '48,38 €',
                     '20,00 %'],
                    ['Consommation (HT)',
                     'Période',
                     'Conso 25 426 kWh',
                     'Prix unitaire HT',
                     '1 287,89 €', 'Taux de TVA'],
                    ['Estimation Electricité Heures Pleines Hiver',
                     'du 01/03/2018 au 02/04/2018',
                     '14 298 kWh',
                     '5,769 c€ /kWh',
                     '824,85 €',
                     '20,00 %'],
                    ['Estimation Electricité Heures Creuses Hiver',
                     'du 01/03/2018 au 02/04/2018',
                     '9 710 kWh',
                     '4,262 c€ /kWh',
                     '413,84 €',
                     '20,00 %'],
                    ['Estimation Electricité Heures Pleines Eté',
                     'du 01/03/2018 au 02/04/2018',
                     '497 kWh',
                     '4,394 c€ /kWh',
                     '21,84 €',
                     '20,00 %'],
                    ['Estimation Electricité Heures Creuses Eté',
                     'du 01/03/2018 au 02/04/2018',
                     '921 kWh',
                     '2,971 c€ /kWh',
                     '27,36 €',
                     '20,00 %'],
                    ['Services', '0,00 €', 'HT'],
                ],
                [['Assiette', 'Taux de TVA']],
                [
                    ['E-Services (Espace client, Bilan annuel)', 'INCLUS'],
                    ["Taxes et contributions (identiques pour l'ensemble des "
                     "fournisseurs)",
                     '653,22 €', 'Hors TVA'],
                ],
                [['Période', 'Assiette',
                  'Prix unitaire HorsTVA', 'Taux de TVA']],
                [
                    ["Contribution au Service Public de l'Electricité",
                     'du 01/03/2018 au 02/04/2018',
                     '25 427 kWh',
                     '2,250 c€ /kWh',
                     '572,11 €',
                     '20,00 %'],
                    ['Taxe Départementale sur la Conso Finale Electricité',
                     'du 01/03/2018 au 02/04/2018',
                     '25 427 kWh',
                     '0,106 c€ /kWh',
                     '26,95 €',
                     '20,00 %'],
                    ['Taxe Communale sur la Conso Finale Electricité',
                     'du 01/03/2018 au 02/04/2018',
                     '25 427 kWh',
                     '0,213 c€ /kWh',
                     '54,16 €',
                     '20,00 %'],
                    ['Total Hors TVA pour ce site', '1 989,49 €', 'Hors TVA'],
                    ["TVA (identique pour l'ensemble des fournisseurs)",
                     'Assiette', '397,90 €'],
                    ['TVA à 20,00%', '1 989,49 €', '397,90 €'],
                    ['Total TTC pour ce site', '2 387,39 €', 'TTC'],
                ],
                [['Les montants de TVA et le montant TTC par site sont fournis '
                  'à titre d’information. Seuls les montants figurant sur la '
                  'première page font foi.']],
                [
                    ['Données de comptage',
                     'Puissance(s) souscrite(s) (kW ou kVA)'],
                    ['Identifiant de comptage : 000945 Type de compteur : '
                     'Interface Clientèle Emeraude',
                     'Operateur Heures de pointe',
                     '100'],
                    ['Acheminement : Tarif HTA5 à Pointe Fixe Longue '
                     'Utilisation',
                     'Opérateur Heures pleines hiver',
                     '100'],
                    ['Puissance souscrite actuelle (kW ou kVA) : 100',
                     'Opérateur Heures creuses hiver',
                     '100'],
                    ['Changement de saison tarifaire: été du 01/04 au 31/10 et '
                     'hiver du 01/11 au 31/03',
                     'Opérateur Heures pleines été',
                     '100'],
                    ['', 'Opérateur Heures creuses été', '100'],
                ],
            ]
        )

    def test_edf_c1_10080595767_p1(self):
        result = _relayout('edf_c1_10080595767_p1.py')
        self.assertEqual(
            result,
            [
                [['1 / 14']],
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
                [['Electricité']],
            ]
        )

    def test_edf_c1_10036338943_p1(self):
        result = _relayout('edf_c1_10036338943_p1.py')
        self.assertEqual(
            result,
            [
                [['EDF Entreprises', '1 / 24'],
                 ['Direction Commerciale Régionale'],
                 ['TSA 70102'],
                 ['33070 BORDEAUX CEDEX'],
                 ['Relation Client Grandes Entreprises'],
                 ['Du lundi au vendredi de 8h à 18h'],
                 ['Téléphone : 0820 144 007'],
                 ["Coût de l'appel pour les n° en 0820 : 0,118€ TTC/min"],
                 ['e-mail : edfentreprises-sud-ouest-31@edf.fr'],
                 ['N° de tél. dépannage : voir annexe site'],
                 ['Compte commercial : 1-19O'],
                 ['Compte de facturation : 823439']],
                [['FLX03300054700014-07RSDO01'],
                 ['B0NO'],
                 ['99 RUE DU GRAS'],
                 ['31560 NAILLOUX']],
                [['Facture 10036339999 du 02/02/2016'],
                 ['Montant Hors T.V.A. :', '70 790,61'],
                 ['Total T.V.A.', '(payée sur les débits) :', '14 158,12'],
                 ['Total TTC en euros (détails au verso) :', '84 948,73'],
                 ['Compte tenu de la situation de votre compte,'],
                 ["vous serez prélevé d'un montant de :", '84 948,73 €'],
                 ['à partir du :', '17/02/2016'],
                 ['sur le compte :', 'FR ** ***** ***** 00000600'],
                 ["Aucun escompte n'est accordé pour paiement anticipé"]],
                [['Prochaine facture vers le 02/03/2016']],
                [['Maintenant EDF vend du gaz naturel, contactez votre '
                  'conseiller commercial']]

            ]
        )

    def test_edf_c2_10073292263_p1(self):
        result = _relayout('edf_c2_10073292263_p1.py')
        self.assertEqual(
            result,
            [
                [['1 / 30']],
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

    def test_edf_c2_10073292263_p18(self):
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

    def test_edf_c2_10073292263_p30(self):
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

    def test_edf_c2_10067224248_p5(self):
        result = _relayout('edf_c2_10067224248_p5.py')
        self.assertEqual(
            result,
            [
                [['5 / 28']],
                [['Vos références'],
                 ['Compte commercial : 1-2QG'],
                 ['Compte de facturation : 923422']],
                [['Facture 10067229999 du 24/10/2017']],
                [
                    ['Détails de facturation par site (Point de livraison)'],
                    ['Les montants de TVA et le montant TTC par site sont '
                     "fournis à titre d'information. Seuls les montants "
                     'figurant sur le Récapitulatif font foi.'],
                ],
                [
                    ['Référence de votre contrat :',
                     '1-1Y9',
                     'Souscrit depuis le : 21/06/2016',
                     'Venant à échéance le : 31/12/2017'],
                ],
                [
                    ['Contrat Electricité Structuré : Prix non réglementés',
                     'Groupe de sites : C2 5P-SDT']],
                [
                    ['Site : USINE',
                     'Code site :', '1311EP303802277I016'],
                    ['PRODUCTION', 'Groupe :', 'INDUSTRIEL'],
                    ['Réf. Acheminement Electricité : 3000221015'],
                ],
                [["Code d'imputation :"]],
                [['Autre référence :']],
                [['0,05 € /appel']],
                [['Tél. dépannage électricité Enedis : 0 811 010 211']],
                [['Données comptage']],
                [['Évolution de votre consommation en kWh']],
                [
                    ['Identifiant de comptage : 021539003020'],
                    ['Type de compteur : Compteur HTA SAPHIR'],
                    ['Acheminement : Tarif HTA5 à Pointe Fixe '
                     'Longue Utilisation'],
                ],
                [['Pertes Joule : 1,000']],
                [['386536', '385656']],
                [['354100 360055 352780']],
                [['323716']],
                [['296568 298183']],
                [['187295']],
                [['Puissance(s) souscrite(s)']],
                [['Période', 'Puissance contractuelle (kW ou kVA)'],
                 ['Operateur Heures de pointe', '680'],
                 ['Opérateur Heures pleines hiver', '680'],
                 ['Opérateur Heures creuses hiver', '680'],
                 ['Opérateur Heures pleines été', '680'],
                 ['Opérateur Heures creuses été', '680'],
                 ['Puissance souscrite actuelle (kW ou kVA) :', '680']],
                [['96909']],
                [['41600', '36635']],
                [['17827']],
                [['Sept 16 Oct 16 Nov 16 Déc 16',
                  'Jan 17', 'Fév 17 Mar 17', 'Avr 17 Mai 17', 'Juin 17',
                  'Juil 17', 'Aou 17 Sept 17']],
                [["Consommation d'après index de fin mesurés"]],
                [['Index Acheminement relevés (en gras) ou estimés en kWh']],
                [['Période', 'Index de début', 'Index de fin',
                  'Puissance atteinte']],
                [['(kW ou kVA)']],
                [
                    ['Pointe', '22222 le 01/09/2017',
                     '22222 le 30/09/2017', '0'],
                    ['Heures Pleines Hiver', '79756 le 01/09/2017',
                     '79756 le 30/09/2017', '0'],
                    ['Heures Creuses Hiver', '83210 le 01/09/2017',
                     '83210 le 30/09/2017', '0'],
                    ['Heures Pleines Eté', '938818 le 01/09/2017',
                     '1142600 le 30/09/2017', '653'],
                    ['Heures Creuses Eté', '672004 le 01/09/2017',
                     '821002 le 30/09/2017', '608'],
                ],
                [['Index de fin de période relevés (en gras) ou estimés en '
                  'kWh']],
                [['Période', 'Index de début', 'Index de fin']],
                [
                    ['Cadran EA1 : Heures Pleines Hiver - Postes Marché',
                     '62442 le 01/09/2017',
                     '62442 le 30/09/2017'],
                    ['Cadran EA2 : Heures Creuses Hiver - Postes Marché',
                     '122747 le 01/09/2017',
                     '122747 le 30/09/2017'],
                    ['Cadran EA3 : Heures Pleines Eté - Postes Marché',
                     '598020 le 01/09/2017',
                     '723917 le 30/09/2017'],
                    ['Cadran EA4 : Heures Creuses Eté - Postes Marché',
                     '1012802 le 01/09/2017',
                     '1239685 le 30/09/2017']],
                [['Electricité', 'Quantité', 'Prix unitaire Montant HT (€ )']],
                [
                    ['Electricité Heures Pleines Eté',
                     'du 01/09/2017 au 30/09/2017',
                     '125 897 kWh',
                     '4,126 c€ /kWh',
                     '5 194,51'],
                    ['Electricité Heures Creuses Eté',
                     'du 01/09/2017 au 30/09/2017',
                     '226 883 kWh',
                     '2,802 c€ /kWh',
                     '6 357,26'],
                    ['Mécanisme de capacité Heures Pleines Eté',
                     'du 01/09/2017 au 30/09/2017',
                     '125 897 kWh',
                     '0,108 c€ /kWh',
                     '135,97'],
                    ['Mécanisme de capacité Heures Creuses Eté',
                     'du 01/09/2017 au 30/09/2017',
                     '226 883 kWh',
                     '0,108 c€ /kWh',
                     '245,03'],
                    ['Option Energie renouvelable',
                     'du 01/09/2017 au 30/09/2017',
                     '352 780 kWh',
                     '0,030 c€ /kWh',
                     '105,83'],
                ],
                [['Total Electricité (HT)', '12 038,60']],
                [['Total consommations facturées', '352 780 kWh']],
                [
                    ['Utilisation du réseau de distribution électricité et '
                     'prestations techniques',
                     'Montant HT (€ )'],
                ],
                [
                    ['Composante de gestion - Reprise',
                     'du 01/09/2017 au 30/09/2017', '-16,44'],
                    ['Composante de gestion - Echu',
                     'du 01/09/2017 au 30/09/2017',
                     '30.000 c.j',
                     '54.81 c€ /c.j',
                     '16,44'],
                    ['Composante de gestion - Echoir',
                     'du 01/10/2017 au 30/10/2017',
                     '30.000 c.j',
                     '54.81 c€ /c.j',
                     '16,44'],
                    ['Composante de comptage - Reprise',
                     'du 01/09/2017 au 30/09/2017', '-43,93'],
                    ['Composante de comptage - Echu',
                     'du 01/09/2017 au 30/09/2017',
                     '30.000 p.j',
                     '146.43 c€ /p.j',
                     '43,93'],
                    ['Composante de comptage - Echoir',
                     'du 01/10/2017 au 30/10/2017',
                     '30.000 p.j',
                     '146.43 c€ /p.j',
                     '43,93'],
                    ['Composante de soutirage fixe - Reprise',
                     'du 01/09/2017 au 30/09/2017',
                     'PS pondérée',
                     '680 kW',
                     '-887,60'],
                    ['Composante de soutirage fixe - Echu',
                     'du 01/09/2017 au 30/09/2017',
                     '20400.000 kW',
                     '4.35 c€ /kW',
                     '887,60'],
                ],
            ]
        )

    def test_text_block_separation(self):
        result = _relayout('edf_c2_10073292263_p27.py')
        self.assertEqual(
            result,
            [
                # junk lost in the tested part of the page
                [['102 323,26 €', 'HT']],
                [['102 323,26 €', 'Taux de TVA']],
                [['63 775,74 €', '20,00 %'], ['35 759,59 €', '20,00 %']],
                [['1 224,49 €', '20,00 %']],
                [['957,37 €', '20,00 %'], ['606,07 €', '20,00 %']],
                # start desired test
                [
                    ['Utilisation du réseau de distribution et prestations '
                     'techniques (identique pour l’ensemble des fournisseurs)',
                     '44 678,29 €', 'HT'],
                ],
                [['Quantité', 'Prix unitaire HT', 'Taux de TVA']],
                [
                    ['Composante de gestion - Reprise',
                     'du 01/12/2017 au 30/12/2017',
                     '-16,44 €',
                     '20,00 %'],
                    ['Composante de gestion - Echu',
                     'du 01/12/2017 au 31/12/2017',
                     '31.000 c.j',
                     '54.81 c€ /c.j',
                     '16,99 €',
                     '20,00 %'],
                    ['Composante de gestion - Echoir',
                     'du 01/01/2018 au 30/01/2018',
                     '30.000 c.j',
                     '97.55 c€ /c.j',
                     '29,26 €',
                     '20,00 %'],
                    ['Composante de comptage - Reprise',
                     'du 01/12/2017 au 30/12/2017',
                     '-43,93 €',
                     '20,00 %'],
                    ['Composante de comptage - Echu',
                     'du 01/12/2017 au 31/12/2017',
                     '31.000 p.j',
                     '146.43 c€ /p.j',
                     '45,39 €',
                     '20,00 %'],
                    ['Composante de comptage - Echoir',
                     'du 01/01/2018 au 30/01/2018',
                     '30.000 p.j',
                     '146.43 c€ /p.j',
                     '43,93 €',
                     '20,00 %'],
                    ["Composante d'alimentation de secours cellule -",
                     'du 01/12/2017 au 30/12/2017',
                     '-266,03 €',
                     '20,00 %'],
                    ['Reprise'],
                    ["Composante d'alimentation de secours cellule - Echu",
                     'du 01/12/2017 au 31/12/2017',
                     '31.000 u.j',
                     '886.77 c€ /u.j',
                     '274,90 €',
                     '20,00 %'],
                    ["Composante d'alimentation de secours cellule - Echoir",
                     'du 01/01/2018 au 30/01/2018',
                     '30.000 u.j',
                     '886.77 c€ /u.j',
                     '266,03 €',
                     '20,00 %'],
                ],
                # more junk lost in the tested part of the page
                [['-526,20 €', '20,00 %']],
                [['149.854 km.j', '362.85 c€ /km.j', '543,74 €', '20,00 %'],
                 ['145.020 km.j', '362.85 c€ /km.j', '526,20 €', '20,00 %']],
                [['PS pondérée : 5000 kW', '-6 526,50 €', '20,00 %']],
                [['155000.000 kW', '4.35 c€ /kW', '6 744,05 €', '20,00 %'],
                 ['150000.000 kW', '4.35 c€ /kW', '6 526,50 €', '20,00 %']],
                [['280237.000 kWh', '2.77 c€ /kWh', '7 762,56 €', '20,00 %'],
                 ['853554.000 kWh', '2.08 c€ /kWh', '17 753,92 €', '20,00 %'],
                 ['886455.000 kWh', '1.30 c€ /kWh', '11 523,92 €', '20,00 %']],
                [['0,00 €']],
                [['343101kVArh (6h-22h)', '343101 kVArh']],
                [['en franchise']],
                [['0,00 €', 'HT']],
                [['Assiette', 'Taux de TVA']],
                [['INCLUS']],
                [['17 217,14 €', 'Hors TVA']],
                [['Assiette', 'Prix unitaire HorsTVA', 'Taux de TVA']],
                [['2 020 246 kWh', '0,750 c€ /kWh', '15 151,85 €', '20,00 %']],
                [['7 637,89', '27,04 %', '2 065,29 €', '20,00 %']],
            ]
        )

    def test_text_merge1(self):
        result = _relayout('text_merge1.py')
        self.assertEqual(
            result,
            [
                 [["Taxe Communale sur la Consommation Finale "
                   "d'Electricité (TCCFE)"]]
            ]
        )

    def test_text_merge2(self):
        result = _relayout('text_merge2.py')
        self.assertEqual(
            result,
            [
                 [['3 993,99 €', 'Taux de TVA']],
            ]
        )

    def test_euro_fix(self):
        result = _relayout('broken_euro.py')
        self.assertEqual(
            result,
            [
                [['97.41 c€ /c.j']],
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


def load_tests(loader, tests, ignore):
    tests.addTests(
        doctest.DocTestSuite('pdfss',
                             optionflags=doctest.NORMALIZE_WHITESPACE)
    )
    return tests


if __name__ == '__main__':
    unittest.main()
