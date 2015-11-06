#!/usr/bin/env python

"""
check_solace - Checks Solace Systems Message Router statistics
"""

import sys
import os
import getopt
import requests
import tempfile
import time
from xml.dom import minidom
from datetime import datetime

def parse_options():
    global SOLACE_HOST
    global SOLACE_CLI_USERNAME
    global SOLACE_CLI_PASSWORD
    global SEMP_PORT
    global MODE
    global CRITICAL
    global WARNING

    try:
        long_options = ['SLOW_SUBSCRIBERS', 'DISCARDS', 'DISCARD-RATE', 'help']
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
        if o in ('-DISCARDS', "--DISCARDS"):
            MODE = "DISCARDS"
        if o in ('-DISCARD-RATE', "--DISCARD-RATE"):
            MODE = "DISCARD-RATE"
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
               '  --SLOW_SUBSCRIBERS          [*] Check Slow Subscribers\n'\
               '  --DISCARDS                  [*] Check ingress/egress discards\n'\
               '  --DISCARD-RATE              [*] Calculates 1-min ingress/egress discard rate\n\n'
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


def solace_discards():
    ingress_discards = 0
    egress_discards = 0
    message = "<rpc semp-version='soltr/7_1'><show><stats><client></client></stats></show></rpc>"
    r = requests.post(call_path, auth=(SOLACE_CLI_USERNAME, SOLACE_CLI_PASSWORD), data=message)
    output = minidom.parseString(r.content)
    if output.getElementsByTagName('client'):
        ingress_discards = output.getElementsByTagName('total-ingress-discards')[0].firstChild.nodeValue
        egress_discards = output.getElementsByTagName('total-egress-discards')[0].firstChild.nodeValue
    status = "OK"
    print "DISCARDS", status, "-", "Ingress_Discards = %s Egress_Discards = %s|Ingress_Discards=%s;%s;%s;0 Egress_Discards=%s;%s;%s;0" % (ingress_discards, egress_discards, ingress_discards, WARNING, CRITICAL, egress_discards, WARNING, CRITICAL)


def solace_discard_rate():
    time_spread = 60  # seconds to average values over
    ingress_discards = 0
    egress_discards = 0
    prev_ingress_discards = 0
    prev_egress_discards = 0
    current_time = time.mktime(datetime.now().timetuple())
    prev_time = None
    diff_time = None
    diff_ingress_discards = None
    diff_egress_discards = None
    ingress_discards_rate = 0
    egress_discards_rate = 0
    prev_ingress_discards_rate = 0
    prev_egress_discards_rate = 0

    cache_filename = tempfile.gettempdir() + "/check_solace_" + SOLACE_HOST + ".cache"
    message = "<rpc semp-version='soltr/7_1'><show><stats><client></client></stats></show></rpc>"
    r = requests.post(call_path, auth=(SOLACE_CLI_USERNAME, SOLACE_CLI_PASSWORD), data=message)
    output = minidom.parseString(r.content)
    if output.getElementsByTagName('client'):
        ingress_discards = output.getElementsByTagName('total-ingress-discards')[0].firstChild.nodeValue
        egress_discards = output.getElementsByTagName('total-egress-discards')[0].firstChild.nodeValue

    # read previous values from cache file
    if os.path.isfile(cache_filename):
        # cache file exists - read data
        cache_file = open(cache_filename, 'r+')
        prev_time = cache_file.readline().rstrip('\n')
        prev_ingress_discards = cache_file.readline().rstrip('\n')
        prev_egress_discards = cache_file.readline().rstrip('\n')
        prev_ingress_discards_rate = cache_file.readline().rstrip('\n')
        prev_egress_discards_rate = cache_file.readline().rstrip('\n')

        # calculate difference stats
        diff_time = float(current_time) - float(prev_time)
        diff_ingress_discards = float(ingress_discards) - float(prev_ingress_discards)
        diff_egress_discards = float(egress_discards) - float(prev_egress_discards)
        ingress_discards_rate = diff_ingress_discards / (diff_time / time_spread)
        egress_discards_rate = diff_egress_discards / (diff_time / time_spread)

        # require time_spread seconds to pass before calculating stats
        if diff_time < time_spread:
            ingress_discards_rate = prev_ingress_discards_rate
            egress_discards_rate = prev_egress_discards_rate
        else:
            # delete the contents of the cache file and write new values
            cache_file.seek(0)
            cache_file.truncate()
            cache_file.write(str(current_time) + "\n")
            cache_file.write(str(ingress_discards) + "\n")
            cache_file.write(str(egress_discards) + "\n")
            cache_file.write(str(ingress_discards_rate) + "\n")
            cache_file.write(str(egress_discards_rate) + "\n")
            cache_file.close()

        status = "OK"
        if float(ingress_discards_rate) >= float(CRITICAL) or float(egress_discards_rate) >= float(CRITICAL):
            status = "Critical"
        elif float(ingress_discards_rate) >= float(WARNING) or float(egress_discards_rate) >= float(WARNING):
            status = "Warning"
        print "DISCARD-RATE", status, "-", "Ingress_Discards/%ssec=%s Egress_Discards/%ssec=%s|Ingress_Discards_Rate=%s;%s;%s;0 Egress_Discards_Rate=%s;%s;%s;0" % (time_spread, ingress_discards_rate, time_spread, egress_discards_rate, ingress_discards_rate, WARNING, CRITICAL, egress_discards_rate, WARNING, CRITICAL)

    else:
        # cache file doesn't exist - create file and write stats
        cache_file = open(cache_filename, 'w')
        cache_file.write(str(current_time) + "\n")
        cache_file.write(str(ingress_discards) + "\n")
        cache_file.write(str(egress_discards) + "\n")
        cache_file.write(str(ingress_discards_rate) + "\n")
        cache_file.write(str(egress_discards_rate) + "\n")
        cache_file.close()
        print "First run - creating cache file", cache_filename, "for discard rate calculation"
        return


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
    if MODE == "DISCARDS":
        solace_discards()
    if MODE == "DISCARD-RATE":
        solace_discard_rate()