#!/usr/bin/python

###################################################
#  Alexa - skill Lisa Xiaomi vaccum cleaner
#
#  based on flask_ask
#
#   History
#   26-04-17    0.2 first running Alexa-Skill with start,stop,pause,home
#   10.04-17    0.1 initial
#
#
# Copyright 2017 Lunax
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###################################################

import logging
import os
import subprocess
from random import randint
from flask import Flask, render_template
from flask_ask import Ask, statement, request, question, session, version

ROBOT_NAME = "Lisa"

app = Flask(__name__)
ask = Ask(app, "/")
log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("alexa_skill").setLevel(logging.DEBUG)


#
# Alexa commands which can be used
COMMANDS = {}
COMMANDS['ON'] = {"START":'SAUGEN | REINIGEN | STAUBSAUGEN | REINIGUNG'}
COMMANDS['OFF'] = {"STOP":'BEENDEN | FERTIG | AUFHOEREN | STOPPE | BEENDE'}
COMMANDS['POWER'] = {"POWERA":'FLUESTERN | LEISE | MINIMAL | SCHWACH | WENIG'}
COMMANDS['HOME'] = {"HOME":'LADESTATION | BASISSTATION | LADEN'}
COMMANDS['FIND'] = {"FIND":'SAUGEN | REINIGEN | STAUBSAUGEN | REINIGUNG'}

#
# real Xiaomi commands which are used in external script
#
XIAOMI_COMMANDS = {}
XIAOMI_COMMANDS['START'] = 'start'
XIAOMI_COMMANDS['STOP'] = 'stop'
XIAOMI_COMMANDS['CHARGE'] = 'charge'
XIAOMI_COMMANDS['FIND'] = 'find'
XIAOMI_COMMANDS['HOME'] = 'home'
XIAOMI_COMMANDS['POWER'] = 'power'
XIAOMI_COMMANDS['STATUS'] = 'status'

@ask.launch
def new_xiaomi_cleaner_session():
    welcome_text = render_template('welcome',robot_name=ROBOT_NAME)
    help_text = render_template('help')
    return question(welcome_text).reprompt(help_text)

##### intent decorators ############################
def constrain(v, min_value, max_value):
    if v < min_value:
        return min_value, 1
    elif v > max_value:
        return max_value, 2
    return v, 0

def _command_msg(cmd, pwr=60):
    rc = 0
    msg = 'unknown'
    if cmd == 'on':
        msg = ""
        pwr0, rc = constrain(int(pwr),10,100)
        log.info("{} {} {}".format(pwr, pwr0, rc))
        if rc == 1:
            msg = render_template('value_min', power = pwr, value=10)
        elif rc >= 2:
            msg = render_template('value_max', power = pwr, value=100)
        #
        # general message - concatinate
        msg = msg + render_template('start', power = pwr0)
    elif cmd == 'off':
        msg = ""
        msg = render_template('stop')
    elif cmd == 'pause':
        msg = ""
        msg = render_template('pause')
    elif cmd == 'home':
        msg = ""
        msg = render_template('home')
    elif cmd == 'bye':
        msg = ""
        msg = render_template('bye')
    else:
        msg = render_template(msg)
        rc = 1
    return msg, rc

@ask.intent('cleanerON',
    default={'on':'saugen', 'power':60}
)
def cmd_on(on,power):
    follow = render_template('follow')
    log.info("====> cmd_on {} {}".format(on,power))
    msg = None
    #msg, rc = _xiaomi_robot(on,power)
    #
    # if we got no error message, create a success message
    if msg == None:
        msg,rc = _command_msg('on',power)
        log.info("render message {}".format(msg))
    if rc == 1:
        return question(msg).reprompt(follow)

    return statement(msg)

@ask.intent('AMAZON.StopIntent')
@ask.intent('cleanerOFF',
    default={'off':'stop'}
)
def cmd_off(off):
    follow = render_template('yesno')
    msg, rc = _command_msg('off')
    log.info("cmd_off: {}".format(msg))
    return question(msg).reprompt(follow)

@ask.intent('AMAZON.YesIntent')
def cmd_home1():
    msg,rc = _command_msg('home')
    log.info("cmd_home: {}".format(msg))
    #
    # TODO xiaomi_robot -cmd "home"
    #
    return statement(msg)

@ask.intent('AMAZON.NoIntent')
def cmd_off1():
    msg,rc = _command_msg('bye')
    log.info("cmd_off1: {}".format(msg))
    #
    # TODO xiaomi_robot -cmd "pause"
    #
    return statement(msg)

@ask.intent('AMAZON.CancelIntent')
@ask.intent('cleanerPAUSE',
    default={'pause':'pause'}
)
def cmd_pause0(v):
    msg, rc = _command_msg('pause')
    log.info("cmd_pause0: {}".format(msg))
    return statement(msg)


######### session decorators ##################
@ask.on_session_started
def new_session():
    logging.info('new session started')
    log.info("Request ID: {}".format(request.requestId))
    log.info("Request Type: {}".format(request.type))
    log.info("Request Timestamp: {}".format(request.timestamp))
    log.info("Session New?: {}".format(session.new))
    log.info("User ID: {}".format(session.user.userId))
    log.info("Alexa Version: {}".format(version))

@ask.session_ended
def session_ended():
    return "", 200


######### private #############################
def _xiaomi_robot(cmd1, cmd2=None):
    xiaomi = None     # default
    msg = None
    rc = 0
    found = False
    print "===> alexa commands: CMD1:{} - CMD2:{}".format(cmd1, cmd2)
    if cmd1 == None:
        return None,0
    # ON;OFF;POWER;...
    for k1 in COMMANDS.keys():
        print "(1.0) Search in COMMAND keys => {} => {}".format(k1,COMMANDS[k1].keys())
        for k2 in COMMANDS[k1].keys():
            # START;STOP;POWERA;POWERB;...
            print "(1.1) Search in COMMAND[{}] following commands [{}]".format(k2,COMMANDS[k1][k2])
            if cmd1.upper() in COMMANDS[k1][k2]:
                xiaomi = XIAOMI_COMMANDS[k2]
                print "(1.2) Search in XIAOMI_COMMANDS[{}] => found {}".format(k2, XIAOMI_COMMANDS[k2])
                found = True
            else:
                print "(1.x) Xiaomi command not found. Set to stop"
                xiaomi = "stop"
                found = False
            if found:
                break
        if found:
            break

    #
    # if second alexa-command was set, search real XIAOMI command
    # if second command can't converted into a xiaomi command than ignore
    # this alexa command
    #
    if (cmd2 != None and found):
        found = False
        for k1 in COMMANDS.keys():
            print "(2.0) Search in COMMAND keys => {} => {}".format(k1,COMMANDS[k1].keys())
            for k2 in COMMANDS[k1].keys():
                # START;STOP;POWERA;POWERB;...
                print "(2.1) Search in COMMAND[{}] following commands [{}]".format(k2,COMMANDS[k1][k2])
                if cmd2.upper() in COMMANDS[k1][k2]:
                    #
                    # several commands must be separated by blank
                    xiaomi = xiaomi + " " + XIAOMI_COMMANDS[k2]
                    print "(2.2) Search in XIAOMI_COMMANDS[{}] => found {}".format(k2, XIAOMI_COMMANDS[k2])
                    found = True
                if found:
                    break
            if found:
                break

    #
    # avoid general xiaomi command error
    if xiaomi == None:
        # Error X001
        msg = render_template('error1',cmd1=cmd1.upper(),cmd2=cmd2.upper())
    else:
        #
        # Attention put job into background => &
        path = "/home/pi/lisa/"
        call = path + "xiaomi_vaccum_cleaner_script.py -s -w 2 -c {0}".format(xiaomi)
        print "CALL: {}".format(call)
        rc = subprocess.Popen(call,shell=True)
        print "Subprocess ended with {}".format(rc)
    return msg, rc

#############################################################################
if __name__ == '__main__':
    app.run(debug=True)
