#!/usr/bin/env python

"""
check_solace - Checks Solace Systems Message Router statistics
"""

import getopt
import os
import sys
import tempfile
import time
from datetime import datetime
from xml.dom import minidom

import requests


def parse_options():
    global SOLACE_HOST
    global SOLACE_CLI_USERNAME
    global SOLACE_CLI_PASSWORD
    global SEMP_PORT
    global MODE
    global CRITICAL
    global WARNING

    try:
        long_options = ['SLOW_SUBSCRIBERS', 'CLIENT-MESSAGES-TOTAL', 'DISCARDS', 'DISCARD-RATE', 'EGRESS-DISCARDS',
                        'INGRESS-DISCARDS', 'CLIENT-MESSAGES-DATA', 'CLIENT-MESSAGES-PERSISTENT',
                        'CLIENT-MESSAGES-NONPERSISTENT', 'CLIENT-MESSAGES-DIRECT', 'CLIENT-MESSAGES-CONTROL',
                        'CLIENT-MESSAGES-RATE', 'CLIENT-BYTES-TOTAL', 'CLIENT-BYTES-DATA', 'CLIENT-BYTES-PERSISTENT',
                        'CLIENT-BYTES-NONPERSISTENT', 'CLIENT-BYTES-DIRECT', 'CLIENT-BYTES-CONTROL',
                        'CLIENT-BYTES-RATE', 'help']
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
        if o in ('-CLIENT-MESSAGES-TOTAL', "--CLIENT-MESSAGES-TOTAL"):
            MODE = "CLIENT-MESSAGES-TOTAL"
        if o in ('-DISCARDS', "--DISCARDS"):
            MODE = "DISCARDS"
        if o in ('-DISCARD-RATE', "--DISCARD-RATE"):
            MODE = "DISCARD-RATE"
        if o in ('-EGRESS-DISCARDS', "--EGRESS-DISCARDS"):
            MODE = "EGRESS-DISCARDS"
        if o in ('-INGRESS-DISCARDS', "--INGRESS-DISCARDS"):
            MODE = "INGRESS-DISCARDS"
        if o in ('-CLIENT-MESSAGES-DATA', "--CLIENT-MESSAGES-DATA"):
            MODE = "CLIENT-MESSAGES-DATA"
        if o in ('-CLIENT-MESSAGES-PERSISTENT', "--CLIENT-MESSAGES-PERSISTENT"):
            MODE = "CLIENT-MESSAGES-PERSISTENT"
        if o in ('-CLIENT-MESSAGES-NONPERSISTENT', "--CLIENT-MESSAGES-NONPERSISTENT"):
            MODE = "CLIENT-MESSAGES-NONPERSISTENT"
        if o in ('-CLIENT-MESSAGES-DIRECT', "--CLIENT-MESSAGES-DIRECT"):
            MODE = "CLIENT-MESSAGES-DIRECT"
        if o in ('-CLIENT-MESSAGES-CONTROL', "--CLIENT-MESSAGES-CONTROL"):
            MODE = "CLIENT-MESSAGES-CONTROL"
        if o in ('-CLIENT-MESSAGES-RATE', "--CLIENT-MESSAGES-RATE"):
            MODE = "CLIENT-MESSAGES-RATE"
        if o in ('-CLIENT-BYTES-TOTAL', "--CLIENT-BYTES-TOTAL"):
            MODE = "CLIENT-BYTES-TOTAL"
        if o in ('-CLIENT-BYTES-DATA', "--CLIENT-BYTES-DATA"):
            MODE = "CLIENT-BYTES-DATA"
        if o in ('-CLIENT-BYTES-PERSISTENT', "--CLIENT-BYTES-PERSISTENT"):
            MODE = "CLIENT-BYTES-PERSISTENT"
        if o in ('-CLIENT-BYTES-NONPERSISTENT', "--CLIENT-BYTES-NONPERSISTENT"):
            MODE = "CLIENT-BYTES-NONPERSISTENT"
        if o in ('-CLIENT-BYTES-DIRECT', "--CLIENT-BYTES-DIRECT"):
            MODE = "CLIENT-BYTES-DIRECT"
        if o in ('-CLIENT-BYTES-CONTROL', "--CLIENT-BYTES-CONTROL"):
            MODE = "CLIENT-BYTES-CONTROL"
        if o in ('-CLIENT-BYTES-RATE', "--CLIENT-BYTES-RATE"):
            MODE = "CLIENT-BYTES-RATE"


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
               '  -h, -help                            Show this help\n' \
               '  -H <hostname>                        * Solace hostname or IP address\n' \
               '  -p <port>                            Solace SEMP port\n' \
               '  -U <username>                        Solace SEMP username\n' \
               '  -P <password>                        Solace SEMP password\n' \
               '  -c <value>                           * Critical value\n'\
               '  -w <value>                           * Warning value\n'\
               '  --SLOW_SUBSCRIBERS                   [*] Check slow subscriber count\n'\
               '  --CLIENT-MESSAGES-TOTAL              [*] Check total message count\n'\
               '  --CLIENT-MESSAGES-DATA               [*] Check total message count\n'\
               '  --CLIENT-MESSAGES-PERSISTENT         [*] Check persistent message count\n'\
               '  --CLIENT-MESSAGES-NONPERSISTENT      [*] Check non-persistent message count\n'\
               '  --CLIENT-MESSAGES-DIRECT             [*] Check direct message count\n'\
               '  --CLIENT-MESSAGES-CONTROL            [*] Check control message count\n'\
               '  --CLIENT-MESSAGES-RATE               [*] Check 60-second message rate\n'\
               '  --CLIENT-BYTES-TOTAL                 [*] Check total message bytes\n'\
               '  --CLIENT-BYTES-DATA                  [*] Check data message bytes\n'\
               '  --CLIENT-BYTES-PERSISTENT            [*] Check persistent message bytes\n'\
               '  --CLIENT-BYTES-NONPERSISTENT         [*] Check non-persistent message bytes\n'\
               '  --CLIENT-BYTES-DIRECT                [*] Check direct message bytes\n'\
               '  --CLIENT-BYTES-CONTROL               [*] Check control message bytes\n'\
               '  --CLIENT-BYTES-RATE                  [*] Check 60-second message bandwidth\n'\
               '  --DISCARDS                    [*] Check ingress/egress discards\n'\
               '  --DISCARD-RATE                [*] Calculates 1-min ingress/egress discard rate\n'\
               '  --INGRESS-DISCARDS            [*] Checks ingress discards\n'\
               '  --EGRESS-DISCARDS             [*] Checks egress discards\n\n'

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
    print "SLOW_SUBSCRIBERS", status, "-", "Slow_Subscribers = %s|Slow_Subscribers=%s;%s;%s;0" \
                                           % (slow_subscribers, slow_subscribers, WARNING, CRITICAL)


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
    print "DISCARDS", status, "-", "Ingress_Discards = %s Egress_Discards = %s|Ingress_Discards=%s;%s;%s;0 " \
                                   "Egress_Discards=%s;%s;%s;0" \
                                   % (ingress_discards, egress_discards, ingress_discards, WARNING, CRITICAL,
                                      egress_discards, WARNING, CRITICAL)


def solace_egress_discards():
    transmit_congestion_discards = 0
    compression_congestion_discards = 0
    egress_discards = 0
    msg_spool_discards = 0
    message = "<rpc semp-version='soltr/7_1'><show><stats><client><detail></detail></client></stats></show></rpc>"
    r = requests.post(call_path, auth=(SOLACE_CLI_USERNAME, SOLACE_CLI_PASSWORD), data=message)
    output = minidom.parseString(r.content)
    if output.getElementsByTagName('client'):
        egress_discards = output.getElementsByTagName('total-egress-discards')[0].firstChild.nodeValue
        transmit_congestion_discards = output.getElementsByTagName('transmit-congestion')[0].firstChild.nodeValue
        compression_congestion_discards = output.getElementsByTagName('compression-congestion')[0].firstChild.nodeValue
        msg_spool_discards = output.getElementsByTagName('msg-spool-egress-discards')[0].firstChild.nodeValue
    status = "OK"
    print "EGRESS-DISCARDS", status, "-", "Total_Egress_Discards = %s Transmit_Congestion_Discards = %s " \
                                   "Compression_Congestion_Discards = %s Msg_Spool_Egress_Discards = %s|" \
                                   "Total_Egress_Discards=%s;%s;%s;0 Transmit_Congestion_Discards=%s;%s;%s;0 " \
                                   "Compression_Congestion_Discards=%s;%s;%s;0 Msg_Spool_Egress_Discards=%s;%s;%s;0" % \
                                   (egress_discards, transmit_congestion_discards, compression_congestion_discards,
                                    msg_spool_discards, egress_discards, WARNING, CRITICAL,
                                    transmit_congestion_discards, WARNING, CRITICAL, compression_congestion_discards,
                                    WARNING, CRITICAL, msg_spool_discards, WARNING, CRITICAL)


def solace_ingress_discards():
    ingress_discards = 0
    no_subscription_match = 0
    msg_spool_discards = 0
    msg_spool_congestion = 0
    message = "<rpc semp-version='soltr/7_1'><show><stats><client><detail></detail></client></stats></show></rpc>"
    r = requests.post(call_path, auth=(SOLACE_CLI_USERNAME, SOLACE_CLI_PASSWORD), data=message)
    output = minidom.parseString(r.content)
    if output.getElementsByTagName('client'):
        ingress_discards = output.getElementsByTagName('total-ingress-discards')[0].firstChild.nodeValue
        no_subscription_match = output.getElementsByTagName('no-subscription-match')[0].firstChild.nodeValue
        msg_spool_discards = output.getElementsByTagName('msg-spool-discards')[0].firstChild.nodeValue
        msg_spool_congestion = output.getElementsByTagName('message-spool-congestion')[0].firstChild.nodeValue
    status = "OK"
    print "INGRESS-DISCARDS", status, "-", "Total_Ingress_Discards = %s No_Subscription_Match = %s " \
                                   "Msg_Spool_Discards = %s Msg_Spool_Congestion = %s|" \
                                   "Total_Ingress_Discards=%s;%s;%s;0 No_Subscription_Match=%s;%s;%s;0 " \
                                   "Msg_Spool_Ingress_Discards=%s;%s;%s;0 Msg_Spool_Congestion=%s;%s;%s;0" % \
                                   (ingress_discards, no_subscription_match, msg_spool_discards,
                                    msg_spool_congestion, ingress_discards, WARNING, CRITICAL,
                                    no_subscription_match, WARNING, CRITICAL, msg_spool_discards,
                                    WARNING, CRITICAL, msg_spool_congestion, WARNING, CRITICAL)


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
        print "DISCARD-RATE", status, "-", "Ingress_Discards/%ssec=%s Egress_Discards/%ssec=%s|" \
                                           "Ingress_Discards_Rate=%s;%s;%s;0 Egress_Discards_Rate=%s;%s;%s;0" % \
                                           (time_spread, ingress_discards_rate, time_spread, egress_discards_rate,
                                            ingress_discards_rate, WARNING, CRITICAL,
                                            egress_discards_rate, WARNING, CRITICAL)
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


def solace_client_in_out(sempvar_in, sempvar_out, heading, var_disp):
    data_in = 0
    data_out = 0
    message = "<rpc semp-version='soltr/7_1'><show><stats><client></client></stats></show></rpc>"
    r = requests.post(call_path, auth=(SOLACE_CLI_USERNAME, SOLACE_CLI_PASSWORD), data=message)
    output = minidom.parseString(r.content)
    if output.getElementsByTagName('client'):
        data_in = output.getElementsByTagName(sempvar_in)[0].firstChild.nodeValue
        data_out = output.getElementsByTagName(sempvar_out)[0].firstChild.nodeValue
    status = "OK"
    print heading, status, "-", "%s_IN = %s %s_OUT = %s|%s_IN=%s;%s;%s;0 " \
                                   "%s_OUT=%s;%s;%s;0" \
                                   % (var_disp, data_in, var_disp, data_out, var_disp, data_in, WARNING, CRITICAL,
                                      var_disp, data_out, WARNING, CRITICAL)


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
    if MODE == "EGRESS-DISCARDS":
        solace_egress_discards()
    if MODE == "INGRESS-DISCARDS":
        solace_ingress_discards()
    if MODE == "CLIENT-MESSAGES-TOTAL":
        solace_client_in_out('total-client-messages-received', 'total-client-messages-sent', "CLIENT_TOTAL_MESSAGES", "Client_Total_Messages")
    if MODE == "CLIENT-MESSAGES-DATA":
        solace_client_in_out('client-data-messages-received', 'client-data-messages-sent', "CLIENT_DATA_MESSAGES", "Client_Data_Messages")
    if MODE == "CLIENT-MESSAGES-PERSISTENT":
        solace_client_in_out('client-persistent-messages-received', 'client-persistent-messages-sent', "CLIENT_PERSISTENT_MESSAGES", "Client_Persistent_Messages")
    if MODE == "CLIENT-MESSAGES-NONPERSISTENT":
        solace_client_in_out('client-non-persistent-messages-received', 'client-non-persistent-messages-sent', "CLIENT_NON_PERSISTENT_MESSAGES", "Client_Non_Persistent_Messages")
    if MODE == "CLIENT-MESSAGES-DIRECT":
        solace_client_in_out('client-direct-messages-received', 'client-direct-messages-sent', "CLIENT_DIRECT_MESSAGES", "Client_Direct_Messages")
    if MODE == "CLIENT-MESSAGES-CONTROL":
        solace_client_in_out('client-control-messages-received', 'client-control-messages-sent', "CLIENT_CONTROL_MESSAGES", "Client_Control_Messages")
    if MODE == "CLIENT-MESSAGES-RATE":
        solace_client_in_out('average-ingress-rate-per-minute', 'average-egress-rate-per-minute', "MESSAGE_RATE_60s", "Message_Rate_60s")
    if MODE == "CLIENT-BYTES-TOTAL":
        solace_client_in_out('total-client-bytes-received', 'total-client-bytes-sent', "CLIENT_TOTAL_BYTES", "Client_Total_Bytes")
    if MODE == "CLIENT-BYTES-DATA":
        solace_client_in_out('client-data-bytes-received', 'client-data-bytes-sent', "CLIENT_DATA_BYTES", "Client_Data_Bytes")
    if MODE == "CLIENT-BYTES-PERSISTENT":
        solace_client_in_out('client-persistent-bytes-received', 'client-persistent-bytes-sent', "CLIENT_PERSISTENT_BYTES", "Client_Persistent_Bytes")
    if MODE == "CLIENT-BYTES-NONPERSISTENT":
        solace_client_in_out('client-non-persistent-bytes-received', 'client-non-persistent-bytes-sent', "CLIENT_NON_PERSISTENT_BYTES", "Client_Non_Persistent_Bytes")
    if MODE == "CLIENT-BYTES-DIRECT":
        solace_client_in_out('client-direct-bytes-received', 'client-direct-bytes-sent', "CLIENT_DIRECT_BYTES", "Client_Direct_Bytes")
    if MODE == "CLIENT-BYTES-CONTROL":
        solace_client_in_out('client-control-bytes-received', 'client-control-bytes-sent', "CLIENT_CONTROL_BYTES", "Client_Control_Bytes")
    if MODE == "CLIENT-BYTES-RATE":
        solace_client_in_out('average-ingress-byte-rate-per-minute', 'average-egress-byte-rate-per-minute', "MESSAGE_BYTE_RATE_60s", "Message_Byte_Rate_60s")
