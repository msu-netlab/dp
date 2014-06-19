"""
Author: Armon Dadgar
Description:
  This namespace can be used as an intermediary logging namespace to
  log calls to the Repy API functions.
"""

# These API functions do _not_ return an object, and can be handled uniformly.
NON_OBJ_API_CALLS = ["gethostbyname_ex","getmyip","sendmess","stopcomm", "listdir","removefile",
                     "exitall","getruntime","randomfloat","settimer","canceltimer","sleep","get_thread_name"]

# Global print lock
PRINT_LOCK = getlock()

# If this is True, then output will be serialized,
# this avoids jumbling but is a performance hit
ENABLE_LOCKING = True

# Limit the maximum print length of arguments and results
MAX_PRINT_VALS = 200  # Print the first 200 characters worth

# Handle when locking is disabled
if not ENABLE_LOCKING:
  def _noop(*args,**kwargs):
    return True
  
  PRINT_LOCK.acquire = _noop
  PRINT_LOCK.release = _noop


# Replace getruntime
if "_orig_getruntime" not in _context:
  _orig_getruntime = getruntime
def getruntime():
  return round(_orig_getruntime(), 5)


# Do a traced function call
def traced_call(self,name,func,args,kwargs,no_return=False,print_args=True,print_result=True):
  # Store the time, function call and arguments
  call_string = str(getruntime()) + " " + name

  # Print the optional stuff
  if not self is None:
    call_string += " " + str(self)
  if print_args and not args == ():
    str_args = str(args)
    if len(str_args) > MAX_PRINT_VALS:
      str_args = str_args[:MAX_PRINT_VALS] + "...)"
    call_string += " " + str_args
  if print_args and not kwargs == {}:
    call_string += " " + str(kwargs)[:MAX_PRINT_VALS]

  # Print if there is no return
  if no_return:
    PRINT_LOCK.acquire()
    print call_string
    PRINT_LOCK.release()

  # Get the result
  try:
    result = func(*args,**kwargs)

  # On an exception, print the call at least
  except Exception, e:
    PRINT_LOCK.acquire()
    print call_string,"->",str(e)
    PRINT_LOCK.release()
    raise

  # Return if there is no result
  if no_return:
    return

  # Lock to print
  if print_result:
    str_result = str(result)
    if len(str_result) > MAX_PRINT_VALS:
      str_result = str_result[:MAX_PRINT_VALS] + "..."
    call_string += " = " + str_result

  PRINT_LOCK.acquire()
  print call_string
  PRINT_LOCK.release()

  return result


# This class is used for API calls that don't return objects
class NonObjAPICall():
  # Initialize with the name of the call
  def __init__(self, name):
    self.name = name
    self.func = _context[name]

  # This method will be called by sub-namespaces
  def call(self,*args,**kwargs):
    # Trace the call
    return traced_call(None,self.name,self.func,args,kwargs)



# This class is used for socket objects
class SocketObj():
  # Store the socket object
  def __init__(self,sock):
    self.sock = sock

  # Emulate the other functions
  def close(self,*args,**kwargs):
    return traced_call(self.sock,"socket.close",self.sock.close,args,kwargs)

  def recv(self,*args,**kwargs):
    return traced_call(self.sock,"socket.recv",self.sock.recv,args,kwargs)

  def send(self,*args,**kwargs):
    return traced_call(self.sock,"socket.send",self.sock.send,args,kwargs)

  def willblock(self,*args,**kwargs):
    return traced_call(self.sock,"socket.willblock",self.sock.willblock,args,kwargs)


# This class is used for lock objects
class LockObj():
  # Store the lock object
  def __init__(self,lock):
    self.lock = lock

  # Emulate the functions
  def acquire(self, *args,**kwargs):
    return traced_call(self.lock,"lock.acquire",self.lock.acquire,args,kwargs)

  def release(self, *args, **kwargs):
    return traced_call(self.lock,"lock.release",self.lock.release,args,kwargs,True)


# This class is used for file objects
class FileObj():
  # Store the file object
  def __init__(self,fileo):
    self.fileo = fileo

  # Emulate the functions
  def close(self,*args,**kwargs):
    return traced_call(self.fileo,"file.close",self.fileo.close,args,kwargs,True)

  def flush(self,*args,**kwargs):
    return traced_call(self.fileo,"file.flush",self.fileo.flush,args,kwargs,True)

  def next(self,*args,**kwargs):
    return traced_call(self.fileo,"file.next",self.fileo.next,args,kwargs)

  def read(self,*args,**kwargs):
    return traced_call(self.fileo,"file.read",self.fileo.read,args,kwargs)

  def readline(self,*args,**kwargs):
    return traced_call(self.fileo,"file.readline",self.fileo.readline,args,kwargs)

  def readlines(self,*args,**kwargs):
    return traced_call(self.fileo,"file.readlines",self.fileo.readlines,args,kwargs)

  def seek(self,*args,**kwargs):
    return traced_call(self.fileo,"file.seek",self.fileo.seek,args,kwargs,True)

  def write(self,*args,**kwargs):
    return traced_call(self.fileo,"file.write",self.fileo.write,args,kwargs,True)

  def writelines(self,*args,**kwargs):
    return traced_call(self.fileo,"file.writelines",self.fileo.writelines,args,kwargs,True)


class VNObj():
  # Store the virt object
  def __init__(self,virt):
    self.virt = virt

  # Emulate the functions
  def evaluate(self,*args,**kwargs):
    return traced_call(self.virt,"VirtualNamespace.evaluate",self.virt.evaluate,args,kwargs,print_args=False,print_result=False)


# Wrap the call to openconn
def wrapped_openconn(*args, **kwargs):
  # Trace the call
  sock = traced_call(None,"openconn",openconn,args,kwargs)

  # Wrap the socket object
  return SocketObj(sock)

# Wrap the call to waitforconn
def wrapped_waitforconn(*args, **kwargs):
  # Get the callback function
  try:
    callback = args[2]

  # If the user input is bad, then waitforconn is going to get angry anyways...
  except:
    callback = None

  # Create a wrapper function
  def _wrapped_callback(*args,**kwargs):
    # Wrap the socket
    socket = SocketObj(args[2])

    # Use the new wrapped socket
    args = args[0:2] + (socket,) + args[3:]
    
    # Call the user callback
    traced_call(callback, "new incoming conn.",callback,args,kwargs,True)

  # Call down
  args = args[0:2] + (_wrapped_callback,)
  return traced_call(None,"waitforconn",waitforconn,args,kwargs)


# Wrap the call to recvmess
def wrapped_recvmess(*args,**kwargs):
  # Get the callback function
  try:
    callback = args[2]
  except:
    callback = None

  # Create a wrapper around this
  def _wrapped_callback(*args,**kwargs):
    # Trace the call
    traced_call(callback, "new incoming mess.",callback,args,kwargs,True)

  # Call down to recvmess
  args = args[0:2] + (_wrapped_callback,)
  return traced_call(None,"recvmess",recvmess,args,kwargs)


# Wrap the call to getlock
def wrapped_getlock(*args,**kwargs):
  # Trace the call to get the lock
  lock = traced_call(None,"getlock",getlock,args,kwargs)

  # Return the wrapped lock
  return LockObj(lock)

# Wrap the call to open
def wrapped_open(*args,**kwargs):
  # Trace the call to get the file object
  fileo = traced_call(None,"open",open,args,kwargs)

  # Return the wrapped object
  return FileObj(fileo)


# Wrap the call to VirtualNamespace
def wrapped_virtual_namespace(*args,**kwargs):
  # Trace the call to get the object
  return VNObj(traced_call(None,"VirtualNamespace(...)",VirtualNamespace,args,kwargs,print_args=False))


# Wrap all the API calls so they can be traced
def wrap_all():
  # Handle the normal calls
  for call in NON_OBJ_API_CALLS:
    CHILD_CONTEXT[call] = NonObjAPICall(call).call

  # Wrap openconn
  CHILD_CONTEXT["openconn"] = wrapped_openconn

  # Wrap waitforconn
  CHILD_CONTEXT["waitforconn"] = wrapped_waitforconn

  # Wrap recvmess
  CHILD_CONTEXT["recvmess"] = wrapped_recvmess

  # Wrap getlock
  CHILD_CONTEXT["getlock"] = wrapped_getlock

  # Wrap open
  CHILD_CONTEXT["open"] = wrapped_open

  # Wrap VirtualNamespace
  CHILD_CONTEXT["VirtualNamespace"] = wrapped_virtual_namespace


# If we are supposed to run, wrap all the functions
if callfunc == "initialize":
  wrap_all()

  # Print the header
  print "Call-time function [instance] [args] [ = result ]"


# Dylink specific
if "HAS_DYLINK" in _context and HAS_DYLINK:
  dy_dispatch_module()


