#!/usr/bin/env python
#
# Copyright(C) 2012 Simon Howard
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
# This is a library used by the master for the signed demos system.  It
# uses GPG to create signed messages that are returned by the master
# back to the clients.
#

from io import BytesIO
import os
import sys
import time

NONCE_SIZE = 16 # bytes

try:
    import gpgme
    available = True
except ImportError:
    available = False

def now_string():
    """Generate an ISO8601 string for the current time."""
    now = time.time()
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))

def bin_to_hex(data):
    """Convert a string of binary data into a hex representation."""
    return "".join(map(lambda x: "%02x" % ord(x), data))

class SecureSigner(object):
    def __init__(self, key):
        """Initialize a new SecureSigner. Must be passed a key identifier
           string specifying the GPG key to use.  """
        self.context = gpgme.Context()
        self.key = self.context.get_key(key)
        self.context.signers = [ self.key ]

    def _generate_start_message(self, nonce):
        """Generate the plaintext used for a start message."""
        return "\n".join([
            "Start-Time: %s" % now_string(),
            "Nonce: %s" % bin_to_hex(nonce),
        ])

    def _sign_plaintext_message(self, message):
        """Sign a plaintext message."""
        signature = BytesIO()
        self.context.sign(BytesIO(message), signature, gpgme.SIG_MODE_CLEAR)
        return signature.getvalue()

    def sign_start_message(self):
        """Generate a new signed start message with a random nonce value."""
        nonce = os.urandom(NONCE_SIZE)
        message = self._generate_start_message(nonce)
        return (nonce, self._sign_plaintext_message(message))

    def _verify_signature(self, result):
        """Check the results of a verify operation."""
        if len(result) != 1:
            return False

        # Check the signature is valid:
        signature = result[0]
        if (signature.summary & gpgme.SIGSUM_VALID) == 0:
            return False

        # Check the signature matches the right key:
        for subkey in self.key.subkeys:
            if subkey.fpr == signature.fpr:
                break
        else:
            return False

        return True

    def _verify_start_message(self, signed_message):
        """Check that a signed message is correctly signed, returning
           the plaintext if it is valid, or None if it is invalid."""
        # Parse the plain text signed message:
        try:
            plaintext = BytesIO()
            result = self.context.verify(BytesIO(signed_message),
                                         None, plaintext)
            if self._verify_signature(result):
                return plaintext.getvalue()
        except gpgme.GpgmeError:
            pass

        # Failure of some kind occurred: message failed to parse, or
        # did not pass verification, etc.
        return None

    def sign_end_message(self, start_message, demo_hash):
        """Verify a start message and sign an end message that verifies
           a complete demo."""
        plaintext = self._verify_start_message(start_message)
        if plaintext is None:
            return None

        # We assume the plaintext message ends with a newline.
        if plaintext[-1] != "\n":
            plaintext = plaintext + "\n"

        # Add extra fields to the plaintext, to create the end message.
        message = plaintext + "\n".join([
            "End-Time: %s" % now_string(),
            "Demo-Checksum: %s" % bin_to_hex(demo_hash),
        ])
        return self._sign_plaintext_message(message)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <start|end> <key>" % sys.argv[0]
        sys.exit(1)

    signer = SecureSigner(sys.argv[2])
    if sys.argv[1] == "start":
        nonce, start_message = signer.sign_start_message()
        print "Nonce: %s" % bin_to_hex(nonce)
        print start_message
    elif sys.argv[1] == "end":
        start_message = sys.stdin.read()
        fake_checksum = "3vism1idm4ibmaJ3nF1f"
        print signer.sign_end_message(start_message, fake_checksum)

