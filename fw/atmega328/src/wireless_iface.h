

#include "Stopwatch.h"
#include "myUART.h"

class WirelessIface
{
	public:
		char* buff;
		int   buff_size;

		bool listen_to;

		WirelessIface(char* buff_in, const int buff_size_in);
		~WirelessIface();


		bool init(myUART* uart, Stopwatch* tmr); // Bluetooth init 

		bool check_status(); // Check wireless interface status (i.e. connected and device is alive)
		void wait_connect(); // Waits until a device connects
		bool listen(char* buff_in, const int buff_size_in, const char* token = nullptr, const int timeout = 0); // Listen for token
		bool listen_timeout();

		void send(const char* msg); // Send string to client
		void sendnum(int num, int base); // Send number to client

		void tr_setup(int blen);
		void tr(unsigned char c);

};
