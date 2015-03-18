#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

## Dependencies:    python-mechanize, python-keyring, curses
## Author:          Gijs Timmers: https://github.com/GijsTimmers
## Contributors:    Gijs Timmers: https://github.com/GijsTimmers
##                  Jo Van Bulck: https://github.com/jovanbulck

## Licence:         CC-BY-SA-4.0
##                  http://creativecommons.org/licenses/by-sa/4.0/

## This work is licensed under the Creative Commons
## Attribution-ShareAlike 4.0 International License. To  view a copy of
## this license, visit http://creativecommons.org/licenses/by-sa/4.0/ or
## send a letter to Creative Commons, PO Box 1866, Mountain View,
## CA 94042, USA.

## kotnetcli.py: encapsulates the end-user command line interface. It parses
## the command line arguments to:
##  - create the appropriate credentials instance
##  - create the appropriate communicator instance
##  - create and start the appropriate worker instance

#jo: zijn alle imports hieronder nog nodig?
import subprocess                       ## Om systeemcommando's uit te voeren
import argparse                         ## Parst argumenten
import argcomplete                      ## Argumenten aanvullen met Tab
import platform                         ## Om te kunnen compileren op Windows
import sys                              ## Basislib
import os                               ## Basislib
import getpass                          ## Voor invoer wachtwoord zonder print

from communicator.fabriek import LoginCommunicatorFabriek, LogoutCommunicatorFabriek    ## Voor output op maat

## Gijs: In de toekomst graag vervangen door fabriek

from credentials import KeyRingCredentials, ForgetCredsException    ## Opvragen van nummer en wachtwoord
from worker import LoginWorker, LogoutWorker, EXIT_FAILURE, EXIT_SUCCESS #, ForceerLoginWorker

from tools import log
import logging
logger = logging.getLogger(__name__)

## Hardcode the version. Development versions should be suffixed with -dev;
## release versions should be followed with "Name" as well. Some examples:
## __version__ = '1.2.1 "American Craftsman"'   (A release)
## __version__ = '1.2.1-dev'                    (A development version)
__version__ = '1.3.0-dev'

## An argument parse action that prints license information
## on stdout and exits
class PrintLicenceAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print "This work is licensed under the Creative Commons"
        print "Attribution-ShareAlike 4.0 International License. To  view a copy of"
        print "this license, visit https://creativecommons.org/licenses/by-sa/4.0/ or"
        print "send a letter to Creative Commons, PO Box 1866, Mountain View,"
        print "CA 94042, USA.\n"
        print "Visit the github page (https://github.com/GijsTimmers/kotnetcli) to"
        print "view the full source code and to collaborate on the project."
        exit(0)

def init_debug_level(log_level):
    try:
        log.init_logging(log_level)
    except ValueError:
        print "kotnetcli: Invalid debug level: %s" % log_level
        sys.exit(1)
        
## A class encapsulating the argument parsing behavior
## Note: directly inherit from "object" in order to be able to use super() in child classes
class KotnetCLI(object):
    
    ## Note: create the parser and groups as instance fiels so subclasses can access them
    ##
    ## We create three different groups, whose arguments can't be mixed (using
    ## the add_mutually_exclusive_group() option. If you enter non-combinable
    ## options, you'll get an error. To support grouping in the help messages,
    ## we add them inside an argument_group (as in http://bugs.python.org/issue10680)
    ##
    ## Then, we use "store_true" to allow elif style switching over the groups. Non-true
    ## values can be specified by using "default=False" to get "store_true" semantics.
    ## This avoids the need for complex decision trees.
    ##
    ## Finally, we call argcomplete, so that we can complete flags automatically
    ## when using bash.
    def __init__(self, descr="Script om in- of uit te loggen op KotNet", \
    log_level_default = "warning"):
        epilog_string = "return values:\n  %s\t\t\ton success\n  %s\t\t\ton failure" % (EXIT_SUCCESS, EXIT_FAILURE)
        self.parser = argparse.ArgumentParser(description=descr, epilog=epilog_string, \
            formatter_class=argparse.RawDescriptionHelpFormatter)
        dummygroup = self.parser.add_argument_group("worker options")
        self.workergroep = dummygroup.add_mutually_exclusive_group()
        dummygroup = self.parser.add_argument_group("credentials options")
        self.credentialsgroep = dummygroup.add_mutually_exclusive_group()
        dummygroup = self.parser.add_argument_group("communicator options")
        self.communicatorgroep = dummygroup.add_mutually_exclusive_group()
        self.voegArgumentenToe(log_level_default)
        argcomplete.autocomplete(self.parser)
    
    def voegArgumentenToe(self, log_level_default):
        ########## general flags ##########
        self.parser.add_argument("-v", "--version", action="version", \
        version=__version__)
        self.parser.add_argument("-l", "--license", action=PrintLicenceAction, \
        help="show license info and exit", nargs=0)
        ## debug flag with optional (nargs=?) level; defaults to LOG_LEVEL_DEFAULT if option 
        ## not present; defaults to debug if option present but no level specified
        self.parser.add_argument("--debug", help="specify the debug verbosity", \
        nargs="?", const="debug", metavar="LEVEL",
        choices=[ 'critical', 'error', 'warning', 'info', 'debug' ],
        action="store", default=log_level_default)
        
        ########## login type flags ##########
        self.workergroep.add_argument("-i", "--login",\
        help="Logs you in on KotNet (default)", action="store_true")
        
        self.workergroep.add_argument("-o", "--logout",\
        help="Logs you out off KotNet", action="store_true")
        
        '''
        self.workergroep.add_argument("-!", "--force-login",\
        help="Logs you out on other IP's, and then in on this one",\
        action="store_const", dest="worker", const="force_login")
        '''
        
        ########## credentials type flags ##########
        self.credentialsgroep.add_argument("-k", "--keyring",\
        help="Makes kotnetcli pick up your credentials from the keyring (default)",\
        action="store_true")
        
        self.credentialsgroep.add_argument("-f", "--forget",\
        help="Makes kotnetcli forget your credentials",\
        action="store_true")
        
        self.credentialsgroep.add_argument("-g", "--guest-mode",\
        help="Logs you in as a different user without forgetting your \
        default credentials", action="store_true")
        
        ########## communicator flags ##########
        self.communicatorgroep.add_argument("-t", "--plaintext",\
        help="Logs you in using plaintext output",\
        action="store_true")

        ## nargs=3 to allow a user to supply optional colorname arguments
        ## default=False to get "store_true" semantics when option not specified
        self.communicatorgroep.add_argument("-c", "--color",\
        help="Logs you in using colored text output (default); arguments = ok_color, wait_color, err_color, style",\
        choices= ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "bright", "normal"],
        nargs=4, default=False, metavar="COL")
        
        #self.communicatorgroep.add_argument("-q", "--quiet",\
        #help="Hides all output",\
        #action="store_const", dest="communicator", const="quiet")
                
        ## voorlopig andere communicators uitschakelen in de dev branch
        '''
        """
        communicatorgroep.add_argument("-a", "--android",\
        help="Logs you in using the Android login system",\
        action="store_const", dest="communicator", const="android")
        """
        
        self.communicatorgroep.add_argument("-u", "--curses",\
        help="Logs you in using curses output",\
        action="store_const", dest="communicator", const="curses")
        
        self.communicatorgroep.add_argument("-d", "--dialog",\
        help="Omits the curses interface by using dialog based output",\
        action="store_const", dest="communicator", const="dialog")
        
        self.communicatorgroep.add_argument("-b", "--bubble",\
        help="Hides all output except for a bubble notification",\
        action="store_const", dest="communicator", const="bubble")
        
        self.communicatorgroep.add_argument("-s", "--summary",\
        help="Hides all output except for a short summary",\
        action="store_const", dest="communicator", const="summary")
        
        self.communicatorgroep.add_argument("-q", "--quiet",\
        help="Hides all output",\
        action="store_const", dest="communicator", const="quiet")
        '''
    
    ## Parses the arguments corresponding to self.parser
    def parseArgumenten(self):
        argumenten = self.parser.parse_args()
        ## 0. general flags
        init_debug_level(argumenten.debug)
        logger.debug("parse_args() is: %s", argumenten)
        ## 1. credential-related flags
        creds = self.parseCredentialFlags(argumenten)
        ## 2. login-type flags
        (worker, fabriek) = self.parseActionFlags(argumenten)
        ## 3. communicator-related flags
        co = self.parseCommunicatorFlags(fabriek, argumenten)
        ## 4. start the process
        worker.go(co, creds)

    ## returns newly created credentials obj
    def parseCredentialFlags(self, argumenten):
        logger.info("ik haal de credentials uit de keyring")
        return self.parseCredsFlags(argumenten, KeyRingCredentials())
    
    ## a helper method with a default credentials object argument
    def parseCredsFlags(self, argumenten, cr):
        if argumenten.forget:
            logger.info("ik wil vergeten")
            try:
                cr.forgetCreds()
                print "You have succesfully removed your kotnetcli credentials."
                sys.exit(0)
            except ForgetCredsException:
                print "You have already removed your kotnetcli credentials."
                sys.exit(1)
        
        elif argumenten.guest_mode:
            logger.info("ik wil me anders voordoen dan ik ben")
            (gebruikersnaam, wachtwoord) = self.prompt_user_creds()
            cr.saveGuestCreds(gebruikersnaam, wachtwoord)
            return cr
            
        else:
            ## default option: argumenten.keyring
            if (not cr.hasCreds()):
                (gebruikersnaam, wachtwoord) = self.prompt_user_creds()
                cr.saveCreds(gebruikersnaam, wachtwoord)
            return cr
            
    def prompt_user_creds(self):
        gebruikersnaam = raw_input("Voer uw s-nummer/r-nummer in... ")
        wachtwoord = getpass.getpass(prompt="Voer uw wachtwoord in... ")
        return (gebruikersnaam, wachtwoord)

    ## returns tuple (worker, fabriek)
    def parseActionFlags(self, argumenten):
        if argumenten.logout:
            logger.info("ik wil uitloggen")
            worker = LogoutWorker()
            fabriek = LogoutCommunicatorFabriek()
        else:
            ## default option: argumenten.login
            logger.info("ik wil inloggen")
            worker = LoginWorker()
            fabriek = LoginCommunicatorFabriek()
                
        '''elif argumenten.worker == "force_login":
            print "ik moet en zal inloggen"
            worker = ForceLoginWorker()
            fabriek = LoginCommunicatorFabriek()
        '''
        
        return (worker, fabriek)
    
    ## returns communicator
    def parseCommunicatorFlags(self, fabriek, argumenten):
        #if argumenten.communicator == "quiet":
        #    print "ik wil zwijgen"
        #    return fabriek.createQuietCommunicator()
        
        if argumenten.plaintext:
            logger.info("ik wil terug naar de basis")
            return fabriek.createPlaintextCommunicator()
        
        elif argumenten.color:
            logger.info("ik wil vrolijke custom kleuren: %s", argumenten.color)
            return fabriek.createColoramaCommunicator(argumenten.color)
        
        else:
            ## default option: argumenten.color with default colors
            logger.info("ik ga mee met de stroom")
            return fabriek.createColoramaCommunicator()
        
        '''
        elif argumenten.communicator == "summary":
            print "ik wil het mooie in de kleine dingen zien"
            return fabriek.createSummaryCommunicator()
        
        elif argumenten.communicator == "quiet":
            print "ik wil zwijgen"
            return fabriek.createQuietCommunicator()
        else:
            print "we still have to fix the others...."
        
        if argumenten.communicator == "curses":
            print "ik wil vloeken"
            if os.name == "posix":
                co = communicator.CursesCommunicator()
            else:
                co = communicator.ColoramaCommunicator()
        
        elif argumenten.communicator == "android":
            print "ik wou dat ik een robot was"
            co = communicator.AndroidCommunicator()
        
        elif argumenten.communicator == "colortext":
            print "ik wil vrolijke kleuren"
            ## jo: TODO changed next line in order to be able to test; should use fac here
                    
            fab = fabriek.LoginCommunicatorFabriek()
            co = fab.createColoramaCommunicator()
            ## Moet worden vervangen in de toekomst: fab moet al aangemaakt zijn
            ## door de login/logout-switch.
        
        elif argumenten.communicator == "plaintext":
            print "ik wil terug naar de basis"
            co = communicator.LogoutPlaintextCommunicator()
        
        elif argumenten.communicator == "dialog":
            print "ik wil fancy dialogs"
            if os.name == "posix":
                co = communicator.DialogCommunicator()
            else:
                co = communicator.ColoramaCommunicator()
        
        elif argumenten.communicator == "bubble":
            print "ik wil bellen blazen"
            if os.name == "posix":
                co = communicator.BubbleCommunicator()
            else:
                co = communicator.ColoramaCommunicator()
        
        elif argumenten.communicator == "summary":
            print "ik wil het mooie in de kleine dingen zien"
            co = communicator.SummaryCommunicator()
        
        elif argumenten.communicator == "quiet":
            print "ik wil zwijgen"
            co = communicator.QuietCommunicator()
        '''
## end class KotnetCLI

## Losse main()-functie, zodat setup.py gemakkelijk een executable voor deze
## methode kan aanleggen in /usr/bin.
def main():
    k = KotnetCLI()
    k.parseArgumenten()

## Start de zaak asa deze file rechtstreeks aangeroepen is vanuit
## command line (i.e. niet is geimporteerd vanuit een andere file)
if __name__ == "__main__":
    main()
