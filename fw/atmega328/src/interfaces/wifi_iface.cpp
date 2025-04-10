
#include "../wireless_iface.h"

#include "esp8266.h"
#include "mystdlib.h"

#define WIFI_BAUD_RATE 115200
#define WIFI_RST_PIN   2
#define WIFI_CONFIGURE_PIN 8

esp8266 wifi;
unsigned char wifi_last_link_id = 0;
unsigned int  wifi_tr_cur = 0;
unsigned int  wifi_tr_limit = 0;
bool          wifi_configure_as_ap = false;

// wifi helper functions prototypes
void _wifi_configure(char* wifi_rbuf, const int rbuf_size);
bool _wifi_configure_station(bool quit_ap, char* wifi_rbuf, const int rbuf_size);
bool _wifi_configure_AP(char* wifi_rbuf, const int rbuf_size);
bool _wifi_connect(int attempts, char* wifi_rbuf, const int rbuf_size);
void _wifi_recover(char* wifi_rbuf, const int rbuf_size);

//
// wifi_configure()
//
// Configure the esp8266 module. Function does not return until controller has been successfully configured
// Enters recovery mode on failures
#define WIFI_AP_SET_IP_CMD "AT+CIPAP_CUR=\"192.168.1.243\"\r\n"
#define WIFI_AP_CREATE_SERVER_CMD "AT+CIPSERVER=1,69\r\n"
void _wifi_configure(char* wifi_rbuf, const int rbuf_size)
{
	bool sts = false;
	while( false == sts )
	{
		if( wifi_configure_as_ap )
		{
			sts = _wifi_configure_AP( wifi_rbuf, rbuf_size );
		}
		else
		{
			// Configure ESP8266 as station for multiple connections
			sts = _wifi_configure_station( true, wifi_rbuf, rbuf_size ); // Configure station (quit_ap = true)

			// Connect to the wifi network
			if( sts )
			{
				sts &= _wifi_connect( 3, wifi_rbuf, rbuf_size );	
			}	
		}

		if( sts )
		{
			// Set AP IP address here
			// NOTE: the router doesn't allow this. Or does this just need to be done before joining?
			//       anyways the router now just has a reserved IP for the MAC of this ESP8266, need
			//       change if we ever change out the esp module
			//sts &= wifi.send(WIFI_AP_SET_IP_CMD, wifi_rbuf, rbuf_size);
		
			// Creating a server
			sts = wifi.send(WIFI_AP_CREATE_SERVER_CMD, wifi_rbuf, rbuf_size); 
		}

		if( !sts ) // If any steps in our configuration failed, enter recovery mode
		{
			_wifi_recover(wifi_rbuf, rbuf_size);
		}
	}
}

//
// wifi_configure_station()
//
// Sets ESP8266 to station mode (i.e. device connecting to wifi) and configures. 
// quit_ap - Quit current wifi connection 
bool _wifi_configure_station(bool quit_ap, char* wifi_rbuf, const int rbuf_size)
{
	bool sts = true;
	sts &= wifi.send("AT+CWMODE=1\r\n", wifi_rbuf, rbuf_size); // 1-Station, 2-Soft AP, 3-Station and Soft AP
	sts &= wifi.send("AT+CIPMUX=1\r\n", wifi_rbuf, rbuf_size); // 1 - configure for multiple connections
	if( quit_ap ) 
	{
		sts &= wifi.send("AT+CWQAP\r\n", wifi_rbuf, rbuf_size); // Quit AP
	}
	return sts;
}

//
// wifi_configure_AP()
//
// AT+CWSAP_CUR=<ssid>,<pwd>,<chl>,<ecn>[, <max conn>][,<ssid hidden>]
//#define WIFI_CONFIG_AP_CMD "," TO_STR(JMTIOT_ESP8266_AP_PSWD) ",5,3" // 3 = WPA2_PSK
#define WIFI_CONFIG_AP_CMD "AT+CWSAP_CUR=\"jmtiot_wifi_pgmr\",\"programstuff\",5,3\r\n" // 3 = WPA2_PSK
bool _wifi_configure_AP(char* wifi_rbuf, const int rbuf_size)
{
	// Set as Access Point
	if( false == wifi.send( "AT+CWMODE=2\r\n", wifi_rbuf, rbuf_size ) ) return false; // 2-Soft Access Point
	if( false == wifi.send("AT+CIPMUX=1\r\n", wifi_rbuf, rbuf_size) ) return false; // 1 - configure for multiple connections
	// Setup IP address of access point
	if( false == wifi.send( WIFI_AP_SET_IP_CMD, wifi_rbuf, rbuf_size ) ) return false;
	// Setting AP to have a password here
	if( false == wifi.send( WIFI_CONFIG_AP_CMD, wifi_rbuf, rbuf_size ) ) return false;	
	return true;	
}

///
//	wifi_connect()
//
#define WIFI_NO_EEPROM_SSID 1 // comment this out to enable eeprom 
#define WIFI_SSID      "we-fee" 
#define WIFI_SSID_PSWD "giveme5bucks"
bool _wifi_connect(int attempts, char* wifi_rbuf, const int rbuf_size)
{
	// Retrieve SSID and PSWD
	bool valid_ssid = true;
	bool wifi_connected = false;

#ifdef WIFI_NO_EEPROM_SSID
	char* ssid = nullptr;
	char* ssid_pswd = nullptr;
	valid_ssid = false;
#else
	char ssid[32];
	char ssid_pswd[32];
	eeprom::read((uint8_t*)ssid, 32, JMTIOT_SSID_OFFSET);
	eeprom::read((uint8_t*)ssid_pswd, 32, JMTIOT_SSID_PSWD_OFFSET);

	// Check strings read
	if( ssid[0] == '\0' || ssid_pswd[0] == '\0' ) valid_ssid = false; // empty string
	for( int i = 0; valid_ssid && ssid[i] != '\0'; i++ )
	{
		if( i >= 32 || ssid[i] < 32 || ssid[i] > 126 ) valid_ssid = false;
	}
	for( int i = 0; valid_ssid && ssid_pswd[i] != '\0'; i++ )
	{
		if( i >= 32 || ssid_pswd[i] < 32 || ssid_pswd[i] > 126 ) valid_ssid = false;
	}
#endif

	for( int i = 0; i < attempts; i++ )
	{
#ifdef WIFI_SSID
		if( i%2 == 0 && valid_ssid )
		{
			wifi_connected = wifi.connectWifi(ssid, ssid_pswd, wifi_rbuf, rbuf_size);
		}
		else
		{
			wifi_connected = wifi.connectWifi(WIFI_SSID, WIFI_SSID_PSWD, wifi_rbuf, rbuf_size);
		}
#else
		if( valid_ssid )
		{
			wifi_connected = wifi.connectWifi(ssid, ssid_pswd, wifi_rbuf, rbuf_size);
		}
#endif
#ifdef WIFI_STS_LED
		if( wifi_connected )
		{
			setPin(WIFI_STS_LED, 1);
			return true;
		}
		else
		{
			setPin(WIFI_STS_LED, 0);
		}
#else
		if( wifi_connected ) return true;
#endif
	}
	return false;
}

//
// recover()
//
// This function should only be called if we think something has completely broken as it will start the
// microcontroller over.
//
// 	1. Check coms with the esp8266
//		- while failing, blink sts LED every 2 seconds on, 4 seconds off
//			- reset esp8266
//		- continue on success
//
// 2. Wifi connect
//		- attempt x times
//		- if still fail, enter station mode. Wait for someone to set the wifi SSID and key
//
// 3. Software reset - restart program
//
//#define WIFI_AP_SET_IP_CMD "AT+CIPAP_CUR=" TO_STR(JMTIOT_ESP8266_AP_SERVER) "\r\n"
//#define WIFI_AP_CREATE_SERVER_CMD "AT+CIPSERVER=1," TO_STR(JMTIOT_ESP8266_AP_PORT) "\r\n"
void _wifi_recover(char* wifi_rbuf, const int rbuf_size)
{
	// TODO
	/*
	int pokes = 0;
	int wait_connects = 0;
	bool recovered = false;
	while( !recovered )
	{
		// 1. Poke (coms verify)
		pokes = 0;
		setPin(WIFI_STS_LED, 0);
		while( false == wifi.poke(2000) )
		{
			if( wifi.poke(2000) )
			{
				break;
			}
			else
			{
				setPin(WIFI_STS_LED, 1);
				_delay_ms(2000);
				setPin(WIFI_STS_LED, 0);
			}
			pokes++;
			
			if( pokes > 20 && ENABLE_WATCHDOG_RESET != 0 )
			{
				// NUCLEAR OPTION: Reset with watchdog timer
				wdt_start(WDTO_15MS); // Start 15ms timeout for watchdog
				while(1){
					_delay_ms(5000);
					uart.print("ERROR: we should have reset with the wdt!");
				};
			}
			else if( pokes%5 == 0 ) // Every 5 failed pokes
			{
				wifi.resetBaudRate(ESP8266_BAUD_RATE); // This does a hw reset to the ESP as well
			}
		}

		// 2. Wifi connect
		if( 2 != wifi.getStatus(wifi_rbuf, rbuf_size) ) // 2 means connected to AP
		{
			// Configure as station
			wifi_configure_station(true); // Configure station (quit_ap = true)
			if( !wifi_connect(2) )
			{
				bool sts = true;
				sts &= wifi.send("AT+CWMODE=2\r\n", wifi_rbuf, rbuf_size); // 2-Soft Access Point
				// Set AP IP address here
				sts &= wifi.send(WIFI_AP_SET_IP_CMD, wifi_rbuf, rbuf_size);
				// Setting AP to have a password here
				sts &= wifi_configure_AP();
				// Creating a server
				sts &= wifi.send(WIFI_AP_CREATE_SERVER_CMD, wifi_rbuf, rbuf_size);

				// Wait loop for SSID and PSWD data
				wait_connects = (sts) ? 0 : 360; // Only wait for data if setup commands succeeded
				while( wait_connects < 360 )// Check back every hour
				{
					if( 0 != wifi.waitConnect(wifi_rbuf, rbuf_size, 10000) ) // Client connected
					{
						uint16_t dataLen = 0;
						uint8_t link_id = wifi.waitIPD(wifi_rbuf, &dataLen, IPD_WAIT_TIMEOUT);

						// Got data? write it to EEPROM, format = <SSID>\n<PSWD>
						uint16_t ssid_len;
						uint16_t pswd_len;
						
						// go until we see '\n'
						for( ssid_len = 0; ssid_len < dataLen && wifi_rbuf[ssid_len] != '\n'; ssid_len++ );
						wifi_rbuf[ssid_len] = '\0';
						pswd_len = dataLen - (ssid_len+1);
						
						// null terminate if not already
						if( wifi_rbuf[ssid_len+pswd_len] != '\0' ) wifi_rbuf[ssid_len+pswd_len+1] = '\0';
						// Successfully read ssid and pswd, write to eeprom now
						if( ssid_len > 0 && pswd_len > 0 )
						{
							eeprom::write((uint8_t*)wifi_rbuf, ssid_len+1, JMTIOT_SSID_OFFSET);
							eeprom::write((uint8_t*)(wifi_rbuf+ssid_len+1), pswd_len+1, JMTIOT_SSID_PSWD_OFFSET);
							wait_connects = 360;
							send_success(link_id);
						}

						else
						{
							send_err(link_id, 0xFF);
						}

					}
					wait_connects += 1;
				}
			}
		}
		else
		{
			recovered = true;
		}
	}
	*/
}


//==================================
//
// WirlessInterface
//
//==================================
WirelessIface::WirelessIface(char* buff_in, const int buff_size_in)
{
	buff = buff_in;
	buff_size = buff_size_in;

	listen_to = false;
}

WirelessIface::~WirelessIface()
{
}

//
// init()
//
bool WirelessIface::init(myUART* uart, Stopwatch* tmr)
{
	setPUD( 0 ); // make sure global pull-up disable is cleared

	// Setup configure pin as pull-up
	setInput( WIFI_CONFIGURE_PIN );
	setPin( WIFI_CONFIGURE_PIN, 1 );

	// Setup reset pin to be open-drain type pin (esp board has local pull-up)
	setInput( WIFI_RST_PIN );
	setPin( WIFI_RST_PIN, 0 );

	// Initialize uart and ESP8266 module
	uart->init( WIFI_BAUD_RATE );
	wifi.init( uart, tmr, WIFI_RST_PIN, WIFI_BAUD_RATE );
	_delay_ms( 500 );

	// Configure esp8266, connect to wifi, start server
	wifi_configure_as_ap = getPin( WIFI_CONFIGURE_PIN );
	_wifi_configure( buff, buff_size );
	return true;
}

//
// check_status()
//
//      0 - Failed to talk to ESP
//      1 - Failed to find 'STATUS:' in ESP response
//      2 - Connected to AP
//      3 - TCP or UDP transmission has been created
//      4 - TCP or UDP transmission of station is disconnected (?)
//      5 - Station is NOT connected to an AP
bool WirelessIface::check_status()
{
	int sts = wifi.getStatus( buff, buff_size );

	// Connected to network, just need to wait for a client
	if( sts == 2 )
	{
		wait_connect();
	}
	else if( sts == 3 || sts == 4 )
	{
		// I think this means we've got clients, carry on
	}
	// Either we failed to talk to esp or got nonsense value back
	else
	{
		// Pulse reset
		setPin( WIFI_RST_PIN, 1 );
		setOutput( WIFI_RST_PIN );
		_delay_ms( 500 );
		setPin( WIFI_RST_PIN, 0 );
		setInput( WIFI_RST_PIN );
	
		// configure (connect to wifi, setup server)
		_wifi_configure( buff, buff_size );
		wait_connect();
	}

	return true;

}

//
//  wait_connect()
//
//  Start inquiry, wait for device to connect
void WirelessIface::wait_connect()
{
	unsigned char cnxn = wifi.waitConnect( buff, buff_size, 0 ); // 0 = not timeout WE MIGHT WANT TO CHANGE THIS
	if( cnxn == 0 )
	{
		// TODO how do we handle if no connections is made
	}
}

//
// listen()
//
bool WirelessIface::listen(char* buff_in, const int buff_size_in, const char* token, const int timeout)
{
	unsigned int  dlen;
	unsigned char sts;
	unsigned int  j;
	unsigned int  dlen_total = 0;
	unsigned int  token_len = strlen( token );

	while( 1 )
	{
		dlen = buff_size_in - dlen_total;
		sts = wifi.waitIPD( (buff_in + dlen_total), &dlen, timeout*1000 );
		j = 0;

		if( sts == 0xFF ) // Timeout
		{
			listen_to = true;
			return false;
		}
		else if( sts >= 0 && sts < 5 )
		{
			wifi_last_link_id = sts;
			dlen_total += dlen;

			// receive until we hit 'buff_size_in'
			if( token == nullptr ) 
			{
				if( dlen_total >= (unsigned int)buff_size_in ) return true;
			}
			// Look for 'token' in received data
			else
			{
				if( dlen >= token_len )
				{
					for( unsigned int i = 0; i < (dlen-token_len+1); i++ )
					{
						for( j = 0; j < token_len; j++ )
						{
							if( buff_in[i+j] != token[j] ) break;
						}

						if( j == token_len ) return true;
					}
				}
			}
		}
		else
		{
			// TODO what happens if we get non-IPD data or something breaks
			listen_to = true;
			return false;
		}
	}
}

//
// send()
//
void WirelessIface::send(const char* msg)
{
	wifi.CIPsend( wifi_last_link_id, msg, 0, buff, buff_size );
}

//
// sendnum()
//
void WirelessIface::sendnum(int num, int base)
{
	char num_str[16];
	itoa(num, num_str, base);
	send( num_str );
}

//
// tr_setup()
//
void WirelessIface::tr_setup(int blen)
{
	wifi_tr_cur = 0;
	wifi_tr_limit = blen;
	wifi.CIPsend( wifi_last_link_id, nullptr, blen, buff, buff_size );
	return;
}

//
// tr()
//
void WirelessIface::tr(unsigned char c)
{
	if( wifi_tr_cur   >= wifi_tr_limit )
	{
		return; // something went wrong, don't transmit anything
	}

	if( wifi_tr_cur+1 == wifi_tr_limit )
	{
		wifi.tr( &c, 1, buff, buff_size, 5000, "SEND OK\r\n" );
		wifi_tr_limit = 0;
	}
	else
	{
		wifi.tr( &c, 1, nullptr, 0, 0, nullptr );
		wifi_tr_cur++;
	}
}

//
// listen_timeout()
//
// Bluetooth timeout clear on read function
bool WirelessIface::listen_timeout()
{
    if( listen_to )
    {
        listen_to = false;
        return true;
    }
    else
	{
        return false;
   	} 
}
