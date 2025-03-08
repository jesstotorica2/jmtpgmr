"""

  wifisock.py

"""

import socket

class WifiSock(socket.socket):
  """
  Wifi Socket for jmtpgm
  """
  def __init__(self, host_ip : str, **kwargs):
    super().__init__( socket.AF_INET, socket.SOCK_STREAM )
    self.host_ip = host_ip
    self.port = 69
    #
    #self.recv_size = 1024
    #self.port = 1
    #self.pkt_dbyte_size = 512 #TODO make configurable
    #self.read_reattempts = 5

    ##  
    #self.debug = False
    
  def connect(self):
    prev_timeout = super().gettimeout()
    super().settimeout( 10 )
    super().connect( (self.host_ip, self.port) )
    super().settimeout( prev_timeout )

  
