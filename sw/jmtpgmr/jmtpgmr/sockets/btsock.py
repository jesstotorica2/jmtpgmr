"""

  btsock.py

"""

import bluetooth

class BTSock(bluetooth.BluetoothSocket):
  """
  Bluetooth Socket for jmtpgm
  """
  def __init__(self, target : str, **kwargs):
    super().__init__(bluetooth.RFCOMM)
    self.target = target
    self.port = 1
    #
    #self.recv_size = 1024
    #self.port = 1
    #self.pkt_dbyte_size = 512 #TODO make configurable
    #self.read_reattempts = 5

    ##  
    #self.debug = False
    
  def connect(self):
    super().connect( (self.target, self.port) )

  
