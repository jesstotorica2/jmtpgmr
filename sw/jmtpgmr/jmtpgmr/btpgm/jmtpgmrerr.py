

# Errors

ERR_MACRO=0
ERR_DESC=1

ERR_PREFIX = "ERROR("
ERR_SUFFIX = ")"


err_dict = {
	
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

}  

#
# get_err_str
#
# Returns string with error macro and description
def get_err_str(errval: int):
  if( errval in err_dict.keys() ):
    err_info = err_dict[errval]
    return( err_info[ERR_MACRO] + ": " + err_info[ERR_DESC] )    
  
  else:
    return( "Unrecognized error code: {}".format(errval) )

#
# parse_err_val
#
# Returns error code value from error string
def parse_err_val(errstr: str):
  err_pre_idx = errstr.index(ERR_PREFIX) + len(ERR_PREFIX)
  errstr = errstr[err_pre_idx:]
  errstr = errstr[0:errstr.index(")")]
  try:
    return(int(errstr))
  except:
    return(errstr)

#
# is_err_resp
#
def is_err_resp(resp: str):
  return(ERR_PREFIX in resp)









