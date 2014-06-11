import sys, socket, select
 
#function to create raw ICMP echo request packet
def CreateICMPRequest():
    packet  = b''
    packet += b'\x08'                        #ICMP Type:8 (icmp echo request)
    packet += b'\x00'                        #Code 0 (no code)
    packet += b'\xbd\xcb'                    #Checksum
    packet += b'\x16\x4f'                    #Identifier (big endian representation)
    packet += b'\x00\x01'                    #Sequence number (big endian representation)
    packet += b'\x92\xde\xe2\x50\x00\x00\x00\x00\xe1\xe1\x0e\x00\x00\x00\x00\x00\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37'                #Data (56 bytes)
    return packet

try:        
	icmpsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
	icmpsocket.bind(('', 10000))
	icmpsocket.setblocking(0)
except socket.error:
	print "You need to be root!"
	sys.exit(0)
 
#send icmp echo request to all hosts in the hosts list
icmpsocket.connect(('8.8.8.8', 1))
icmpsocket.send(CreateICMPRequest())