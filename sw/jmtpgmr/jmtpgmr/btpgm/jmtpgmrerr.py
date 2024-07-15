
class jmtpgmrerr:
  # Errors

  def __init__(self):
    self.ERR_MACRO=0
    self.ERR_DESC=1

    self.ERR_PREFIX = "ERROR("
    self.ERR_SUFFIX = ")"

    
    self.err_dict = {
      
         0: ['JMT_INVALID_CMD',                 "Invalid command"],
          
         1: ['JMT_PGM_INVALID_ARGS',            "Invalid argument syntax(non-int) or count"],
         2: ['JMT_PGM_TRGT_RESP',               "Invalid response from target device"],
         3: ['JMT_PGM_EXCEEDS_MAX_PKTSIZE',     "Proposed packet size exceed programmers buffer size"], 
          
         4: ['JMT_FLASH_NOT_PGM_MODE',          "Program mode not started while attempting flash"],
         5: ['JMT_FLASH_INVALID_ARGS',          "Incorrect number of arguments or invalid arguments provided"],  
         6: ['JMT_FLASH_INVALID_BLEN',          "Invalid byte stream length, length was less than no. of header bytes"],
         7: ['JMT_FLASH_EXCEEDS_MAX_PKTSIZE',   "Stream raw byte lentgth is greater than max packet size + header bytes"],
         8: ['JMT_FLASH_TRGT_RESP',             "During block flash, an invalid transaction took place"], 
          
         9: ['JMT_READ_INVALID_ARGS',           "Incorrect number of arguments or invalid arguments provided"],  
        10: ['JMT_READ_NOT_PGM_MODE',           "Program mode not started while attempting pmem read"],
        11: ['JMT_READ_ARGVAL',                 "Byte length or byte address has negative value"],
        12: ['JMT_READ_TRGT_RESP',              "During memory read, an invalid transaction took place with target"],
          
        13: ['JMT_END_ARGS',                    "Number of arguments given with end command did not equal zero."],
        14: ['JMT_ECHO_ARGS',                   "Number of arguments provided with 'ECHO' command was not equal to one."],
        15: ['JMT_EESAVE_ARGS',                 "Number of arguments provided with 'EESAVE' command was not equal to one."],
        16: ['JMT_NO_DEVICE',                   "No target device detected"],

    }  

  #
  # get_err_str
  #
  # Returns string with error macro and description
  def get_err_str(self, errval: int):
    if( errval in self.err_dict.keys() ):
      err_info = self.err_dict[errval]
      return( err_info[self.ERR_MACRO] + ": " + err_info[self.ERR_DESC] )    
    
    else:
      return( "Unrecognized error code: {}".format(errval) )

  #
  # parse_err_val
  #
  # Returns error code value from error string
  def parse_err_val(self, errstr: str):
    err_pre_idx = errstr.index(self.ERR_PREFIX) + len(self.ERR_PREFIX)
    errstr = errstr[err_pre_idx:]
    errstr = errstr[0:errstr.index(")")]
    try:
      return(int(errstr))
    except:
      return(errstr)

  #
  # is_err_resp
  #
  def is_err_resp(self, resp: str):
    return(self.ERR_PREFIX in resp)









