#!/usr/bin/env python

"""
check_solace - Checks Solace Systems Message Router statistics
"""

import sys
import getopt
import requests
from xml.dom import minidom


def parse_options():
    global SOLACE_HOST
    global SOLACE_CLI_USERNAME
    global SOLACE_CLI_PASSWORD
    global SEMP_PORT
    global MODE
    global CRITICAL
    global WARNING

    try:
        long_options = ['SLOW_SUBSCRIBERS', 'help']
        opts, args = getopt.getopt(sys.argv[1:], "hc:w:H:U:P:p:", long_options)
    except getopt.GetoptError:
        sys.stderr.write(display_help())
        sys.exit(3)

    if len(args):
        sys.stderr.write("Unknown arguments: %s\n" % args)
        sys.exit(3)

    MODE = None
    WARNING = None
    CRITICAL = None

    for o, a in opts:
        if o in ('-SLOW_SUBSCRIBERS', "--SLOW_SUBSCRIBERS"):
            MODE = "SLOW_SUBSCRIBERS"
        if o in ('-h', '--help'):
            sys.stdout.write(display_help())
            sys.exit(0)
        if o in ('-c',):
            try:
                CRITICAL = a
            except:
                sys.stderr.write(display_help())
                sys.exit(3)
        if o in ('-w',):
            try:
                WARNING = a
            except:
                sys.stderr.write(display_help())
                sys.exit(3)
        if o in ('-H',):
            try:
                SOLACE_HOST = a
            except:
                sys.stderr.write(display_help())
                sys.exit(3)
        if o in ('-U',):
            try:
                SOLACE_CLI_USERNAME = a
            except:
                sys.stderr.write(display_help())
                sys.exit(3)
        if o in ('-P',):
            try:
                SOLACE_CLI_PASSWORD = a
            except:
                sys.stderr.write(display_help())
                sys.exit(3)
        if o in ('-p',):
            try:
                SEMP_PORT = a
            except:
                sys.stderr.write(display_help())
                sys.exit(3)

    return MODE, CRITICAL, WARNING


def display_help():
    help_msg = 'check_solace - checks Solace Systems Message Router statistics\n\nUsage: check_solace [OPTION]...\n' \
               '\n' \
               '* denotes a required option\n\n'\
               '  -h, -help                   Show this help\n' \
               '  -H <hostname>               * Solace hostname or IP address\n' \
               '  -p <port>                   Solace SEMP port\n' \
               '  -U <username>               Solace SEMP username\n' \
               '  -P <password>               Solace SEMP password\n' \
               '  -c <value>                  * Critical value\n'\
               '  -w <value>                  * Warning value\n'\
               '  --SLOW_SUBSCRIBERS          [*] Check Slow Subscribers\n\n'
    return help_msg


def solace_slow_subscribers():
    slow_subscribers = 0
    message = "<rpc semp-version='soltr/7_1'><show><client><name>*</name><slow-subscriber></slow-subscriber></client></show></rpc>"
    r = requests.post(call_path, auth=(SOLACE_CLI_USERNAME, SOLACE_CLI_PASSWORD), data=message)
    output = minidom.parseString(r.content)

    if output.getElementsByTagName('client'):
        clients = output.getElementsByTagName('client-address')
        for client in clients:
            slow_subscribers += 1

    status = "OK"
    if int(slow_subscribers) >= int(CRITICAL):
        status = "Critical"
    elif int(slow_subscribers) >= int(WARNING):
        status = "Warning"

    print "SLOW_SUBSCRIBERS", status, "-", "Slow_Subscribers = %s|Slow_Subscribers=%s;%s;%s;0" % (slow_subscribers, slow_subscribers, WARNING, CRITICAL)



if __name__ == '__main__':
    SOLACE_HOST = None
    SOLACE_CLI_USERNAME = "admin"
    SOLACE_CLI_PASSWORD = "admin"
    SEMP_PORT = 80
    SEMP_PATH = "/SEMP"

    MODE, CRITICAL, WARNING = parse_options()

    if (SOLACE_HOST is None) or (MODE is None) or (WARNING is None) or (CRITICAL is None):
        sys.stderr.write(display_help())
        sys.exit(3)

    call_path = "http://" + SOLACE_HOST + ":" + str(SEMP_PORT) + SEMP_PATH
    if MODE == "SLOW_SUBSCRIBERS":
        solace_slow_subscribers()