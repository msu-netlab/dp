"""
<Program>
  run_experimentlib_examples.py
  
<Author>
  Justin Samuel
  
<Date Started>
  December 11, 2009
  
<Purpose>
  This is a way to assist manually testing the experimentlib. This may
  come in handy later for writing automated tests.
  
<Usage>
  How I use it:
    * Set the proper path and constants at the top of the script.
    * Start a python/ipython shell.
    * import run_experimentlib_examples
    * run the functions by using commands such as:
        run_experimentlib_examples.test_lookup_node_locations()
"""

import os
import sys

# This should be the directory with experimentlib.py
sys.path.append("experimentlibrary/")
# This should be the experimentmanager's examples/ directory.
sys.path.append("experimentlibrary/examples/")

import experimentlib



# This will be used by both tests that use public nodemanager commands but
# require a key (e.g. for advertise lookups) as well as tests that use
# nodemanager commands that require user privileges.
USER_PUBLICKEY_FILENAME = "/path/to/user.publickey"
# User's private key only needed for tests that require user privileges.
USER_PRIVATEKEY_FILENAME = "/path/to/user.privatekey"

# Only needed for tests that require vessel owner privileges.
OWNER_PUBLICKEY_FILENAME = "/path/to/owner.publickey"
OWNER_PRIVATEKEY_FILENAME = "/path/to/owner.privatekey"

# For test_run_program().
PROGRAM_FILE = "myprogram.py"
ARGUMENTS_TO_START_PROGRAM_WITH = []

# For test_seattlegeni_maintain_vessels().
experimentlib.SEATTLECLEARINGHOUSE_ALLOW_SSL_INSECURE = False
experimentlib.SEATTLECLEARINGHOUSE_CA_CERTS_FILES = None
MIN_VESSELS_TO_KEEP = 4

# For test_upload_files().
FILES_TO_UPLOAD = ['file1.txt', 'file2.txt']

# For test_set_user_keys().
VESSELNAME_TO_SET_USER_KEYS_ON = "v100"
# A list of public key strings (e.g. ['123 456'])
USERKEY_LIST = []

# For test_monitor_vessel_status().
LOOKUP_SLEEP_SECONDS = 20
MONITOR_SLEEP_SECONDS = 5



def test_lookup_node_locations():
  import lookup_node_locations as test
  test.PUBLICKEY_FILENAME = USER_PUBLICKEY_FILENAME
  test.main()



def test_download_files():
  import download_files as test
  test.PUBLICKEY_FILENAME = USER_PUBLICKEY_FILENAME
  test.PRIVATEKEY_FILENAME = USER_PRIVATEKEY_FILENAME
  test.main()



def test_get_logs():
  import get_logs as test
  test.PUBLICKEY_FILENAME = USER_PUBLICKEY_FILENAME
  test.PRIVATEKEY_FILENAME = USER_PRIVATEKEY_FILENAME
  test.main()



def test_run_program():
  import run_program as test
  test.PUBLICKEY_FILENAME = USER_PUBLICKEY_FILENAME
  test.PRIVATEKEY_FILENAME = USER_PRIVATEKEY_FILENAME
  test.PROGRAM_FILE = PROGRAM_FILE
  test.ARGUMENTS_TO_START_PROGRAM_WITH = ARGUMENTS_TO_START_PROGRAM_WITH
  test.main()



def test_seattlegeni_maintain_vessels():
  import seattlegeni_maintain_vessels as test
  test.PUBLICKEY_FILENAME = USER_PUBLICKEY_FILENAME
  test.PRIVATEKEY_FILENAME = USER_PRIVATEKEY_FILENAME
  test.MIN_VESSELS_TO_KEEP = MIN_VESSELS_TO_KEEP
  test.main()



def test_upload_files():
  import upload_files as test
  test.PUBLICKEY_FILENAME = USER_PUBLICKEY_FILENAME
  test.PRIVATEKEY_FILENAME = USER_PRIVATEKEY_FILENAME
  test.FILES_TO_UPLOAD = FILES_TO_UPLOAD
  test.main()



def test_set_user_keys():
  import set_user_keys as test
  test.PUBLICKEY_FILENAME = OWNER_PUBLICKEY_FILENAME
  test.PRIVATEKEY_FILENAME = OWNER_PRIVATEKEY_FILENAME
  test.VESSELNAME_TO_SET_USER_KEYS_ON = VESSELNAME_TO_SET_USER_KEYS_ON
  test.USERKEY_LIST = USERKEY_LIST
  test.main()



def test_monitor_vessel_status():
  import monitor_vessel_status as test
  test.PUBLICKEY_FILENAME = USER_PUBLICKEY_FILENAME
  test.LOOKUP_SLEEP_SECONDS = LOOKUP_SLEEP_SECONDS
  test.MONITOR_SLEEP_SECONDS = MONITOR_SLEEP_SECONDS
  test.main()



if __name__ == "__main__":
  print("This module is not yet meant to be run as a script. For now, just " +
        "import it and call the functions individually")
  sys.exit(1)
