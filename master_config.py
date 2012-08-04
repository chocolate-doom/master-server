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
# Configuration file for master server.
#

# Filename of log file.

LOG_FILE = "chocolate-master.log"

# Servers must refresh themselves periodically.  If nothing happens
# after this many seconds, remove them from the list.

SERVER_TIMEOUT = 2 * 60 * 60  # 2 hours

# How long is metadata valid before we force another query to refresh it?

METADATA_REFRESH_TIME = 6 * 60 * 60 # 6 hours

# Address and port to listen on.

SERVER_ADDRESS = (None, 2342)

# Address and port to bind query socket.

QUERY_ADDRESS = None

# ID of the GPG key to use to sign secure demo messages.
# Use the email address of the key or the hex key ID.

SIGNING_KEY = None

