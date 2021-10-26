/*

	btprogrammer.h

	Macros and prototypes for btprogrammer
*/

// Includes
#include "mystdlib.h"
#include "myUART.h"
#include "mySPI.h"
#include "myTimer.h"
#include "hc05.h"
#include "myIO.h"
#include "atmega328_pgm.h"
#include "uartxspi.h"

//==============================
// Macros

// HC-05
#define BT_BAUD_RATE 						115200
#define BT_EN_PIN								7

#define RBUF_SIZE    						600

#define SPI_MOSI								11
#define SPI_MISO								12
#define SPI_SCK									13
#define SPI_SS									10

#define BT_CMD_LISTEN_TIMEOUT		20
#define BT_WAIT_CONNECT_TIMEOUT 30

// Commands
#define JMT_ERROR    -1        

#define JMT_PGM       0		// Start programming mode (puts target device into programming mode)
#define JMT_FLASH     1		// Flashes data to program memory
#define JMT_READ			2		// Reads data from program memory
#define JMT_END				3		// End programming mode (releases target reset)

#define JMT_ECHO			4		// Echos data sent from target device over bluetooth

// Byte Stream
#define MAX_PKT_SIZE 600
#define ADDR_BYTES   4
#define LEN_BYTES    4
#define HEADER_BYTES 8 //ADDR_BYTES+LEN_BYTES

// Programmer
#define SLV_RESET 					6
#define PGM_START_ATTEMPTS	2


// Errors
#define JMT_INVALID_CMD										0		// Invalid command

#define JMT_PGM_INVALID_ARGS							1		// Invalid argument syntax(non-int) or count
#define JMT_PGM_TRGT_RESP									2		// Invalid response from target device
#define JMT_PGM_EXCEEDS_MAX_PKTSIZE     	3   // Proposed packet size exceed programmers buffer size 

#define JMT_FLASH_NOT_PGM_MODE						4 	// Program mode not started while attempting flash
#define JMT_FLASH_INVALID_ARGS						5		// Incorrect number of arguments or invalid arguments provided	
#define JMT_FLASH_INVALID_BLEN						6 	// Invalid byte stream length, length was less than no. of header bytes
#define JMT_FLASH_EXCEEDS_MAX_PKTSIZE			7   // Stream raw byte lentgth is greater than max packet size + header bytes
#define JMT_FLASH_TRGT_RESP								8 	// During block flash, an invalid transaction took place 

#define JMT_READ_INVALID_ARGS							9		// Incorrect number of arguments or invalid arguments provided	
#define JMT_READ_NOT_PGM_MODE						 10 	// Program mode not started while attempting pmem read
#define JMT_READ_ARGVAL									 11		// Byte length or byte address has negative value
#define JMT_READ_TRGT_RESP							 12 	// During memory read, an invalid transaction took place with target

#define JMT_END_ARGS										 13	 	// Number of arguments given with 'END' command did not equal zero.

#define JMT_ECHO_ARGS										 14   // Number of arguments provided with 'ECHO' command was not equal to one.

//#define JMT

// Typedefs
typedef char rbuf_t;

//==============================
// Prototypes
void sys_init();
void wait_connect();
int  get_cmd(char** args);
void run_cmd(int cmd, char* args);
void print_succ(const char* msg = nullptr);
void print_err(int err);

// Commands
void jmt_pgm(int pkt_size, int verify);
void jmt_flash(int stream_blen); 
void jmt_read(int baddr, int blen);
void jmt_end();
void jmt_echo(int begin);


// Helper Functions
void fill_arg_vals(int* vals, int* num_vals, char** args, int max_vals);
bool get_arg_int(char** args, int* val);
bool substrcmp(char* str, char* end, const char* val);
bool has_str(char* str, const char* sub);
bool str_is_int(char* str);
uint16_t buf_byte_to_uint(int st, int len);
bool bt_listen_timeout();

