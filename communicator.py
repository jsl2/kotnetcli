#!/usr/bin/env python2
# -*- coding: utf-8 -*-

## Dependencies:    python-mechanize, python-keyring, curses
## Author:          Gijs Timmers: https://github.com/GijsTimmers
## Contributors:    Gijs Timmers: https://github.com/GijsTimmers
##                  Jo Van Bulck: https://github.com/jovanbulck

## Licence:         CC-BY-SA-4.0
##                  https://creativecommons.org/licenses/by-sa/4.0/

## This work is licensed under the Creative Commons
## Attribution-ShareAlike 4.0 International License. To view a copy of 
## this license, visit https://creativecommons.org/licenses/by-sa/4.0/ or
## send a letter to Creative Commons, PO Box 1866, Mountain View, 
## CA 94042, USA.

import re                               ## Basislib voor reguliere expressies
import time                             ## Voor timeout om venster te sluiten
import sys                              ## Basislib
import os                               ## Basislib
import platform                         ## Om onderscheid Lin/Mac te maken
import cursor                           ## Om cursor te verbergen/tonen

if os.name == "nt":
    try:            
        from colorama import (              ## Voor gekleurde tekst.
            Fore,
            Style,
            init
            )
    except ImportError:
        print "Couldn't import the colorama library."
        pass


if os.name == "posix" and platform.system() == "Darwin": ## Is een Mac
    try:            
        from colorama import (              ## Voor gekleurde tekst.
            Fore,
            Style,
            init
            )
    except ImportError:
        print "Couldn't import the colorama library."
        pass


if os.name == "posix" and platform.system() != "Darwin": ## Is een Linux
    print "Import Linux stuff"

    try:            
        import curses                       ## Voor tekenen op scherm.
    except ImportError:
        print "Couldn't import the curses library."
        pass
    try:            
        import notify2                      ## OS-specifieke notificaties
    except ImportError:
        print "Couldn't import the notify2 library."
        pass
    try:            
        from dialog import Dialog           ## Voor tekenen op scherm.
    except ImportError:
        print "Couldn't import the dialog library."
        pass
    
    try:            
        from colorama import (              ## Voor gekleurde tekst.
            Fore,
            Style,
            init
            )
    except ImportError:
        print "Couldn't import the colorama library."
        pass

class QuietCommunicator():
    ## jo: removed 'uit_te_voeren_procedure' argument, omdat procedure-specific
    ## behavior in de klasse hierarchy komt te zitten
    def __init__(self):
        pass
    
    def eventPingSuccess(self):
        pass
    def eventPingFailure(self):
        pass
    def eventPingAlreadyOnline(self):
        pass

    def eventNetloginStart(self):
        pass
    def eventNetloginSuccess(self):
        pass
    def eventNetloginFailure(self):
        pass
        
    def eventKuleuvenStart(self):
        pass
    def eventKuleuvenSuccess(self):
        pass
    def eventKuleuvenFailure(self):
        pass

    def eventInvoerenStart(self):
        pass
    def eventInvoerenSuccess(self):
        pass
    def eventInvoerenFailure(self):
        pass

    def eventOpsturenStart(self):
        pass
    def eventOpsturenSuccess(self):
        pass
    def eventOpsturenFailure(self):
        pass
        
    def eventLoginGeslaagd(self, downloadpercentage, uploadpercentage):
        pass
    
    ## jo: moet 'error_code=0' hier niet vervangen worden door
    ## gewoon 'error_code'? en ook in de child classes??
    def beeindig_sessie(self, error_code=0):
        pass

## Abstract super class (not intended to directly create), encapsulating 
## things common to a Login- and LogoutSummaryCommunicator
class SuperSummaryCommunicator(QuietCommunicator):
    def eventPingFailure(self):
        print "Niet verbonden met het KU Leuven-netwerk."
    def eventPingAlreadyOnline(self):
        print "U bent al online."

class LoginSummaryCommunicator(SuperSummaryCommunicator):
    def eventLoginGeslaagd(self, downloadpercentage, uploadpercentage):
        print "Download: " + str(downloadpercentage) + "%" + ",",
        print "Upload: " + str(uploadpercentage) + "%"

    def beeindig_sessie(self, error_code=0):
        if error_code == 0:
            print "login succesvol."
        else:
            print "login mislukt."
            sys.exit(error_code)

class LogoutSummaryCommunicator(SuperSummaryCommunicator):
    def beeindig_sessie(self, error_code=0):
        if error_code == 0:
            print "logout succesvol."
        else:
            print "logout mislukt."


class SuperBubbleCommunicator(QuietCommunicator):
    def __init__(self):
        notify2.init("kotnetcli")

    def createAndShowNotification(message, icon):
        n = notify2.Notification("kotnetcli", message, icon)
        n.show()

class LoginBubbleCommunicator(SuperBubbleCommunicator):
    def eventLoginGeslaagd(self, downloadpercentage, uploadpercentage):
        createAndShowNotification( "Download: %s%%, Upload: %s%%" % \
        (downloadpercentage, uploadpercentage), \
        "notification-network-ethernet-connected")
    
    def beeindig_sessie(self, error_code=0):
        if error_code == 0:
            pass
        else:
            createAndShowNotification( "Login mislukt. Errorcode: %s" % \
            (error_code), "notification-network-ethernet-disconnected")

class LogoutBubbleCommunicator(SuperBubbleCommunicator):
    def beeindig_sessie(self, error_code=0):
        if error_code == 0:
            pass
        else:
            createAndShowNotification( "Logout mislukt. Errorcode: %s" % \
            (error_code), "notification-network-ethernet-connected")

## jo: ik zal deze communicator nog opslitsen in een
## super en 2 subklassen als ik tijd heb...
class DialogCommunicator(QuietCommunicator):
    def __init__(self, uit_te_voeren_procedure):
        
        # some constant definitions to avoid using magic numbers
        # for the DialogCommunicator mixedgauge dialog
        self.WAIT        = 7
        self.DONE        = 0
        self.FAIL        = 1
        
        self.d = Dialog(dialog="dialog")
        self.d.set_background_title("kotnetcli")
        self.netlogin = self.WAIT
        self.kuleuven = self.WAIT
        self.invoeren = self.WAIT
        self.opsturen = self.WAIT
        self.download = self.WAIT
        self.upload = self.WAIT
        self.overal = 0
        self.update()
    
    def update(self):
        self.d.mixedgauge("",
            title="kotnetcli",
            percent= self.overal,
            elements= [ ("Netlogin openen", self.netlogin),
                        ("KU Leuven kiezen", self.kuleuven),
                        ("Gegevens invoeren", self.invoeren),
                        ("Gegevens opsturen", self.opsturen),                                   
                        ("", ""),
                        ("Download", self.download),
                        ("Upload", self.upload)
                      ])
    
    def eventPingFailure(self):
        self.d.infobox("Niet verbonden met het KU Leuven-netwerk.", 5, 30)
    def eventPingAlreadyOnline(self):
        self.d.infobox("U bent al online.", 5, 30)
    
    def eventNetloginSuccess(self):
        self.netlogin = self.DONE
        self.overal = 40
        self.update()
    def eventNetloginFailure(self):
        self.netlogin = self.FAIL
        self.overal = 40
        self.update()
    
    def eventKuleuvenSuccess(self):
        self.kuleuven = self.DONE
        self.overal = 60        
        self.update()
    def eventKuleuvenFailure(self):
        self.kuleuven = self.FAIL
        self.overal = 60        
        self.update()
    
    def eventInvoerenSuccess(self):
        self.invoeren = self.DONE
        self.overal = 80
        self.update()
    def eventInvoerenFailure(self):
        self.invoeren = self.FAIL
        self.overal = 80        
        self.update()

    def eventOpsturenSuccess(self):
        self.opsturen = self.DONE 
        self.overal = 100        
        self.update()
    def eventOpsturenFailure(self):
        self.opsturen = self.FAIL
        self.overal = 100        
        self.update()
    
    def eventLoginGeslaagd(self, downloadpercentage, uploadpercentage):
        self.download = -downloadpercentage
        self.upload = -uploadpercentage
        self.overal = 100
        self.update()
        
    def beeindig_sessie(self, uitgevoerde_procedure=None, error_code=0):
        print "" # print newline to clean prompt under dialog


class SuperPlaintextCommunicator(QuietCommunicator):
    def __init__(self):
        cursor.hide()

    ## Encapsulates the printing of an error string on stderr
    ## Override this method to change the appearance of the printed string.
    def printerr(self, msg):
        sys.stderr.write(msg),
        sys.stderr.flush()

    ## Encapsulates the printing of a "text" string on stdout, *without* a trailing newline
    ## Override this method to change the appearance of the printed string.
    def print_txt(self, msg):
        sys.stdout.write(msg)

    ## Encapsulates the printing of a "wait" event on stdout
    ## Override this method to change the appearance of the printed string.
    def print_wait(self, msg):
        print msg + "[WAIT]" + "\b\b\b\b\b\b\b",
        sys.stdout.flush()

    ## Encapsulates the printing of a "succes" string on stdout
    ## Override this method to change the appearance of the printed string.
    def print_success(self):
        print "[ OK ]"

    ## Encapsulates the printing of a "done" string on stdout
    ## Override this method to change the appearance of the printed string.
    def print_done(self):
        print "[ DONE ]"

    ## Encapsulates the printing of a "fail" string on stdout
    ## Override this method to change the appearance of the printed string.
    def print_fail(self):
        print "[ FAIL ]"

    ## generic print_balk method (not meant to be overriden)
    def print_generic_balk(self, percentage, style, color, stop_color, stop_style):
        balkgetal = int(round(float(percentage) / 10.0))
        print style + "[" + color + \
        "=" * balkgetal + stop_color + \
        " " * (10-balkgetal) +\
        "] [" + \
        " " * (3 - len(str(percentage))) +\
        color + str(percentage) + "%" + \
        stop_color + "]" + stop_style

    ## Encapsulates the printing of a "balk" string on stdout
    ## Override this method to change the appearance of the printed string.
    def print_balk(self, percentage):
        self.print_generic_balk(percentage, "", "", "", "")
    
    def eventPingFailure(self):
        self.printerr("Niet verbonden met het KU Leuven-netwerk.")
        
    def eventPingAlreadyOnline(self):
        self.printerr("U bent al online.")
    
class LoginPlaintextCommunicator(SuperPlaintextCommunicator):     
    def eventNetloginStart(self):
        self.print_wait("Netlogin openen....... ")
    def eventNetloginSuccess(self):
        self.print_success()
    def eventNetloginFailure(self):
        self.print_fail()
        
    def eventKuleuvenStart(self):
        self.print_wait("KU Leuven kiezen...... ")
    def eventKuleuvenSuccess(self):
        self.print_success()
    def eventKuleuvenFailure(self):
        self.print_fail()

    def eventInvoerenStart(self):
        self.print_wait("Gegevens invoeren..... ")
    def eventInvoerenSuccess(self):
        self.print_success()
    def eventInvoerenFailure(self):
        self.print_fail()

    def eventOpsturenStart(self):
        self.print_wait("Gegevens opsturen..... ")
    def eventOpsturenSuccess(self):
        self.print_success()
    def eventOpsturenFailure(self):
        self.print_fail()

    def eventLoginGeslaagd(self, downloadpercentage, uploadpercentage):
        self.print_txt("Download:  ")
        self.print_balk(downloadpercentage)
        self.print_txt("Upload:    ")
        self.print_balk(uploadpercentage)
        
    def beeindig_sessie(self, error_code=0):
        self.print_txt("Inloggen............. "),
        if error_code == 0:
            self.print_done()
        else:
            self.print_fail()
        cursor.show()

class LogoutPlaintextCommunicator(SuperPlaintextCommunicator):     
    def beeindig_sessie(self, error_code=0):
        self.print_txt("Uitloggen............. "),
        if error_code == 0:
            self.print_success()
        else:
            self.print_fail()
        cursor.show()

class SuperColoramaCommunicator(LoginPlaintextCommunicator):
    def __init__(self):
        from colorama import (                  ## Om de tekst kleur te geven
            Fore,                               ## 
            Style,                              ## 
            init as colorama_init)              ## 
        colorama_init()
        cursor.hide()
        self.init_colors()
    
    ## any communicator wanting to customize the colors can override
    ## this method to define new colors and styles
    ## TODO: evt custom perentage style
    def init_colors(self):
        self.ERR_COLOR = Fore.RED
        self.ERR_STYLE = Style.BRIGHT
        self.WAIT_STYLE = Style.BRIGHT
        self.WAIT_COLOR = Fore.YELLOW
        self.SUCCESS_STYLE = Style.BRIGHT
        self.SUCCESS_COLOR = Fore.GREEN
        self.FAIL_STYLE = Style.BRIGHT
        self.FAIL_COLOR = Fore.RED
        self.PERC_STYLE = Style.BRIGHT
        self.CRITICAL_PERC_COLOR = Fore.RED
        self.LOW_PERC_COLOR = Fore.YELLOW
        self.OK_PERC_COLOR = Fore.GREEN

    ## Overrides the printing of an error string on stderr
    def printerr(self, msg):
        sys.stderr.write(self.ERR_STYLE + self.ERR_COLOR + \
        msg + Style.RESET_ALL),
        sys.stderr.flush()

    ## Overrides the printing of a "wait" event on stdout
    def print_wait(self, msg):
        print msg + self.WAIT_STYLE + "[" + self.WAIT_COLOR + \
        "WAIT" + Fore.RESET + "]" + Style.RESET_ALL + "\b\b\b\b\b\b\b",
        sys.stdout.flush()

    ## Overrides the printing of a "succes" string on stdout
    def print_success(self):
        print self.SUCCESS_STYLE + "[" + self.SUCCESS_COLOR + " OK " + \
        Fore.RESET + "]" + Style.RESET_ALL

    ## Overrides the printing of a "done" string on stdout
    def print_done(self):
        print self.SUCCESS_STYLE + "[" + self.SUCCESS_COLOR + " DONE " + \
        Fore.RESET + "]" + Style.RESET_ALL

    ## Overrides the printing of a "fail" string on stdout
    def print_fail(self):
        print self.FAIL_STYLE + "[" + self.FAIL_COLOR + "FAIL" + \
        Fore.RESET + "]" + Style.RESET_ALL

    ## Overrides the printing of a "balk" string on stdout
    def print_balk(self, percentage):
        if percentage <= 10:
            voorwaardelijke_kleur = self.CRITICAL_PERC_COLOR
        elif 10 < percentage < 60:
            voorwaardelijke_kleur = self.LOW_PERC_COLOR
        else:
            voorwaardelijke_kleur = self.OK_PERC_COLOR
        
        self.print_generic_balk(percentage, self.PERC_STYLE,
        voorwaardelijke_kleur, Fore.RESET, Style.RESET_ALL)

class LoginColoramaCommunicator(SuperColoramaCommunicator):
    pass

class LogoutColoramaCommunicator(SuperColoramaCommunicator):
    pass
    
class SuperCursesCommunicator(QuietCommunicator):
    def __init__(self):
        self.scherm = curses.initscr()
        
        
        curses.curs_set(0)                  ## cursor invisible
        curses.start_color()                ## Kleuren aanmaken
        curses.use_default_colors()
        curses.init_pair(1, 1, -1)          ## Paren aanmaken: ndz vr curses.
        curses.init_pair(2, 2, -1)          ## Ik heb de curses-conventie
        curses.init_pair(3, 3, -1)          ## aangehouden, 1 is dus rood,
                                            ## 2 is groen, 3 is geel.
        
        self.tekstKleurRood = curses.color_pair(1)
        self.tekstKleurGroen = curses.color_pair(2)
        self.tekstKleurGeel = curses.color_pair(3)
        self.tekstOpmaakVet = curses.A_BOLD
        
        self.tekstKleurRoodOpmaakVet = curses.color_pair(1) | curses.A_BOLD
        self.tekstKleurGroenOpmaakVet = curses.color_pair(2) | curses.A_BOLD
        self.tekstKleurGeelOpmaakVet = curses.color_pair(3) | curses.A_BOLD
        

        """
        elif uit_te_voeren_procedure == "loguit":
            self.scherm.addstr(6, 0, "Uitloggen.............")
        elif uit_te_voeren_procedure == "forceer_login":
            self.scherm.addstr(6, 0, "Geforceerd inloggen...")
        """
        
    def kprint(self, pos_y, pos_x, tekst, *args):
        if args:
            self.scherm.addstr(pos_y, pos_x, tekst, args[0])
            self.scherm.refresh()
        else:
            self.scherm.addstr(pos_y, pos_x, tekst)
            self.scherm.refresh()
    
    def eventPingSuccess(self):
        pass
    
    def eventPingFailure(self):
        self.kprint(6, 0, "Niet verbonden met het KU Leuven-netwerk.", \
        self.tekstKleurRoodOpmaakVet)
    def eventPingAlreadyOnline(self):
        self.kprint(6, 0, "U bent al online.", \
        self.tekstKleurGeelOpmaakVet)

class LoginCursesCommunicator(SuperCursesCommunicator):
    def __init__(self):
        SuperCursesCommunicator.__init__(self)
        ## We hebben hier het probleem dat we twee __init__s nodig hebben:
        ## we kunnen namelijk niet alles in de superklasse-init zetten.
        ## Want dan zouden we ook bijvoorbeeld Download: en Upload: daar al
        ## moeten plaatsen.
        ## Een elegante oplossing is het gebruiken van een extra init hier.
        ## Gewoonlijk zou dat de __init__ van de superklasse overschrijven,
        ## daarom roepen we deze nog eens expliciet aan.
        
        self.scherm.addstr(0, 0, "Netlogin openen.......")
        self.scherm.addstr(0, 22, "[    ]", self.tekstOpmaakVet)
        self.scherm.addstr(1, 0, "KU Leuven kiezen......")
        self.scherm.addstr(1, 22, "[    ]", self.tekstOpmaakVet)
        self.scherm.addstr(2, 0, "Gegevens invoeren.....")
        self.scherm.addstr(2, 22, "[    ]", self.tekstOpmaakVet)
        self.scherm.addstr(3, 0, "Gegevens opsturen.....")
        self.scherm.addstr(3, 22, "[    ]", self.tekstOpmaakVet)
        self.scherm.addstr(4, 0, "Download:")
        self.scherm.addstr(4, 10, "[          ][    ]", self.tekstOpmaakVet)
        self.scherm.addstr(5, 0, "Upload:")
        self.scherm.addstr(5, 10, "[          ][    ]", self.tekstOpmaakVet)
        self.scherm.addstr(6, 0, "Inloggen..............")
        
        self.scherm.refresh()
        
    def eventNetloginStart(self):
        self.kprint(0, 23, "WAIT", self.tekstKleurGeelOpmaakVet)
    def eventNetloginSuccess(self):
        self.kprint(0, 23, " OK ", self.tekstKleurGroenOpmaakVet)
    def eventNetloginFailure(self):
        self.kprint(0, 23, "FAIL", self.tekstKleurRoodOpmaakVet)
        
    def eventKuleuvenStart(self):
        self.kprint(1, 23, "WAIT", self.tekstKleurGeelOpmaakVet)
    def eventKuleuvenSuccess(self):
        self.kprint(1, 23, " OK ", self.tekstKleurGroenOpmaakVet)
    def eventKuleuvenFailure(self):
        self.kprint(1, 23, "FAIL", self.tekstKleurRoodOpmaakVet)

    def eventInvoerenStart(self):
        self.kprint(2, 23, "WAIT", self.tekstKleurGeelOpmaakVet)
    def eventInvoerenSuccess(self):
        self.kprint(2, 23, " OK ", self.tekstKleurGroenOpmaakVet)
    def eventInvoerenFailure(self):
        self.kprint(2, 23, "FAIL", self.tekstKleurRoodOpmaakVet)

    def eventOpsturenStart(self):
        self.kprint(3, 23, "WAIT", self.tekstKleurGeelOpmaakVet)
    def eventOpsturenSuccess(self):
        self.kprint(3, 23, " OK ", self.tekstKleurGroenOpmaakVet)
    def eventOpsturenFailure(self):
        self.kprint(3, 23, "FAIL", self.tekstKleurRoodOpmaakVet)
    
    def eventLoginGeslaagd(self, downloadpercentage, uploadpercentage):
        balkgetal_download = int(round(float(downloadpercentage) / 10.0))
        
        if downloadpercentage <= 10:
            voorwaardelijke_kleur_download = \
            self.tekstKleurRoodOpmaakVet
        elif 10 < downloadpercentage < 60:
            voorwaardelijke_kleur_download = \
            self.tekstKleurGeelOpmaakVet
        else:
            voorwaardelijke_kleur_download = \
            self.tekstKleurGroenOpmaakVet
            
        self.kprint(4, 23, " " * (3 - len(str(downloadpercentage))) + \
        str(downloadpercentage) + \
        "%", voorwaardelijke_kleur_download)
        
        self.kprint(4, 11, "=" * balkgetal_download + \
        " " * (10-balkgetal_download), voorwaardelijke_kleur_download)
    
        balkgetal_upload = \
        int(round(float(uploadpercentage) / 10.0))
        
        if uploadpercentage <= 10:
            voorwaardelijke_kleur_upload = \
            self.tekstKleurRoodOpmaakVet
        elif 10 < uploadpercentage < 60:
            voorwaardelijke_kleur_upload = \
            self.tekstKleurGeelOpmaakVet
        else:
            voorwaardelijke_kleur_upload = \
            self.tekstKleurGroenOpmaakVet
        
        self.kprint(5, 23, " " * (3 - len(str(uploadpercentage))) + \
        str(uploadpercentage) + \
        "%", voorwaardelijke_kleur_upload)
    
        self.kprint(5, 11, "=" * balkgetal_upload + \
        " " * (10-balkgetal_upload), voorwaardelijke_kleur_upload)
        
    def beeindig_sessie(self, error_code=0):
        if error_code == 0:
            self.kprint(6, 23, "DONE", self.tekstKleurGroenOpmaakVet)
        elif error_code != 0:
            self.kprint(6, 23, "FAIL", self.tekstKleurRoodOpmaakVet)
        
        time.sleep(2)
        
        curses.nocbreak()
        self.scherm.keypad(0)
        curses.echo()
        curses.endwin()

class LogoutCursesCommunicator(SuperCursesCommunicator):
    def __init__(self):
        SuperCursesCommunicator.__init__(self)
        ## We hebben hier het probleem dat we twee __init__s nodig hebben:
        ## we kunnen namelijk niet alles in de superklasse-init zetten.
        ## Want dan zouden we ook bijvoorbeeld Download: en Upload: daar al
        ## moeten plaatsen.
        ## Een elegante oplossing is het gebruiken van een extra init hier.
        ## Gewoonlijk zou dat de __init__ van de superklasse overschrijven,
        ## daarom roepen we deze nog eens expliciet aan.
        
        self.scherm.addstr(0, 0, "Formulier openen......")
        self.scherm.addstr(0, 22, "[    ]", self.tekstOpmaakVet)
        #self.scherm.addstr(1, 0, "IP-adres invoeren......")
        #self.scherm.addstr(1, 22, "[    ]", self.tekstOpmaakVet)
        self.scherm.addstr(2, 0, "Gegevens invoeren.....")
        self.scherm.addstr(2, 22, "[    ]", self.tekstOpmaakVet)
        self.scherm.addstr(3, 0, "Gegevens opsturen.....")
        self.scherm.addstr(3, 22, "[    ]", self.tekstOpmaakVet)
        #self.scherm.addstr(4, 0, "Download:")
        #self.scherm.addstr(4, 10, "[          ][    ]", self.tekstOpmaakVet)
        #self.scherm.addstr(5, 0, "Upload:")
        #self.scherm.addstr(5, 10, "[          ][    ]", self.tekstOpmaakVet)
        self.scherm.addstr(4, 0, "Uitloggen.............")
        
        self.scherm.refresh()
        
    def eventNetloginStart(self):
        self.kprint(0, 23, "WAIT", self.tekstKleurGeelOpmaakVet)
    def eventNetloginSuccess(self):
        self.kprint(0, 23, " OK ", self.tekstKleurGroenOpmaakVet)
    def eventNetloginFailure(self):
        self.kprint(0, 23, "FAIL", self.tekstKleurRoodOpmaakVet)
    
    def eventInvoerenStart(self):
        self.kprint(2, 23, "WAIT", self.tekstKleurGeelOpmaakVet)
    def eventInvoerenSuccess(self):
        self.kprint(2, 23, " OK ", self.tekstKleurGroenOpmaakVet)
    def eventInvoerenFailure(self):
        self.kprint(2, 23, "FAIL", self.tekstKleurRoodOpmaakVet)

    def eventOpsturenStart(self):
        self.kprint(3, 23, "WAIT", self.tekstKleurGeelOpmaakVet)
    def eventOpsturenSuccess(self):
        self.kprint(3, 23, " OK ", self.tekstKleurGroenOpmaakVet)
    def eventOpsturenFailure(self):
        self.kprint(3, 23, "FAIL", self.tekstKleurRoodOpmaakVet)
        
    def beeindig_sessie(self, error_code=0):
        if error_code == 0:
            self.kprint(4, 23, "DONE", self.tekstKleurGroenOpmaakVet)
        elif error_code != 0:
            self.kprint(4, 23, "FAIL", self.tekstKleurRoodOpmaakVet)
        
        time.sleep(2)
        
        curses.nocbreak()
        self.scherm.keypad(0)
        curses.echo()
        curses.endwin()

## The abstract factory specifying the interface and maybe returning 
## some defaults (or just passing)
class SuperCommunicatorFabriek:
   def createSummaryCommunicator():
     pass

class LoginCommunicatorFabriek(SuperCommunicatorFabriek):
    def createSummaryCommunicator():
        LoginSummaryCommunicator()

class LogoutCommunicatorFabriek(SuperCommunicatorFabriek):
    def createSummaryCommunicator():
        LogoutSummaryCommunicator()
