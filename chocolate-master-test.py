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
# Test script for querying the master server.
#

import socket
import sys
import struct
import simplejson

NET_MASTER_PACKET_TYPE_ADD = 0
NET_MASTER_PACKET_TYPE_ADD_RESPONSE = 1
NET_MASTER_PACKET_TYPE_QUERY = 2
NET_MASTER_PACKET_TYPE_QUERY_RESPONSE = 3
NET_MASTER_PACKET_TYPE_GET_METADATA = 4
NET_MASTER_PACKET_TYPE_GET_METADATA_RESPONSE = 5

UDP_PORT = 2342

def send_message(sock, addr, message_type, payload=None):
    header = struct.pack(">h", message_type)
    packet = header

    if payload is not None:
        packet += payload

    sock.sendto(packet, addr)

def get_response(sock, addr, message_type):
    """ Wait for a response of the specified type to be received. """

    while True:
        packet, remote_addr = sock.recvfrom(1024)

        if remote_addr == addr:
            type, = struct.unpack(">h", packet[0:2])

            if type != message_type:
                raise Exception("Wrong type of packet received: %i != %i" %
                                (type, message_type))

            return packet[2:]

        print "Rxed from %s, expected %s" % (remote_addr, addr)

def read_string(packet):
    terminator = struct.pack("b", 0)
    strlen = packet.index(terminator)

    result, = struct.unpack("%ss" % strlen, packet[0:strlen])

    return packet[strlen + 1:], result

def add_to_master(addr_str):
    """ Add self to master at specified IP address. """

    addr = (socket.gethostbyname(addr_str), UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send request

    print "Sending request to master at %s" % str(addr)

    send_message(sock, addr, NET_MASTER_PACKET_TYPE_ADD)

    # Wait for response.

    print "Waiting for response..."

    response = get_response(sock, addr, NET_MASTER_PACKET_TYPE_ADD_RESPONSE)

    success, = struct.unpack(">h", response)

    if not success:
        raise Exception("Address not successfully added to master.")

    print "Address added to master."

def decode_string_list(packet):
    """ Decode binary data containing NUL-terminated strings. """

    strings = []

    while len(packet) > 0:
        packet, string = read_string(packet)

        strings.append(string)

    return strings

def query_master(addr_str):
    """ Query a master server for its list of server IP addresses. """

    addr = (socket.gethostbyname(addr_str), UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send request

    print "Sending query to master at %s" % str(addr)

    send_message(sock, addr, NET_MASTER_PACKET_TYPE_QUERY)

    # Receive response

    print "Waiting for response..."

    response = get_response(sock, addr, NET_MASTER_PACKET_TYPE_QUERY_RESPONSE)

    servers = decode_string_list(response)

    print "%i servers" % len(servers)

    for s in servers:
        print "\t%s" % s

def get_metadata(addr_str):
    """ Query a master server for metadata about its servers. """

    addr = (socket.gethostbyname(addr_str), UDP_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send request

    print "Sending metadata query to master at %s" % str(addr)

    send_message(sock, addr, NET_MASTER_PACKET_TYPE_GET_METADATA)

    # Receive response

    print "Waiting for response..."

    response = get_response(sock, addr, NET_MASTER_PACKET_TYPE_GET_METADATA_RESPONSE)

    servers = decode_string_list(response)

    print "%i servers" % len(servers)

    for json in servers:
        metadata = simplejson.loads(json)
        print "\tServer: %s:%i" % (metadata["address"], metadata["port"])
        print "\t\tAge: %i seconds" % metadata["age"]
        print "\t\tName: %s" % metadata["name"]
        print "\t\tVersion: %s" % metadata["version"]
        print "\t\tMax. players: %i" % metadata["max_players"]

if len(sys.argv) > 2 and sys.argv[1] == "query":
    query_master(sys.argv[2])
elif len(sys.argv) > 2 and sys.argv[1] == "add":
    add_to_master(sys.argv[2])
elif len(sys.argv) > 2 and sys.argv[1] == "get-metadata":
    get_metadata(sys.argv[2])
else:
    print "Usage:"
    print "chocolate-master-test.py query <address>"
    print "chocolate-master-test.py add <address>"
    print "chocolate-master-test.py get-metadata <address>"

