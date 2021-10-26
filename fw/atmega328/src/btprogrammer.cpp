/*

	btprogrammer.cpp

*/

#include "btprogrammer.h"

//==============================
// Global variables/objects
myUART 								uart;
mySPI									spi;
Timer0								tmr0;
hc05									bt;
Atmega328_Programmer 	pgmr(&spi, &uart);
uartxspi							btxspi;
bool									bt_listen_to = false;

char 									rbuf[RBUF_SIZE];

//===========================================
//
//	main()
//
//===========================================
#define PGMR_DEBUG
int main() {
	int 	cmd;
	char* cmd_args;
	
	//_delay_ms(5000);
	sys_init();
	wait_connect();
/*
//speed test
	uart.print("connected\r\n");
	while(1)
	{
		tmr0.start();
		bt.listen(rbuf, 200);
		uart.printnum(tmr0.read()); uart.print(" ms\r\n");
	}
//
*/

	while(1)
	{
		if( bt_listen_timeout() ) // If HC-05 responds, bt might not be connected
		{	uart.print("attempting poke\r\n");
			//uart.print("\r\n");
			if( bt.poke(75) ) // Try a quick poke (75 ms)
				wait_connect();
		}
		
		// Wait for command
		cmd = get_cmd(&cmd_args);	
		run_cmd(cmd, cmd_args);
	
	}

	return 0;
}


//======================================================================================
//
//	Functions
//
//======================================================================================

//
//	sys_init()
//
//	Initialize system
void sys_init() 
{
	uart.init( BT_BAUD_RATE, 8, 1, 0 );
	spi.init( SPI_MST, SPI_DIV4, 0x0 );
	if( !bt.init( &uart, &tmr0, BT_EN_PIN, BT_BAUD_RATE ) )
	{
		while(1)
		{
			uart.print("BT_CNCT_ERR");
			_delay_ms(2000);
		}
	}
	return;	
}


//
//	wait_connect()
//
//	Start inquiry, wait for device to connect
void wait_connect() 
{
	bool connected = false;

	// Start HC-05 inquiring
	bt.inquire();

	// Clear the buffer string
	rbuf[0] = '\0';
	uart.print("rbuf before waiting: |"); uart.print(rbuf); uart.print("|\r\n");
	while( !connected ) 
	{
		// Wait for device to send an 'OK' after connection
		bt.listen(rbuf, RBUF_SIZE, "\r\n");
		// Check for 'OK' from successful connection
		connected = has_str(rbuf,"OK\r\n");
		//if(connected) {uart.print("connected with |");uart.print(rbuf);uart.print("|\r\n");}
	}
	
}


//
//	get_cmd()
//
//
int get_cmd(char** args)
{	
	char* cmd = nullptr;
	char* cmd_end = nullptr;

	// Clear the buffer string
	rbuf[0] = '\0';

	tmr0.start(); // DEBUG!!!!!!!!
	// Listen to BT module, record if there is a timeout
	bt_listen_to = !bt.listen(rbuf, RBUF_SIZE, "\r\n", BT_CMD_LISTEN_TIMEOUT);
	cmd = strstr(rbuf,"JMT+");

	// Check if prefix was found
	if(cmd == nullptr)
		return JMT_ERROR;
	else
		cmd += 4;
	
	// Additional args
	(*args) = nullptr;

	// Find command end
	if(  			(cmd_end = strstr(cmd, "=" 		)) != nullptr )	(*args) = (cmd_end + 1);
	else if(  (cmd_end = strstr(cmd, "?" 		)) != nullptr );
	else if(  (cmd_end = strstr(cmd, "\r\n" )) != nullptr );
	else
		return JMT_ERROR;


	if( substrcmp(cmd, cmd_end, "PGM") ) 		return JMT_PGM;
	if( substrcmp(cmd, cmd_end, "FLASH") ) 	return JMT_FLASH;
	if( substrcmp(cmd, cmd_end, "READ") ) 	return JMT_READ;
	if( substrcmp(cmd, cmd_end, "END") ) 		return JMT_END;
	if( substrcmp(cmd, cmd_end, "ECHO") )		return JMT_ECHO;
	else
		return JMT_ERROR;

}


//
//	run_cmd()
//
//
void run_cmd(int cmd, char* args)
{	
	int vals[3], num_vals;
	
	// Get any trailing argument values ( =a,b,c,... )
	fill_arg_vals(vals, &num_vals, &args, 3);
	
	switch(cmd) 
	{
		
		case JMT_PGM :
//			if( num_vals != 2 )  	print_err(JMT_PGM_INVALID_ARGS); // err
			if( num_vals != 2 ){  	print_err(JMT_PGM_INVALID_ARGS); uart.print("\r\n|");uart.print(rbuf);uart.print("|\r\n"); }// err
			else									jmt_pgm(vals[0],vals[1]);
			break;
		
		case JMT_FLASH:
			if		 ( !pgmr.inPgmMode() ) 		print_err(JMT_FLASH_NOT_PGM_MODE); 	// err
			else if( num_vals != 1 		 )		print_err(JMT_FLASH_INVALID_ARGS);  // err
			else														jmt_flash(vals[0]);																
			break;

		case JMT_READ:
			if		 ( !pgmr.inPgmMode() ) 		print_err(JMT_READ_NOT_PGM_MODE);  // err
			else if( num_vals != 2 		 )		print_err(JMT_READ_INVALID_ARGS);  // err
			else														jmt_read(vals[0],vals[1]);
			break;
		
		case JMT_END:
			if	( num_vals != 0	)						print_err(JMT_END_ARGS);	//err
			else														jmt_end();
			break;
	
		case JMT_ECHO:
			if	( num_vals != 1 ) 					print_err(JMT_ECHO_ARGS);	//err
			else														jmt_echo(vals[0]);
			break;

		case JMT_ERROR:
			// Disconnect from hc-05
			if( strstr(rbuf, "+DISC:SUCCESS") != nullptr )	
			{ 
				_delay_ms(10); 
				wait_connect(); 
				bt_listen_to = false;
			}
			// BT listen timeout
			else if( bt_listen_to ){uart.print("bt tout\r\n");}
			else
			{
				uart.print("in err with |"); uart.print(rbuf); uart.print("|\r\n");
				print_err(JMT_INVALID_CMD);	//err
			}
			//uart.print("exiting err\r\n");
			break;
		default:
			break;
	}
}


//
// print_succ()
//
// 
// Prints success response ending with success token (OK\r\n\r\n)
void print_succ(const char* msg)
{
	if(msg != nullptr)
	{
		bt.send(msg);
		bt.send("\r\n");
	}
		bt.send("OK\r\n\r\n");
}

//
// print_err()
//
// 
// Prints encoded error response
void print_err(int err)
{
	char num_str[5];
	itoa(err, num_str, 10);
	bt.send("ERROR(");
	bt.send(num_str);
	bt.send(")\r\n\r\n");
}

//*******************************************
//
//	Commands
//
//*******************************************


//
// jmt_pgm()
//
//	Args: [max packet size, verify programming (0 or 1)]
//	 
void jmt_pgm(int pkt_size, int verify){
	int wr_cmd;
	char* args;

	// Check pkt size 
	if( pkt_size > (RBUF_SIZE+64)) {
		print_err(JMT_PGM_EXCEEDS_MAX_PKTSIZE);
		return;
	} 
	else { // If valid pgm command, start programming
		uint8_t attempts = 0;
		while( !pgmr.inPgmMode() && attempts < PGM_START_ATTEMPTS )
		{
			pgmr.startProgrammingMode();
			attempts++;
		}
		// Erase flash if programming mode started successfully
		if( pgmr.inPgmMode() ){
			pgmr.atmegaChipErase(true); // Erase Pmem, block till action is complete
			print_succ("PGM READY");
		}
		else
			print_err(JMT_PGM_TRGT_RESP);
	}
	
	// Run programmer while in programming mode
	int err_cnt = 0;
	while( pgmr.inPgmMode() && err_cnt < 3 && !bt_listen_to ) 
	{
		// Wait for flash cmd
		wr_cmd = get_cmd(&args);
		uart.printnum(tmr0.read()); uart.print(" ms\r\n");//DEBUG!!!!!
		run_cmd(wr_cmd, args);
		if(wr_cmd == JMT_ERROR)
		{
			err_cnt++;
		}
	}

	if( err_cnt >= 3 ) pgmr.endProgrammingMode(); // If exited on programming errors

}


//
// jmt_flash()
//
// Args: [ Stream raw byte length ]
// Flashes byte stream to program memory
void jmt_flash(int stream_blen){
	uint16_t baddr;	// Note: avr int is only 16-bit, so leading two bytes will be cut off
	uint16_t blen;	// Note: avr int is only 16-bit, so leading two bytes will be cut off

	// Check stream bytelength validity
	if( stream_blen < (HEADER_BYTES) )		print_err(JMT_FLASH_INVALID_BLEN);
	else if( stream_blen > MAX_PKT_SIZE ) print_err(JMT_FLASH_EXCEEDS_MAX_PKTSIZE);
	else { // Valid bytelength
		print_succ("BSTRM READY");
		uart.printnum(tmr0.read()); uart.print(" ms\r\n");//DEBUG!!!!!

		//bt.debug=true; //DEBUG
		// Wait for bytestream
		bt_listen_to = !bt.listen(rbuf, stream_blen, nullptr, BT_CMD_LISTEN_TIMEOUT);
		
		//DEBUG
		//tmr0.start();
		
		// Iterate through sections
		for( int bidx = 0; bidx < stream_blen; ) {
			// Get byte address and dbyte count
			baddr = buf_byte_to_uint(				  0, ADDR_BYTES);
			blen = 	buf_byte_to_uint(ADDR_BYTES, LEN_BYTES);
			bidx += HEADER_BYTES;
			
			//for( int i = 0; i < blen; i++ ){ unsigned char b = rbuf[i]; uart.printnum(b,16); uart.print(" "); }
			// Ensure target device is not busy
			while( pgmr.atmegaIsBusy() );

			// Right shift byte address one to get word address. Write to program memory
			pgmr.wrPmem( (baddr>>1), (unsigned char*)(rbuf+bidx), blen);


			if( pgmr.errFlag() ){  // Check for errors during Pmem write
				bt.sendnum(pgmr.errFlag(), 16);
				print_err(JMT_FLASH_TRGT_RESP);
				bidx = stream_blen; // Exit loop
			}
			else
			{
				bidx += blen;
				//bt.send("Section write complete.\r\n");
			 	//bt.send("Byte Address: "); bt.sendnum(baddr); bt.send("\r\n");
				//bt.send("Word Address: "); bt.sendnum((baddr>>1)); bt.send("\r\n");
				//bt.send("Byte Length: "); bt.sendnum(blen); bt.send("\r\n");
			}
		}
			
		print_succ();	
	}
}

//
//	jmt_read()
//
// Args: [ mem. byte address, byte length to read ]
// Reads a given length of bytes starting at given byte address. Sends back data as its reads each byte out of
// program memory
void jmt_read(int baddr, int blen) {
	if( baddr < 0 || blen < 0 ) print_err(JMT_READ_ARGVAL); 
	else{
		print_succ();
		
		// Ensure target device is not busy
		while( pgmr.atmegaIsBusy() );
		
		// Begin reading data
		for( int i = baddr; i < (baddr+blen); i++ ){
			bt.tr( pgmr.rdPmemByte(int(i/WORD_BLEN), (i%2==1)) );
		}
		
		if( pgmr.errFlag() )	print_err(JMT_READ_TRGT_RESP);
		//else									print_succ();

	}

}


//
//	jmt_end()
//
//	Releases slave from reset/programming mode
void jmt_end() {
	pgmr.endProgrammingMode();
	print_succ();	
}


//
//	jmt_echo()
//
// 	Act as SPI slave, echo data sent from target device over bluetooth. Data sent to programmer will be held 
//	in buffer until requested by the slave.
#define WR_BUF_IDX RBUF_SIZE/2
void spi_echo_rd_reply();
void jmt_echo(int begin) {
	if( begin != 0 ) { 
		bool echoing = true;
		char* wr_buf = (rbuf+WR_BUF_IDX);
		const char echo_cmd[] = "JMT+ECHO=0\r\n";
		uint8_t ecmd_len = strlen(echo_cmd);
		uint8_t ecmd_idx = 0;

		spi.enable_interrupt();
		spi.enable(0); // Enable as slave

		print_succ();
		
		// Clear uart buffer
		uart.flush();

		// Reset bt <-> spi buffer pointers
		btxspi.reset();
			
		// Run echoer
		while( echoing ){

			// Recieving from uart (store as read data for master device)
			if( uart.available() && ((btxspi.rd_uart_ptr+1) != btxspi.rd_spi_ptr) ) // Check data ready and buffer not full
			{
				char rcv_char = uart.read();
				rbuf[btxspi.rd_uart_ptr] = rcv_char;
				
				//uart.print("rd_uart_ptr: "); uart.printnum(btxspi.rd_uart_ptr); uart.print("\n");
				//uart.print("rd_spi_ptr: "); uart.printnum(btxspi.rd_spi_ptr); uart.print("\n");
				//uart.print("req_rlen: "); uart.printnum(btxspi.req_rlen); uart.print("\n");
				//uart.print("rcv_char: "); uart.printnum((int)rcv_char); uart.print("\n");

				// Check for the echo exit command
				if( rcv_char == echo_cmd[ecmd_idx] ) 
				{
					ecmd_idx++;
					if( ecmd_idx >= ecmd_len ) {// Full exit command has been read
						echoing = false; // Exit while loop
						jmt_echo(0); // Turn off echo (disable SPI interrupt and set back to master)
					}
				}
				else
					ecmd_idx = 0;
				btxspi.rd_uart_ptr++;
			}
			
			// Transmitting thru uart (sending stored write data from master device)
			if( btxspi.wr_uart_ptr != btxspi.wr_spi_ptr ){	
				bt.tr( (unsigned char) wr_buf[btxspi.wr_uart_ptr] );
				/*uart.print("wr_uart_ptr: "); uart.printnum(btxspi.wr_uart_ptr); uart.print("\r\n");
				uart.print("wr_spi_ptr: "); uart.printnum(btxspi.wr_spi_ptr); uart.print("\r\n");
				uart.print("req_wlen: "); uart.printnum(btxspi.req_wlen); uart.print("\r\n");
				*/
				btxspi.wr_uart_ptr++;
			}
		
		}
	}
	// begin=0 (stop)
	else{
		spi.disable_interrupt();
		spi.set_mst();
		print_succ();
	} 
}

//**** JMT_ECHO SPI Interrupt *****
void _MY_SPI_ISR_() {
	
	// New cmd
	if( btxspi.cmd == 0 ) 
	{
		btxspi.cmd = (SPDR & 0xC0);
		SPDR = (btxspi.rd_uart_ptr - btxspi.rd_spi_ptr); // Read data count
	}
	else if( btxspi.cmd & 0xC0 ) 
	{
		btxspi.cmd = (btxspi.cmd >> 2);
		btxspi.req_wlen = SPDR;
		SPDR = (btxspi.wr_spi_ptr - btxspi.wr_uart_ptr);				 // Write data count	
	}
	else if( btxspi.cmd & 0x30 ) 
	{
		btxspi.cmd = (btxspi.cmd >> 4);
		btxspi.req_rlen 	 = SPDR;
		if( btxspi.req_rlen > uint8_t(btxspi.rd_uart_ptr - btxspi.rd_spi_ptr))
			btxspi.req_rlen = uint8_t(btxspi.rd_uart_ptr - btxspi.rd_spi_ptr);
		if( btxspi.req_wlen == 0 ) btxspi.cmd &= (~0x1);
		if( btxspi.req_rlen == 0 ) btxspi.cmd &= (~0x2);
		else
		{
			spi_echo_rd_reply();
		}
	}
	else
	{
		// Read (being read)
		if( btxspi.cmd & 0x2 )
		{
			spi_echo_rd_reply();
		}
		else // Send zero if done reading
			SPDR = 0x00;
	
		//Write (being written to)
		if( btxspi.cmd & 0x1 )
		{
			rbuf[WR_BUF_IDX + btxspi.wr_spi_ptr] = SPDR;	
			btxspi.wr_spi_ptr += ((btxspi.wr_spi_ptr+1) == btxspi.wr_uart_ptr) ? 0 : 1;
			if( btxspi.req_wlen != 0 ) btxspi.req_wlen--; 
			btxspi.cmd &= (btxspi.req_wlen == 0) ? (~0x1) : 0xff;
		}
		else // Discard data if done reading 
			SPDR;
		
	}

}


void spi_echo_rd_reply()
{
			SPDR = rbuf[btxspi.rd_spi_ptr];
			btxspi.rd_spi_ptr += (btxspi.rd_spi_ptr == btxspi.rd_uart_ptr) ? 0 : 1; // Prevent spi ptr from passing uart ptr
			btxspi.req_rlen--;
			btxspi.cmd &= (btxspi.req_rlen==0) ? (~0x2) : 0xff;

}
//************

//*******************************************
//
//	Helper Functions
//
//*******************************************

//
// fill_arg_vals()
//
// Fills 'vals'array until invalid argument (non-integer) or no more arguments remaining
void fill_arg_vals(int* vals, int* num_vals, char** args, int max_vals) {
	for( *num_vals = 0; (*num_vals < max_vals) && (get_arg_int(args, &vals[*num_vals])); (*num_vals)++ );
}

//
// get_arg_int()
//
//	
bool get_arg_int(char** args, int* val) {
	char* end = strstr((*args),",");
	bool  last_arg = false;
	
	if( end == nullptr ) {
		end = strstr((*args), "\r\n"); 	// If no comma do CR
		last_arg = true;
	}
	
	if( end == nullptr )	return false;										// If neither return false
	else								 	(*end) = '\0';									// Terminate string
	
	
	// Convert string to int
	if( str_is_int(*args) )		(*val) = atoi((*args));
	else											return false;	


	// Move arg pointer to start of next string
	if( last_arg ) (*args) = end;
	else					 (*args) = (end+1);
	

	return true;

}


//
//	substrcmp()
//
//
bool substrcmp(char* str, char* end, const char* val) {
	int end_idx = (int)end - (int)str;
	bool eq = (end_idx > 0);
	bool end_str = false;

	for( int i = 0; eq && !end_str && (i < end_idx); i++ )
	{
		eq = (str[i] == val[i]);
		end_str = ((val[i] == '\0') || (str[i] == '\0'));
	}
	return eq;
}

//
//	has_str()
//
//
bool has_str(char* str, const char* sub) {
	return( strstr(str, sub) != NULL );
}

//
//	str_is_int()
//
//
bool str_is_int(char* str){
	bool is_int = true;
	for(int i = 0; (str[i] != '\0') && (is_int = (str[i] >= '0' && str[i] <= '9')); i++);
	return is_int;
}


//
// buf_byte_to_uint()
//
// 
uint16_t buf_byte_to_uint( int st, int len ) {
	uint16_t val = 0;
	unsigned char b;	
	for( int i = 0; i < len ; i++ ){ 
			b = rbuf[st+i]; 
			val |= (b << ((len-1-i)*8));
	}
	return val;
}

//
// bt_listen_timeout()
//
// Bluetooth timeout clear on read function
bool bt_listen_timeout()
{
	if( bt_listen_to )
	{
		bt_listen_to = false;
		return true;
	}
	else 
		return false;
	
}
