from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
import os
from operator import itemgetter


author = 'Jörn Wieber'

doc = """
shows participants pictures of snacks and asks for their willingness-to-pay
"""


class Constants(BaseConstants):
    name_in_url = 'Step1'
    players_per_group = None

    # Anzahl unterschiedlicher Snack-Bilder, basierend auf Dateien im Snackbilder-Ordner
    num_snacks = len(os.listdir('_static//kosfeld_test'))

    # Liste der Snacks, basierend auf .jpg-Dateien im Snackbilder-Ordner
    list_snacks = []
    for snack in os.listdir('_static//kosfeld_test'):
        if snack.endswith('.JPG'):
            snack = snack[:-4]
            list_snacks.append(snack)
        else:
            continue

    # Anzahl an Entscheidungen, die in Step 1 gefällt werden sollen = Anzahl Snacks gesamt
    num_rounds = len(os.listdir('_static//kosfeld_test'))




class Subsession(BaseSubsession):
    def before_session_starts(self):


        if self.round_number == 1:          # damit Schleifen nur 1x durchlaufen werden

            # initialisiere Index-Liste
            # erstelle für jeden Teilnehmer eine Liste mit Indizes für die Snack-Liste
            # diese Liste wird zufällig geordnet -> individuelle Reihenfolge für jeden Teilnehmer
            for p in self.get_players():
                if 'num_snacks' not in p.participant.vars:
                    # Liste für Step 1
                    p.participant.vars['num_snacks'] = (list(range(Constants.num_snacks)))
                    random.shuffle(p.participant.vars['num_snacks'])
                    # Liste für Step 4
                    p.participant.vars['num_snacks_Step4'] = (list(range(Constants.num_snacks)))
                    random.shuffle(p.participant.vars['num_snacks_Step4'])


            # initialisiere BDM-Dictionary
            # erstellt ein zunächst leeres Dictionary, in das nach jeder Bewertung
            # über Player.fill_BDM_dict() ein key-value-Paar eingetragen wird
            # key: Snack
            # value: willingness-to-pay
            for p in self.get_players():
                if 'BDM' not in p.participant.vars:
                    p.participant.vars['BDM'] = {}


class Group(BaseGroup):
    pass



class Player(BasePlayer):
    def unfill_snack_list(self):
        ''' entferne erste Index-Zahl aus Teilnehmer-Snack-Liste
        '''
        self.participant.vars['num_snacks'].pop(0)


    def fill_BDM_dict(self):
        rated_snack = self.slider_value
        # key: abgefragter Snack
        # value: willingness-to-pay
        self.participant.vars['BDM'][Constants.list_snacks[self.participant.vars['num_snacks'][0]]] = self.slider_value


    def sort_WTPs(self):
        '''Differenzen der WTPs minimal halten
        '''
        # konvertiere BDM-dictionary in Liste von Tupel-Paaren: [(snack, WTP), (snack, WTP),...]
        sorted_BDM_tuples = sorted(self.participant.vars['BDM'].items(), key=itemgetter(1))
        # drehe Liste um, damit absteigend nach WTPs geordnet ist
        sorted_BDM_tuples.reverse()
        print('-----------------------sorted_BDM_tuples-------------------------------')
        print(sorted_BDM_tuples)
        BDM_length = len(sorted_BDM_tuples)

        # initialisiere Liste mit den geringsten WTP-Differenzen (wird in nachfolgender Schleife gefüllt)
        closest_WTPs = []


        for index, element in enumerate(sorted_BDM_tuples):
        # ermittelt Differenz zwischen höchster WTP und allen anderen WTPs,
        # geht dann weiter zur zweit-höchsten WTP und ermittelt deren Differenz zu allen niedrigeren WTPs
        # usw.
            if index != BDM_length-1:       # wenn nicht letztes Element der Liste
                i = index + 1
                while i < BDM_length:
                    WTP_difference = round(float(element[1])-float(sorted_BDM_tuples[i][1]), 1)
                    # wenn closest_WTP-Liste noch nicht voll ODER die gerade ermittelte WTP-Differenz niedriger als das Maximum der bereits vorhandenen WTP-Differenzen
                    if len(closest_WTPs) < Constants.num_rounds or max(closest_WTPs, key=itemgetter(2))[2] > WTP_difference:
                        next_element = sorted_BDM_tuples[i][0]
                        i += 1
                        # füge Triple (Snack1, Snack2, WTP-Differenz zwischen Snack1 und Snack2) zu closest_WTP-Liste hinzu
                        closest_WTPs.append((element[0], next_element, WTP_difference))

                        # wenn closest_WTP-Liste voll: entferne größte WTP-Differenz
                        if len(closest_WTPs) > Constants.num_rounds:
                            closest_WTPs.remove(max(closest_WTPs, key=itemgetter(2)))
                    else:
                        break


        # speichere closest_WTP-Liste global in Teilnehmer-Variablen
        self.participant.vars['closest_WTPs'] = closest_WTPs

        print("-----------------------closest WTPs-------------------------------")
        print(self.participant.vars['closest_WTPs'])

        # Liste mit Snacks aus closest WTPs, um später davon die Pfade zu den Bildern zu bestimmen
        snacks_to_show = []
        for i in closest_WTPs:
            snacks_to_show.append(i[0])
            snacks_to_show.append(i[1])

        self.participant.vars["snacks_to_show"] = snacks_to_show

        print("-----------------------snacks_to_show-------------------------------")
        print(snacks_to_show)

        # ordne Snacks neu (zufällig) für Step 3:
        snacks_to_show_3 = list(set(snacks_to_show))
        print(snacks_to_show_3)
        random.shuffle(snacks_to_show_3)
        while len(snacks_to_show_3) < len(snacks_to_show):
            random_snack = random.choice(snacks_to_show_3)
            if random_snack != snacks_to_show_3[-1]:
                snacks_to_show_3.append(random_snack)

        self.participant.vars["snacks_to_show_step3"] = snacks_to_show_3
        print("-----------------------snacks_Step_3-------------------------------")
        print(snacks_to_show_3)



    #### DATA-fields:
    # Kontrollfragen - dem Experimentator wird mit "HILFE" eine falsche Antwort signalisiert
    control_1 = models.CharField(verbose_name="Kotrollfrage 1:", choices=[['ok', 'Ja'], ['HILFE', 'Nein']], widget=widgets.RadioSelect())
    control_2 = models.CharField(verbose_name="Kotrollfrage 2:", choices=[['ok', 'Ja'], ['HILFE', 'Nein']], widget=widgets.RadioSelect())
    control_3 = models.CharField(verbose_name="Kotrollfrage 3:", choices=[['ok', 'Ja'], ['HILFE', 'Nein']], widget=widgets.RadioSelect())
    # was der Teilnehmer mit dem Schieberegler wählt
    slider_value = models.CharField(widget=widgets.SliderInput())
    # welchen Snack der Teilnehmer gerade bewertet
    rated_snack = models.CharField(widget=widgets.HiddenInput(), verbose_name='')
