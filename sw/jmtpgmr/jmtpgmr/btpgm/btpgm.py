"""

  btpgm.py

"""

import sys
import time
import traceback

import bluetooth
import os
import re
from .myTerm import myTerm
from .hexprocessor import HexProcessor
from .jmtpgmrerr import *


import time
from threading import Thread, Event

class BTprogrammer:
  """
  Bluetooth uC programming class
  """
  def __init__(self, **kwargs):
    self.btsock = None
    self.btconnected = False
  
    #
    self.recv_size = 1024
    self.port = 1
    self.pkt_dbyte_size = 512 #TODO make configurable
    self.read_reattempts = 5

    #  
    self.debug = False
    
    # 
    self.pgm_size = 0

    # Percent bar settings
    self.pbar_len = 50
    self.pbar_sym = "$"

    if kwargs:
      pass #TODO make warning
  
    # Create bluetooth socket
    self.err_h = jmtpgmrerr()    
    self.btsock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
  

  #=============================================================================
  #
  # Bluetooth Program
  #
  #=============================================================================
  

  #
  #	btpgm()
  #
  #
  #	Args: Input hexfile path, target device bt address 
  #
  def btpgm(self,infile,target,**kwargs):
    hx = HexProcessor()
    bstrm_blks = []
    verify  = False
    echo    = False
    eesave  = None

    # kwargs    
    for key, val in kwargs.items():
      if  ( key == 'debug'  ):   self.debug = val
      elif( key == 'verify' ):   verify = val
      elif( key == 'echo'   ):   echo = val
      elif( key == 'eesave'   ): eesave = val

    pgm_st_time = time.time()
    print()
    # Verify file exist
    if( infile != None ):
        if( not os.path.exists(infile) ):
          self._btpgm_exit( ("File '{}' not found!\n".format(infile)) )
        else:
          print("Creating bytestream from hex file...")
          bstrm_blks = hx.get_bytestream(infile)
          self._print_green("Bytestream created!")
          self.pgm_size = 0
          for blk in bstrm_blks:
            self.pgm_size += blk.dbyte_count
          print("Program Size: {} bytes\n".format(self.pgm_size))

    
    # Attempt to connect to device
    try: 
      print("Attempting to connect to bluetooth device...")
      self.btsock.connect((target, self.port))
      self.btconnected = True
      self._print_green("Bluetooth connected!")
    except:
      print( traceback.format_exc() )
      self._btpgm_exit("Bluetooth connection attempt to device address '{}' failed!".format(target))
  
    #self._send_cmd("ECHO=0\r\n","OK\r\n")
    
    # Program fuse bits if requested
    if( eesave != None ):
        print("eesave: {}".format(eesave))
        self._set_eesave(eesave)

    # Program target
    if( infile != None ): 
        self._init_program_request()    
        
        self._flash_pmem(bstrm_blks)
        if( verify ):
          self._verify(bstrm_blks)
        
    self._end_program_mode()
    
    self._print_green("\nDevice Programming Complete!")
    print("Total programming time: {} s\n".format(round(time.time()-pgm_st_time,3)))
    
    if( echo ):  
      self.echo(target)

    self.btsock.close()
  


  #
  #	_init_program_request()
  #
  #  
  #	Initialize program request
  def _init_program_request(self):
    pgm_req_cmd = "PGM={pkt_size},{verify}\r\n".format(pkt_size=self.pkt_dbyte_size, verify=0)     
    success_resp = "OK\r\n"

    # Send Command 
    self._send_cmd(pgm_req_cmd, success_resp)
  
  #
  # _set_eesave()
  #
  def _set_eesave(self, enable):
    set_eesave_cmd="EESAVE={}\r\n".format("1" if enable else "0" )
    success_resp = "OK\r\n"
    self._send_cmd(set_eesave_cmd, success_resp)

  #
  #	_flash_pmem()
  #
  #	Flash bytestream data to Program memory
  def _flash_pmem(self, bstrm_blks):
    success_resp = "OK\r\n"
    resp = ""
    bytes_flashed = 0
    
    print("\nWriting to program memory...\n\n"+self._percent_bar(0), end="")
    st_time = time.time()
    for blk in bstrm_blks:
      blk_start_t = time.time()
      flash_cmd = "FLASH={blen}\r\n".format(blen=blk.byte_count) 
      
      # Send Command 
      self._send_cmd(flash_cmd, success_resp)

      if( self._send(blk.bytestream) ):
        resp = self._get_resp()
        if( self.debug ):
          print("Bytestream block write time: {} s".format(round((time.time() - blk_start_t),2)))
      else:
        self._btpgm_exit("Failed to send byte stream data through BT socket.")
    
      if( success_resp not in resp ):
        if( self.err_h.is_err_resp(resp) ):
          err_val = self.err_h.parse_err_val(resp)
          self._btpgm_exit(self.err_h.get_err_str(err_val))
        else:
          self._btpgm_exit( "Unexpected response during bytestream flash:\r\n{}".format(self._format_resp(resp)) )
      else:
        bytes_flashed += blk.dbyte_count
        print(self._percent_bar((100*bytes_flashed/self.pgm_size)), end="")
    self._print_green("\nWrite Done!")  
    print("Write time: {} s".format(round(time.time() - st_time, 3)))

  #
  # _verify()
  #
  # Verify byte stream was correctly flashed to program memory
  def _verify(self, bstrm_blks):
    success_resp = "OK\r\n"
    match = True
    fail_idx = 0
    fail_addr = 0
    bytes_read = 0

    print("\nReading Program Memory...\n\n"+self._percent_bar(0), end="")
    st_time = time.time()
    for blk in bstrm_blks:
      for sect in range(blk.section_count):
        for attempt in range( self.read_reattempts ):
            blk_start_t = time.time()
            # Read section
            read_cmd = "READ={baddr},{blen}\r\n".format(baddr=blk._start_addr[sect], blen=blk._dbyte_count[sect])
            self._send_cmd(read_cmd, success_resp)

            # Get byte data
            rd_data = self._get_bdata_resp(blk._dbyte_count[sect])
            if( self.debug ):
              print("Block section readback time: {} s".format(round((time.time() - blk_start_t),2)))

            # Compare to write data
            fail_idx = blk.cmp_section(sect, rd_data)
            if( fail_idx != -1 ):
              match = False
              if( fail_idx == -2 ):
                self._btpgm_exit(
                  "During verification, bytestream read was not the same length as the bytestream written.\n"
                  "Write byte length: {wlen}\n"
                  "Read byte length: {rlen}".format(wlen=blk._dbyte_count[sect],rlen=len(rd_data))
                )
              else:
                fail_addr = blk._start_addr[sect] + fail_idx
                if( attempt >= (self.read_reattempts-1) ):
                    self._btpgm_exit(
                      "Byte read did not match byte written!\n"
                      "Byte address: {baddr}\n"
                      "Write Data: {wdata}\nRead Data: {rdata}".format(
                         baddr=fail_addr,
                         wdata=hex(blk.bytestream[blk._dbyte_ptr[sect]+fail_idx]),
                         rdata=hex(rd_data[fail_idx])
                      )
                    )
            else:
              bytes_read += blk._dbyte_count[sect]
              print(self._percent_bar((100*bytes_read/self.pgm_size)), end="")
              break

    self._print_green("\nProgram verified!") 
    print("Read time: {} s".format(round(time.time() - st_time, 3)))

  #
  # _end_program_mode()
  #
  #
  # Sends command to programmer to end programming mode and release target device
  def _end_program_mode(self):
    end_cmd = "END\r\n"
    success_resp = "OK\r\n"
    self._send_cmd(end_cmd, success_resp)

  #=============================================================================
  #
  # Echo Interface
  #
  #=============================================================================
  
  #
  # echo
  #
  #
  # Echo command.
  def echo(self,target,**kwargs):
    already_connected = False

    # kwargs
    for key, val in kwargs.items():
      pass
      #if( key == 'verify' ): self.verify = val
      #if( key == 'debug'  ): self.debug = val

    if( not self.btconnected ):
      self.btsock.connect((target, self.port))
      self.btconnected = True
    else:
      already_connected = True

    self._send_cmd("ECHO=0\r\n","OK\r\n")
    # Start echo mode 
    self._send_cmd("ECHO=1\r\n","OK\r\n")
    
    # Create terminal interface
    term = myTerm()
   
    #self.btsock.settimeout(.01)
    self.btsock.setblocking(False)
    
    # Start term
    old_dbg = self.debug
    self.debug = False # set false to avoid printing issues
    term.start_term()
    
    while( not term.exit_req ):
      # Run terminal output
      term.eval()

      # Send data available?
      if( term.line_count > 0 ):
        self._send(term.get_line())

      # Get bluetooth data
      try:  
        c = self.btsock.recv(1).decode()
        term.output(c)
      except:
        pass

    # End term
    term.end_term()
    self.debug = old_dbg
    
    # End echo mode 
    self._send_cmd("ECHO=0\r\n","OK\r\n")
   
    # Close BT if not connected coming in
    if( not already_connected ):
      self.btsock.close()

  #=============================================================================
  #
  # Common
  #
  #=============================================================================

  #
  #	_send_cmd()
  #
  #	Sends a 'JMT+' command to bluetooth device and retrieves response.
  # Returns response string
  def _send_cmd(self,cmd, success_resp) -> str:
    resp = ""
    # Send cmd
    if( self._send("JMT+"+cmd) ):
      time.sleep(0.050)
      resp = self._get_resp()
    else:
      self._btpgm_exit("Failed to send data through BT socket.")
    
    # Check response
    if( success_resp in resp ):
      return resp
    elif( self.err_h.is_err_resp(resp) ):
      err_val = self.err_h.parse_err_val(resp)
      self._btpgm_exit(self.err_h.get_err_str(err_val))
    else:
      self._btpgm_exit("Unrecognized response from programmer:\r\n{}".format(self._format_resp(resp)))

  #
  #	_send()
  #
  #
  #	Transmits data to bluetooth device
  def _send(self, data) -> bool:
    if( isinstance(data, bytearray) ):
      bdata = data
    else:
      bdata = data.encode()
      
    success = False
    self.btsock.setblocking( True )
    if( self.btconnected ):
      try:
        if( self.debug and not isinstance(data, bytearray)):
          print("Sending:\n{}\n".format(self._format_resp(data)))
        self.btsock.send(bdata)
        success = True
      except Exception as e:
        success = False
    return success

  #
  #	_get_resp()
  #
  #	Retrieves a response from bluetooth device returns string.
  def _get_resp(self, resp_end="\r\n\r\n", timeout=10) -> str:
    resp_data = ""
    token_len = len(resp_end)
    token_found = False


    self.btsock.settimeout( 1 ) # Check back from 'recv' every 1s if no data has been recieved
    st_time = time.time()
    timed_out = False

    while( (not timed_out) and (not token_found) ):
      try:
        resp_data += self.btsock.recv(1).decode()
      except TimeoutError:
        pass
      except:
        print( traceback.format_exc() )
        self._btpgm_exit( "Exception occurred during recv()" )
      token_found = (resp_end in resp_data[(-3-token_len):]) # Trying to prevent from seaching entire string each byte!
      timed_out = ((time.time() - st_time) > timeout)

    if( timed_out ):
      resp_err = "Bluetooth timeout!\n"
      if( resp_data == "" ):
        resp_err += ("No response from programmer!")
      else:
        resp_err += ( "Token '{}' not found. Response data:\n{}\n".format(
                      re.sub( "\r\n", "{\\r}{\\n}", resp ),
                      self._format_resp(resp_data))
        )
      self._btpgm_exit( resp_err )

    if( self.debug ):
      print( "Device Response:\n{}\n".format( self._format_resp(resp_data)) )

    return resp_data
 
  #
  # _get_bdata_resp()
  #
  # Retrieves byte data from a response
  def _get_bdata_resp(self, blen, timeout=10000):
    resp_data = bytearray()
    recv_blen = 0

    self.btsock.settimeout( 1 ) # Check back every 1 seconds
    st_time = time.time()
    timed_out = False

    while( (not timed_out) and recv_blen < blen ):
      try:
        recv_data = self.btsock.recv(1)
        recv_blen += len(recv_data)
        resp_data += recv_data
      except TimeoutError:
        pass
      except:
        print( traceback.format_exc() )
        self._btpgm_exit( "Exception occurred during recv()" )

      timed_out = ((time.time() - st_time) > timeout)

    if( timed_out ):
      resp_err = "Bluetooth timeout!\n"
      if( recv_blen == 0 ):
          resp_err += ("No byte data received from programmer!")
      else:
          resp_err += ( "Did not receive {blen} bytes before timeout. Response data:\n"
                        "{bdata}\n".format( blen=recv_blen, bdata=self._format_resp(resp_data) )
                      )
      self._btpgm_exit(resp_err)

    if( self.debug ):
      print( "Device Response:\n{}\n".format(self._format_resp(resp_data)) )

    return resp_data


  #
  #	_format_resp()
  #
  #
  #	Formats	a response from bluetooth device. Prints blue.
  def _format_resp(self, resp) -> str:
    resp_str = ""
    re.sub( "\r\n", "{\\r}{\\n}\r\n", resp )
    if( isinstance(resp, bytearray) ):
      resp_str = ""
      for i in range(len(resp)):
        byte_hex_str = str(hex(resp[i]))
        resp_str += "{}0 ".format(byte_hex_str) if(len(byte_hex_str) < 4) else "{} ".format(byte_hex_str)
        resp_str += "\n" if((i+1)%16 == 0) else ""
    else:
      resp_str = resp
    resp_str = re.sub("\n","\n\033[0;37m#\033[0;34m ",resp_str) 
    return "#\033[0;34m " + resp_str + "\033[0;37m"


  #
  # _btpgm_exit()
  #
  #
  # Prints error and exits program
  def _btpgm_exit(self, p_err):
    print("\033[0;31m\nERROR:\033[0;97m	" + p_err)
    if( self.btconnected ):
      print("Closing bluetooth connection...")
      self.btsock.close()
    print("Exiting...")
    exit(0)

  #
  # _print_green()
  #
  #
  # Print in green
  def _print_green(self, data_str):
    print("\033[0;32m"+data_str+"\033[0;97m")

  #
  #	_percent_bar()
  #
  #
  # Returns string for percent bar
  def _percent_bar(self, pval, pb_len=0, symbol='') -> str:
    if( self.debug ):
      return ""
    pbar_str = "\r"
    pb_len = (self.pbar_len) if(pb_len <= 0 ) else (pb_len)
    symbol = (self.pbar_sym) if(symbol == '') else (symbol)
    
    for i in range(pb_len):
      if( (((i+1)/pb_len)*100) <= pval ): pbar_str += symbol[(i%len(symbol))]
      else:                               pbar_str += " "                                

    pval = round(pval, 2)
    pbar_str += "| {}%  ".format(pval)
    return pbar_str




