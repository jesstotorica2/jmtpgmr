
#include "../wireless_iface.h"

#include "hc05.h"
#include "mystdlib.h"

#define BT_BAUD_RATE                        115200
#define BT_EN_PIN                               2

hc05 bt;

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
	return bt.init( uart, tmr, BT_EN_PIN, BT_BAUD_RATE );
}

//
// check_status()
//
bool WirelessIface::check_status()
{
	// This isn't great... If the device is not responding this will return true
	if( bt.poke(75) ) // Try a quick poke (75 ms)
	{
		wait_connect();
		return true;
	}
	else
	{
		return true;
	}
}

//
//  wait_connect()
//
//  Start inquiry, wait for device to connect
void WirelessIface::wait_connect()
{
    bool connected = false;

    // Start HC-05 inquiring
    bt.inquire();

    // Clear the buffer string
    buff[0] = '\0';
    //uart.print("rbuf before waiting: |"); uart.print(rbuf); uart.print("|\r\n"); //DEBUG!!!!!!!!!!!!!!!!
    while( !connected )
    {
        // Wait for device to send an 'OK' after connection
        bt.listen(buff, buff_size, "\r\n");
        // Check for 'OK' from successful connection
        connected = (strstr(buff,"OK\r\n") != NULL);
		//if(connected) {uart.print("connected with |");uart.print(rbuf);uart.print("|\r\n");}
    }

}

//
// listen()
//
bool WirelessIface::listen(char* buff_in, const int buff_size_in, const char* token, const int timeout)
{
	listen_to = bt.listen(buff_in, buff_size_in, token, timeout);
	return listen_to;
}

//
// send()
//
void WirelessIface::send(const char* msg)
{
	bt.send( msg );
}

//
// sendnum()
//
void WirelessIface::sendnum(int num, int base)
{
	bt.sendnum( num, base );
}

//
// tr_setup()
//
void WirelessIface::tr_setup(int blen)
{
	return;
}

//
// tr()
//
void WirelessIface::tr(unsigned char c)
{
	bt.tr( c );
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
