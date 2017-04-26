#!/usr/bin/python

###################################################
#  Alexa - skill Lisa Xiaomi vaccum cleaner
#
#  based on flask_ask
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
from flask_ask import Ask, statement, question, session

ROBOT_NAME = "Lisa"

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger("flask_ask").setLevel(logging.INFO)

#
# Alexa commands which can be used
COMMANDS = {}
COMMANDS['ON'] = {"START":'SAUGEN | REINIGEN | STAUBSAUGEN | REINIGUNG'}
COMMANDS['OFF'] = {"STOP":'BEENDEN | FERTIG | AUFHOEREN | STOPPE | BEENDE'}
COMMANDS['POWER'] = {
    "POWERA":'FLUESTERN | LEISE | MINIMAL | SCHWACH | WENIG',
    "POWERB":'NORMAL | STANDARD',
    "POWERC":'POWER | MAXIMAL | TURBO | MAXIMUM | STARK'
}
COMMANDS['HOME'] = {"HOME":'LADESTATION | BASISSTATION | LADEN'}
COMMANDS['FIND'] = {"FIND":'SAUGEN | REINIGEN | STAUBSAUGEN | REINIGUNG'}

#
# real Xiaomi commands which are used in external script
#
XIAOMI_COMMANDS = {}
XIAOMI_COMMANDS['START'] = 'start'
XIAOMI_COMMANDS['STOP'] = 'stop'
XIAOMI_COMMANDS['POWERA'] = 'silent'
XIAOMI_COMMANDS['POWERB'] = 'standard'
XIAOMI_COMMANDS['POWERC'] = 'power'
XIAOMI_COMMANDS['FIND'] = 'find'
XIAOMI_COMMANDS['HOME'] = 'home'

@ask.launch
def new_xiaomi_cleaner_session():
    welcome_text = render_template('welcome',robot_name=ROBOT_NAME)
    help_text = render_template('help')
    return question(welcome_text).reprompt(help_text)

##### intent decorators ############################
def _command_msg(cmd, power=None):
    msg = 'help'
    if cmd == 'on':
        msg = render_template('start', power=power)
    if cmd == 'off':
        msg = render_template('stop')
    if cmd == 'off2':
        msg = render_template('stop2')
    if cmd == 'helpon':
        list = "saugen, reinigen, staubsaugen, reinigung"
        msg = render_template('help_on',cmd=list)
    if cmd == 'helpoff':
        list = "beenden,fertig,aufhoeren,stoppe,beende"
        msg = render_template('help_off',cmd=list)
    if cmd == 'helppower':
        list = "fluestern,leise,minimal"
        msg = render_template('help_power',cmd=list)
    if cmd == 'home':
        msg = render_template('home')
    return msg

@ask.intent('cleanerON',
    default={'on':'saugen', 'power':'normal'}
)
def cmd_on(on,power=''):
    follow = render_template('follow')
    print("====> cmd_on {} {}".format(on,power))
    msg, rc = _xiaomi_robot(on,power)
    #
    # if we got no error message, create a success message
    if msg == None:
        msg = _command_msg('on',power)
    return statement(msg)

@ask.intent('cleanerOFF')
def cmd_off(off):
    follow = render_template('follow')
    print("====> cmd_off {}".format(off))
    msg,rc = _xiaomi_robot(off)
    #
    # if we got no error message, create a success message
    if msg == None:
        msg = _command_msg('off2')
    return question(msg).reprompt(follow)
#
# called if user answer last stop-question with YES
@ask.intent('AMAZON.YesIntent')
def show_commands():
    follow = render_template('follow')
    msg,rc = _xiaomi_robot('home')
    return question(cmd_list).reprompt(follow)

@ask.intent('cleanerHome')
def cmd_off(home):
    follow = render_template('follow')
    print("====> cmd_home {}".format(home))
    msg,rc = _xiaomi_robot(home)
    #
    # if we got no error message, create a success message
    if msg == None:
        msg = _command_msg('on')
    return statement(msg)

@ask.intent('cleanerHelpOn')
def cmd_off():
    follow = render_template('follow')
    msg = _command_msg('helpon')
    return question(msg).reprompt(follow)

@ask.intent('cleanerHelpOff')
def cmd_off():
    follow = render_template('follow')
    msg = _command_msg('helpoff')
    return question(msg).reprompt(follow)

@ask.intent('cleanerHelpPower')
def cmd_off():
    follow = render_template('follow')
    msg = _command_msg('helppower')
    return question(msg).reprompt(follow)


@ask.intent('AMAZON.HelpIntent')
def help():
    help_text = render_template('help')
    return question(help_text).reprompt(help_text)

@ask.intent('AMAZON.YesIntent')
def show_commands():
    follow = render_template('follow')
    cmd_list = COMMANDS.keys
    return question(cmd_list).reprompt(follow)

@ask.intent('AMAZON.NoIntent')
def show_commands():
    follow = render_template('follow')
    return question(follow)

@ask.intent('AMAZON.CancelIntent')
@ask.intent('AMAZON.StopIntent')
def stop():
    bye_text = render_template('bye')
    return statement(bye_text)

######### session decorators ##################
@ask.on_session_started
def new_session():
    logging.info('new session started')

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
