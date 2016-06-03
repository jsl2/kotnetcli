#!/usr/bin/env python2
# -*- coding: utf-8 -*-

## Dependencies:    python-mechanize, python-keyring, curses
## Author:          Gijs Timmers: https://github.com/GijsTimmers
## Contributors:    Gijs Timmers: https://github.com/GijsTimmers
##                  Jo Van Bulck: https://github.com/jovanbulck
##
## Licence:         GPLv3
##
## kotnetcli is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## kotnetcli is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with kotnetcli.  If not, see <http://www.gnu.org/licenses/>.

## worker.py: directs the login/logout process:
##  - receives a 'black box' credentials and communicator instance
##  - uses the KotnetBrowser interface to do the actual actions one
##    after the other, in the correct order
##  - sends status updates to the communicator
##  - exits with the corresponding exit code

import sys                              ## Basislib

from .credentials import ForgetCredsException
from .browser import *
import traceback

import logging
logger = logging.getLogger(__name__)

EXIT_FAILURE = 1 ## Tijdelijke exitcode, moet nog worden geïmplementeerd.
EXIT_SUCCESS = 0

class AbstractWorker(object):
    def go(self, co, creds):
        try:
            logger.debug("Enter worker.go()")
            self.do_work(co, creds)
            logger.debug("Exiting worker with success")
            sys.exit(EXIT_SUCCESS)
        ## fail gracefully when encountering an unexpected error
        except Exception:
            logger.debug("Caught worker exception; exiting with failure")
            co.eventFailureInternalError(traceback)
            sys.exit(EXIT_FAILURE)

class ForgetCredsWorker(AbstractWorker):
    def do_work(self, co, creds):
        try:
            co.eventForgetCreds()
            creds.forgetCreds()
            co.eventForgetCredsSuccess()
        except ForgetCredsException:
            co.eventFailureForget()
            sys.exit(EXIT_FAILURE)

class SuperNetWorker(AbstractWorker):
    def __init__(self):
        self.browser = KotnetBrowser()
    
    def check_credentials(self, co, creds):
        if not creds.hasCreds():
            logger.info("querying for user credentials")
            try:
                (username, pwd, inst) = co.promptCredentials()
            except Exception:
                logger.debug("communicator prompt exception; exiting with failure")
                sys.exit(EXIT_FAILURE)
            creds.storeCreds(username, pwd, inst)
        logger.debug("got creds for user %s@%s", creds.getUser(), creds.getInst())
    
    def check_kotnet(self, co):
        co.eventCheckNetworkConnection()
        try:
            self.browser.check_connection()
        except KotnetOfflineException:
            co.eventFailureOffline(self.browser.get_server_url())
            sys.exit(EXIT_FAILURE)

## A worker class that either succesfully logs you in to kotnet
## or exits with failure, reporting events to the given communicator
class LoginWorker(SuperNetWorker):
    def do_work(self, co, creds):
        self.check_credentials(co,creds)
        self.check_kotnet(co)
        self.login_gegevensinvoeren(co, creds)
        self.login_gegevensopsturen(co, creds)
        self.login_resultaten(co)
        
    def login_gegevensinvoeren(self, co, creds):
        co.eventGetData()
        try:
            self.browser.login_get_request(creds)
        except KotnetOfflineException:
            co.eventFailureOffline(self.browser.get_server_url())
            sys.exit(EXIT_FAILURE)

    def login_gegevensopsturen(self, co, creds):
        co.eventPostData()
        try:
            self.browser.login_post_request(creds)
        except KotnetOfflineException:
            co.eventFailureOffline(self.browser.get_server_url())
            sys.exit(EXIT_FAILURE)

    def login_resultaten(self, co):
        co.eventProcessData()
        try:
            tup = self.browser.login_parse_results()
            co.eventLoginSuccess(tup[0], tup[1])
        except WrongCredentialsException:
            co.eventFailureCredentials()
            sys.exit(EXIT_FAILURE)
        except MaxNumberIPException:
            co.eventFailureMaxIP()
            sys.exit(EXIT_FAILURE)
        except InvalidInstitutionException, e:
            co.eventFailureInstitution(e.get_inst())
            sys.exit(EXIT_FAILURE)
        except InternalScriptErrorException:
            co.eventFailureServerScriptError()
            sys.exit(EXIT_FAILURE)
        except UnknownRCException, e:
            (rccode, html) = e.get_info()
            co.eventFailureUnknownRC(rccode, html)
            sys.exit(EXIT_FAILURE)

class DummyLoginWorker(LoginWorker):
    def __init__(self, inst="kuleuven", dummy_timeout=0.1, kotnet_online=True, netlogin_unavailable=False, \
        rccode=RC_LOGIN_SUCCESS, downl=44, upl=85):
        self.browser = DummyBrowser(inst, dummy_timeout, kotnet_online, netlogin_unavailable, rccode, downl, upl)
