"""
<Program Name>
  bundler.py
  
<Purpose>
  Bundles simplify the transferring of repy programs and associated data to and
  from vessels.  A bundle is a self-extracting repy program that contains a
  repy program and embedded files that the contained program depends on.
  Bundles have a .bundle.repy extension.
  
  Embedded files within a bundle are extracted into the local file system 
  before the flow of execution reaches the contained program.  Bundles do not 
  necessarily have to contain a repy program, and can be used solely to pack
  data into a single unit.

  This program is a command line wrapper to access the Bundle class 
  functionality.  You can use this to perform the following operations
  on bundles:
  
  - Create a new bundle
  - Add files to/Remove files from a bundle
  - Extract files from a bundle
  - Show a bundle's contents
  - Wipe a bundle's contents
  
<Usage>
  First, use this program to create the bundle.  Then, use this program to add
  the files you want to the bundle.
  
  For further usage information, run this program without any arguments. 
  
  
<Example Usage>
  # program.bundle.repy is the name of the output file to generate.
  # If you dont supply this value, then the bundle will be created in-place.
  $ python bundler.py create program.repy [program.bundle.repy]

  $ python bundler.py add program.bundle.repy file1 file2 file3
  $ python repy.py restrictions_file program.bundle.repy

"""

import sys
import repyhelper
repyhelper.translate_and_import('bundle.repy')


PROGRAM_HELPSTRING = """
Valid commands:
  $ bundle.repy create [source] bundlename
  $ bundle.repy wipe bundlename [outputfile]
  $ bundle.repy [list | extract-all]
  $ bundle.repy [add | extract | remove] bundlename {filename}

For more information on how to use a particular command:
  $ bundle.repy help [command]
"""


class BadArgumentsError(BaseException):
  """ The user gave us bad arguments. """


def _bundle_create(args):
  """
  <Purpose>
    Creates a bundle with the specified name.
    Optionally takes in a source argument.
  
  <Arguments>
    args: 
      A list of filenames.  This function's behavior changes depending on
      how many filenames are passed.
      
      Valid arguments:
        [source, bundle name]
        [bundle name]
  
  <Side Effects>
    Overwrites the existing file at bundle name if one exists.  If a source 
    file is not specified, we will treat an existing file as the source file.
  
  <Exceptions>
    None
    
  <Returns>
    None
  """
  # User passed us bad arguments
  if not len(args) in [1, 2]:
    raise BadArgumentsError("Expected Arguments: {source_filename} bundle_filename")
  
  
  # Args are: bundle_fn
  if len(args) == 1:
    bundle_Bundle(args[0], 'w')
  
  # Args are: src_fn, bundle_fn
  else:
    bundle_Bundle(args[1], 'w', srcfn=args[0])


def _bundle_list(args):
  """
  <Purpose>
    Lists the contents of the specified bundle.
  
  <Arguments>
    args:
      A list containing a single filename, which corresponds to a bundle name.
  
  <Side Effects>
    The contents of the specified bundle will be listed with their file sizes.

  <Exceptions>
    None
    
  <Returns>
    None
  """
  fname = args[0]
  headers = ("Filename", "Size (bytes)")
  bundle = bundle_Bundle(fname, 'r')
  filedata = bundle.list()
  
  # Get longest filename
  max_length = 0
  for fname in filedata:
    if len(fname) > max_length:
      max_length = len(fname)
  # Give the first column enough room
  if max_length < len(headers[0]):
    max_length = len(headers[0])
  # Cap the maximum length so we don't overflow every single line
  elif max_length > 60:
    max_length = 60
  
  # Filename      Size (bytes)
  #    file1                14
  #    file2             14234
  # ...
  base_format = "%"+str(max_length)+"s   %"+str(len(headers[1]))
  header_format = (base_format + 's')
  filelist_format = (base_format + 'i')
  
  # Display the file list sorted
  file_list = filedata.keys()
  file_list.sort()
  
  print "Bundle contents:"
  print header_format % headers
  for file in file_list:
    print header_format % (file, filedata[file])
  
  
def _bundle_add(args):
  """
  <Purpose>
    Adds the specified files to the bundle.
  
  <Arguments>
    args:
      A list of filenames.
      
      The first filename is the bundlename.  Following filenames are files to
      add to the bundle.
  
  <Side Effects>
    Adds the specified files to the bundle.
  
  <Exceptions>
    None
    
  <Returns>
    None
  """
  fname = args[0]
  add_fnames = args[1:]
  bundle = bundle_Bundle(fname, 'a')
  failed = bundle.add_files(add_fnames)
  if failed:
    for key, value in failed.iteritems():
      print key, value


def _bundle_extract(args):
  """
  <Purpose>
    Extracts the specified files.
  
  <Arguments>
    args:
      A list of filenames.
      
      The first filename is the bundlename.  Following filenames are files to
      extract from the bundle.
  
  <Side Effects>
    Specified files within the bundle with be extracted to the local directory.
    Any conflicting files will be overwritten.
  
  <Exceptions>
    None
    
  <Returns>
    None
  """
  fname = args[0]
  extract_fnames = args[1:]
  bundle = bundle_Bundle(fname, 'r')
  failed = bundle.extract_files(extract_fnames)
  if failed:
    for key, value in failed.iteritems():
      print key, value
  
  
def _bundle_extract_all(args):
  """
  <Purpose>
    Extracts all files in a bundle.
  
  <Arguments>
    args:
      A list containing a single filename, which corresponds to a bundle name.
  
  <Side Effects>
    Files within the bundle with be extracted to the local directory.
    Any conflicting files will be overwritten.
  
  <Exceptions>
    None
    
  <Returns>
    None
  """
  fname = args[0]
  bundle = bundle_Bundle(fname, 'r')
  failed = bundle.extract_all()
  if failed:
    for key, value in failed.iteritems():
      print key, value
  
  
def _bundle_remove(args):
  """
  <Purpose>
    Removes the specified files.
  
  <Arguments>
    args:
      A list of filenames.
      
      The first filename is the bundlename.  Following filenames are files to
      remove from the bundle.
  
  <Side Effects>
    Existing files within the bundle with the specified names will be removed.
  
  <Exceptions>
    None
    
  <Returns>
    None
  """
  fname = args[0]
  remove_fnames = args[1:]
  bundle = bundle_Bundle(fname, 'a')
  failed = bundle.remove_files(remove_fnames)
  if failed:
    for key, value in failed.iteritems():
      print key, value


def _bundle_wipe(args):
  """
  <Purpose>
    Wipes the bundle with the specified name.
    Optionally takes in an output argument.
  
  <Arguments>
    args: 
      A list of filenames.  This function's behavior changes depending on
      how many filenames are passed.
      
      Valid arguments:
        [bundle name]
        [bundle name, output_file]
  
  <Side Effects>
    Overwrites the existing file at bundle name if one exists.  If an output
    file is not specified, we will overwrite the original file.
  
  <Exceptions>
    None
    
  <Returns>
    None
  """
  # User passed us bad arguments
  if not len(args) in [1, 2]:
    raise BadArgumentsError("Expected Arguments: bundle_filename {output_filename} ")
  
  fname = args[0]
  
  # Args are: bundle_fn
  if len(args) == 1:
    try:
      bundle_clear_bundle_from_file(fname)
    except bundle_InvalidOperationError:
      print fname, "is not a valid bundle"
    
  # Args are: bundle_fn, outputfile
  else:
    output_fname = args[1]
    
    # Copy over file contents
    _bundle_copy_file(fname, output_fname)

    try:
      bundle_clear_bundle_from_file(output_fname)
    except bundle_InvalidOperationError:
      print fname, "is not a valid bundle"

  

def _display_help(args):
  """
  <Purpose>
    Displays the helpstrings for the bundler.
  
  <Arguments>
    args: 
      The name of the command to query
  
  <Side Effects>
    None
  
  <Exceptions>
    None
    
  <Returns>
    None
  """
  if not args:
    print PROGRAM_HELPSTRING
    return
  
  if not args[0] in ACTIONDICT:
    print "'"+args[0]+"' is not a known command."
    print PROGRAM_HELPSTRING
    return
  
  print ACTIONDICT[args[0]]['helptext']


ACTIONDICT = {
  'create': {
    'callback': _bundle_create,
    'helptext': """
$ bundle.repy create [source] bundlename

Creates a new bundle at the specified output file.  If no source file is given
and the output file already exists, the existing file will be embedded into
the bundle.  Otherwise, the existing file will be overwritten.
    """,},
  'list': {
    'callback': _bundle_list,
    'helptext': """
$ bundle.repy list bundlename

Lists the contents of the specified bundle and their embedded file sizes.
The sizes of extracted files will be slightly smaller than the sizes listed 
here.
    """,},
  'add': {
    'callback': _bundle_add,
    'helptext': """
$ bundle.repy add bundlename file_1 [file_2] ... [file_n]

Adds the specified files to the bundle.  You must provide at least one file,
and file names must not have any spaces.
    """,},
  'extract': {
    'callback': _bundle_extract,
    'helptext': """
$ bundle.repy extract bundlename file_1 [file_2] ... [file_n]

Extracts the specified files to the currently working directory.  You must 
provide at least one file, and file names must not have any spaces.

WARNING:
  If there are files in the working directory with same filenames as 
  any of the specified files, they are overwritten!
""",},
  'extract-all': {
    'callback': _bundle_extract_all,
    'helptext': """
$ bundle.repy extract-all bundlename

Extracts all files to the current working directory.

WARNING:
  If there are files in the working directory with same filenames as 
  a file in those in the bundle, they are overwritten!
"""},
  'remove': {
    'callback': _bundle_remove,
    'helptext': """
$ bundle.repy remove bundlename file_1 [file_2] ... [file_n]

Removes the specified files from the bundle.  You must provide at least one 
file, and file names must not have any spaces.
""",},
  'wipe': {
    'callback': _bundle_wipe,
    'helptext': """
$ bundle.repy wipe bundlename [output_filename]

Wipes the bundle of embedded files and auto-extraction scripts.

WARNING:
  If no output file is provided, then all original bundle contents will be
  lost.
"""},
  'help': {
    'callback': _display_help,
    'helptext': PROGRAM_HELPSTRING
    }
}



if __name__ == '__main__':
  callargs = sys.argv[1:]
  # Perform a single task based on what the user inputted.
  if not callargs:
    print PROGRAM_HELPSTRING
    exitall()
  
  action = callargs[0].lower()
  arguments = callargs[1:]
  
  if action not in ACTIONDICT:
    print "Action is unsupported."
    print PROGRAM_HELPSTRING
    exit()
  
  try:
    ACTIONDICT[action]['callback'](arguments)
  except BadArgumentsError, e:
    print str(e)


