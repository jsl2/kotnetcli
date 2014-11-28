#!/usr/bin/env python2
# -*- coding: utf-8 -*-

## Dependencies:    python-mechanize, python-keyring, curses
## Author:          Gijs Timmers
## Licence:         CC-BY-SA-4.0
##                  http://creativecommons.org/licenses/by-sa/4.0/

## This work is licensed under the Creative Commons
## Attribution-ShareAlike 4.0 International License. To view a copy of 
## this license, visit http://creativecommons.org/licenses/by-sa/4.0/ or
## send a letter to Creative Commons, PO Box 1866, Mountain View, 
## CA 94042, USA.

import re                               ## Basislib voor reguliere expressies
import time                             ## Voor timeout om venster te sluiten na login etc.
import getpass                          ## Voor invoer wachtwoord zonder feedback
import curses                           ## Voor tekenen op scherm.
import sys                              ## Basislib voor output en besturingssysteemintegratie
import os                               ## Basislib voor besturingssysteemintegratie

class QuietCommunicator():
    def __init__(self):
        self.tekstKleurRood = None
        self.tekstKleurGroen = None
        self.tekstKleurGeel = None
        self.tekstOpmaakVet = None
        self.tekstKleurGeelOpmaakVet = None
        
        
    def kprint(self, pos_y, pos_x, tekst, *args):
        pass

class PlaintextCommunicator():
    pass

class SummaryCommunicator():
    pass

#class CursesCommunicator(QuietCommunicator):
class CursesCommunicator():
    def __init__(self):
        self.scherm = curses.initscr()
        
        curses.curs_set(0)                  ## cursor invisible
        curses.start_color()                ## Kleuren aanmaken
        curses.use_default_colors()
        curses.init_pair(1, 1, -1)          ## Paren aanmaken: ndz vr curses.
        curses.init_pair(2, 2, -1)          ## Ik heb de curses-conventie aangehouden, 1 is dus rood,
        curses.init_pair(3, 3, -1)          ## 2 is groen, 3 is geel.
        
        self.tekstKleurRood = curses.color_pair(1)
        self.tekstKleurGroen = curses.color_pair(2)
        self.tekstKleurGeel = curses.color_pair(3)
        self.tekstOpmaakVet = curses.A_BOLD
        
        self.tekstKleurGeelOpmaakVet = curses.color_pair(3) | curses.A_BOLD
        ## Ingevoegd omdat het moeilijk is om | te parsen.
        
        #self.tekstKleurRood = None
        #self.tekstKleurGroen = None
        #self.tekstKleurGeel = None
        #self.tekstOpmaakVet = None
        

    def kprint(self, pos_y, pos_x, tekst, *args):
        #print args
        if args:
            #print args[0]
            #self.scherm.addstr(0, 0, "SHOW ME THE TEXT", args)
            self.scherm.addstr(pos_y, pos_x, tekst, args[0])
            self.scherm.refresh()
        else:
            self.scherm.addstr(pos_y, pos_x, tekst)
            self.scherm.refresh()
        
