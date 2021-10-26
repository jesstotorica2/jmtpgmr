import sys

class ByteStreamBlk:
  """
  Structure for holding bytestream generated from file
  Bytestream structure: (A = address byte, C = bytecount byte, D = data byte)
     [  AAAA CCCC DDDDDD..... | |  AAAA CCCC DDDDDD..... | ....  ]
     |       Section 0        | |      Section 1         | ....

  """
  def __init__(self, no_abytes=4, no_cntbytes=4):
    # Byte stream config params
    self.MEM_WIDTH         = 1            # Memory byte width (NOTE: dont change, hex file always provides a byte address)
    self.NUM_ADDR_BYTES    = no_abytes    # Number of address bytes
    self.NUM_BYTECNT_BYTES = no_cntbytes  # Number of byte count bytes

    # Byte stream class data
    self._start_addr   = [] # Start address array for each starting address in bytestream [A0 C0 DDDD....A1 C1 DDDD....]
    self._dbyte_count  = [] # Data byte count array for each section of the bytestream
    self._dbyte_ptr    = [] # Pointer first data byte for each section
    self.sect_idx      = 0  # Bytestream section index
    self.stream_started = False

    # Data for user
    self.start_addr     = 0  # Bytestream initial address start
    self.byte_count     = 0  # Bytestream total bytes (Address bytes + count bytes + data bytes)
    self.dbyte_count    = 0  # Bytestream total data byte count
    self.section_count  = 1  # Bytestream section count
    self.bytestream  = bytearray()
  
  # add_dbyte
  # 
  # Adds a data byte to stream, assumes address is consecutive
  #
  def add_dbyte(self, byteval): 
    self._dbyte_count[self.sect_idx] += 1
    self.byte_count += 1
    self.dbyte_count += 1
    self._update_bytecnt_bytes()
    self.bytestream.append( (byteval & 0xff) )
  
  # add_dbyte_at_addr
  #
  # Adds a data byte to stream for specified address. 
  # If Address is not consecutive to current section, new section is started
  #
  def add_dbyte_at_addr(self, byteval, addr):
    if( not self.stream_started ):
      self._start_new_section(addr)
    else:
      cur_addr = (int(self._dbyte_count[self.sect_idx]/self.MEM_WIDTH) + self._start_addr[self.sect_idx])
      if( cur_addr < addr ):
        self._start_new_section(addr)
    self.add_dbyte(byteval)


  # cmp_section
  #
  # Compares a given bytearray() to given section of blk bytestream
  #
  def cmp_section(self, sect_idx, bdata) -> int:
    fail_idx = -1
    
    if( len(bdata) != self._dbyte_count[sect_idx] ):
      return -2

    for i in range(self._dbyte_count[sect_idx]):
      if( bdata[i] != self.bytestream[self._dbyte_ptr[sect_idx] + i] ):
        fail_idx = i
        break

    return fail_idx

  # get_section
  #
  # Returns data byte array of section for given index
  #
  def get_section(self, sect_idx):
    section = bytearray();
    for i in range(self._dbyte_cnt[sect_idx]):
      section.append( self.bytestream[self._dbyte_ptr[sect_idx] + i] )
  
    return section


  def _update_bytecnt_bytes(self):
    cur_bcnt_ptr = (self.byte_count - self._dbyte_count[self.sect_idx] - self.NUM_BYTECNT_BYTES) # Index of current bytecnt bytes
    #print( "byte_count: {bc}, dbyte_count[{idx}]: {dbc}, cur_bcnt_ptr: {cbp}".format(bc=self.byte_count, idx=self.sect_idx, dbc=self._dbyte_count[self.sect_idx], cbp=cur_bcnt_ptr ))
    for i in range(self.NUM_BYTECNT_BYTES):
      self.bytestream[cur_bcnt_ptr+i] = ( (self._dbyte_count[self.sect_idx] >>(8*(self.NUM_BYTECNT_BYTES-i-1))) & 0xff )
  
  def _start_new_section(self, addr):
    if( self.stream_started ):
      self.sect_idx += 1
      self.section_count += 1
    else:
      self.stream_started= True 
    
    self._dbyte_count.append(0)
    self._start_addr.append(addr)
    for i in range(self.NUM_ADDR_BYTES+self.NUM_BYTECNT_BYTES):
      self.bytestream.append(0)
      if( i < self.NUM_ADDR_BYTES ):
        self.bytestream[self.byte_count+i] = ( (addr >>(8*(self.NUM_ADDR_BYTES-i-1))) & 0xff )
        #print("Addr {x}: {v}".format(x=self.byte_count+i,v=hex(self.bytestream[self.byte_count+i])))
    self.byte_count += self.NUM_ADDR_BYTES + self.NUM_BYTECNT_BYTES 
    self._dbyte_ptr.append(self.byte_count)




#=======================================================================================================
# Hex Processor
#=======================================================================================================
class HexProcessor:
  """
  Class for processing hex file
  """
  def __init__(self):
    self.TXNBYTESTRM_MAX_SIZE = 512
    self.PAGE_BYTE_SIZE   = 128

  def get_bytestream(self, fpath):
    fo = open(fpath,"r")            # Get file object
    fd = fo.read()                  # Get file data as string
    lineno = 0
    #print(fd)
    bstrms = []
    bstrms.append(ByteStreamBlk())
    bstrm_idx = 0
    
     
    for line in fd.splitlines(): 
      if( not self._check_sum(line) ):
        print("Checksum not equal to zero on line {lineno} of file'{file}'".format(lineno=lineno,file=fpath))
        exit(0)

              
      b_idx = 0
      for b in self._get_data_val(line):  
        if(bstrms[bstrm_idx].dbyte_count >= self.TXNBYTESTRM_MAX_SIZE):
          bstrm_idx += 1
          bstrms.append(ByteStreamBlk())
          bstrms[bstrm_idx].add_dbyte_at_addr(b, b_idx + self._get_addr(line))
        else:  
          if(b_idx == 0):
            bstrms[bstrm_idx].add_dbyte_at_addr(b, self._get_addr(line))
          else:
            bstrms[bstrm_idx].add_dbyte(b)
          b_idx += 1

      lineno +=  1
    
    return bstrms

  def _get_bytecount(self, line):
    if( line[1:3] == '' ):
      print("blank bytecount: %s"%line)
      return 0
    return int(line[1:3], 16)

  def _get_addr(self, line):
    return int(line[3:7], 16)

  def _get_record(self, line):
    val = int(line[7:9], 16)
    if( val == 0 ):
      return "DATA"
    elif( val == 1 ):
      return "EOF"
    else:
      print("None DATA/EOF record type encountered. RECORD TYPE: ",val)
      return ""

  def _check_sum(self, line) -> bool:
    csum = 0
    for i in range(0,int(len(line)/2)):
      if(line[i] == ' ' or line[i] == '\n' or line[i] == ''):
        break
      #print( line[i*2+1:i*2+3], end=' ' )
      csum += (int(line[i*2+1:i*2+3],16))
      csum = ( csum & 0xFF )
    return( csum == 0 )

  def _get_data_str(self, line):
    data_str = ""
    data_str_arr = []
    bytecount = self._get_bytecount(line)
    data_str = line[9:(9+bytecount*2)]
    for i in range(bytecount):
      data_str_arr.append(data_str[(i*2):(i*2+2)])
    return data_str_arr


  def _get_data_val(self, line):
    data_str = self._get_data_str(line)
    data_val = []
    for byte_str in data_str:
      data_val.append(int(byte_str,16))
    return data_val

  def _print_C_hex_array(self, fin_str,fout_str=""):
    fin = open(fin_str)
    C_hex_array = "{"
    blen = 0
    for line in f.read().splitlines():
      for hex_val in get_data_str(line):
             C_hex_array += "0x"
             C_hex_array += hex_val
             C_hex_array += ","
             blen+=1
    C_hex_array = C_hex_array[0:-1]+"}"

    if( fout_str == "" ):
      print(C_hex_array)
      print("Total Byte Length: ",blen)


"""
b = ByteStreamBlk()
b.add_dbyte_at_addr(0xab, 0x12)
b.add_dbyte(0xbc)
b.add_dbyte_at_addr(0xcd, 0x22)
b.add_dbyte_at_addr(0x1F, 0x00)
for i in range(len(b.bytestream)):
  print("{i}: {b}".format(i=i,b=hex(b.bytestream[i])))
"""
"""
hx = HexProcessor()
#b = hx.get_bytestream("../../../../atmega_BT_programmer/sw_dev/Python/test/test.hex")
b = hx.get_bytestream("test.hex")
for i in range(len(b[0].bytestream)):
  pass
	#if i < 48:
  #  print("{i}: {b}".format(i=i,b=hex(b[0].bytestream[i])))
"""
