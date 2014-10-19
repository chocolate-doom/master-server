#!/usr/bin/env python
#
# Copyright(C) 2010 Simon Howard
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
#
# CGI script that generates master server web page.
#

from cgi import escape
from time import time
from select import select
import socket
import sys
import struct
import simplejson

NET_MASTER_PACKET_TYPE_GET_METADATA = 4
NET_MASTER_PACKET_TYPE_GET_METADATA_RESPONSE = 5

METADATA_GATHER_TIME = 0.1 # seconds

MASTER_SERVER = "master.chocolate-doom.org"
UDP_PORT = 2342

def send_message(sock, addr, message_type, payload=None):
    header = struct.pack(">h", message_type)
    packet = header

    if payload is not None:
        packet += payload

    sock.sendto(packet, addr)

def read_string(packet):
    terminator = struct.pack("b", 0)
    strlen = packet.index(terminator)

    result, = struct.unpack("%ss" % strlen, packet[0:strlen])

    return packet[strlen + 1:], result

def decode_string_list(packet):
    """ Decode binary data containing NUL-terminated strings. """

    strings = []

    while len(packet) > 0:
        packet, string = read_string(packet)

        strings.append(string)

    return strings

def process_metadata_response(packet):
    """ Process a response received from the master server. """

    type, = struct.unpack(">h", packet[0:2])

    if type != NET_MASTER_PACKET_TYPE_GET_METADATA_RESPONSE:
        raise Exception("Wrong packet type received: %i" % type)

    # Process the payload data (list of NUL-terminated strings)

    strings = decode_string_list(packet[2:])

    # Each string is a JSON-encoded dictionary.  Decode these.

    return map(simplejson.loads, strings)

def get_metadata(addr_str):
    """ Query a master server for metadata about its servers. """

    addr = (socket.gethostbyname(addr_str), UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send request to master.

    send_message(sock, addr, NET_MASTER_PACKET_TYPE_GET_METADATA)

    # Wait for METADATA_GATHER_TIME seconds to receive responses from
    # the master.  There may be multiple response packets if there are
    # lots of servers.

    servers = []
    start_time = time()

    while time() < start_time + METADATA_GATHER_TIME:
        r, w, x = select([sock], [], [], METADATA_GATHER_TIME)

        if sock in r:
            packet, remote_addr = sock.recvfrom(1024)

            servers += process_metadata_response(packet)

    return servers

# CGI script to print out server list.

def get_server_data():
    """ Query the master server and retrieve server metadata. """

    return get_metadata(MASTER_SERVER)

def age_string(seconds):
    seconds = int(seconds)
    minutes, seconds = seconds / 60, seconds % 60
    hours, minutes = minutes / 60, minutes % 60
    days, hours = hours / 24, hours % 24

    result = "%02i:%02i:%02i" % (hours, minutes, seconds)

    if days > 0:
        result = "%i days, %s" % (days, result)

    return result

def generate_table_row(server):
    """ Generate a row of the HTML table, containing data for a
        particular server. """

    data = [
        "%s:%i" % (server["address"], server["port"]),
        escape(server["name"]),
        escape(server["version"]),
        server["max_players"],
        age_string(server["age"])
    ]

    result = []

    for col in data:
        result.append("    <td>%s</td>\n" % col)

    return "<tr>\n" + ("".join(result)) + "</tr>\n"

def generate_table(server_data):
    """ Generate an HTML table from list of server metadata. """

    server_data = sorted(server_data, key=lambda server: -server["age"])

    result = []

    for server in server_data:
        result.append(generate_table_row(server))

    return "\n".join(result)

def read_template(filename):
    """ Read HTML template file. """

    file = open(filename)
    result = file.read().decode('utf8')
    file.close()

    return result

def output_html(html):
    """ Output HTML data back to client. """

    print "Content-Type: text/html; charset=utf-8"
    print
    sys.stdout.write(html.encode('utf8'))

template = read_template("index.template")

server_data = get_server_data()
table_data = generate_table(server_data)
html = template.replace("___TABLE_DATA___", table_data)

output_html(html)

