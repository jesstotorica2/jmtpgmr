# AVR Library
MYAVRLIB_PATH=/Users/jesstotorica/projects/my_avr_lib.git
MCU=atmega328

TARGET=btprogrammer
SRC_DIR=../src
MYAVR_SRC_DIR=$(MYAVRLIB_PATH)/src/$(MCU)
IMG_DIR=./image
SRC_FILES=$(SRC_DIR)/$(TARGET).cpp
BUILD_DIR=object_files

INCLUDES= $(MYAVRLIB_PATH)/include/$(MCU)

# Source files used from AVR lib
MYAVR_SRCS=	mystdlib.cpp \
			myUART.cpp \
			mySPI.cpp \
			myTimer.cpp \
			hc05.cpp \
			myIO.cpp \
			atmega328_pgm.cpp \
			uartxspi.cpp \
			Stopwatch.cpp \
			myInterrupt.cpp


# Compiler Macros
MACRO_DEFS=	-DMY_SPI_STC_ISR 

F_CPU=16000000
CC=avr-gcc
OBJCOPY=avr-objcopy
CFLAGS= -Wall -g -Os -mmcu=$(MCU) $(MACRO_DEFS) -DF_CPU=$(F_CPU) -I $(INCLUDES)

LIBS= -L$(MYAVRLIB_PATH)/lib -lmy_$(MCU)

# Get list of source files
SRC_FILES=$(shell cd $(SRC_DIR) && find *.cpp)

# Get list of object files
SRC_OBJ=$(patsubst %.cpp,$(BUILD_DIR)/%.o,$(SRC_FILES))
MYAVR_OBJ=$(patsubst %.cpp,$(BUILD_DIR)/%.o,$(MYAVR_SRCS))


# VPATH - This should include all directories where target source files reside
VPATH=	$(SRC_DIR) \
		$(MYAVR_SRC_DIR)

# Create hexfile image for flash programming
.PHONY: hex
#hex: dirs $(MYAVR_OBJ) $(SRC_OBJ)
hex: dirs  $(SRC_OBJ) $(MYAVR_OBJ)
	$(CC) $(CFLAGS) $(MYAVR_OBJ) $(SRC_OBJ) -o $(IMG_DIR)/$(TARGET).bin
	$(OBJCOPY) -j .text -j .data -O ihex $(IMG_DIR)/$(TARGET).bin $(IMG_DIR)/$(TARGET).hex


# Create image directory
dirs:
	@mkdir -p $(IMG_DIR)
	@mkdir -p $(BUILD_DIR)

# Create object files from .cpp files
$(BUILD_DIR)/%.o: %.cpp
	@echo
	@echo "--------------------Compiling $@----------------------"
	$(CC) -c $(CFLAGS) -o $@ $<
	@echo "-----------------Finished Compiling $@----------------"
	@echo

hex_debug:
	${CC} ${CFLAGS} -o ${TARGET}.bin ${SRCS} | >> compErrs.txt
	${OBJCOPY} -j .text -j .data -O ihex ${TARGET}.bin ${TARGET}.hex 

flash:
	/Applications/Arduino.app/Contents/Java/hardware/tools/avr/bin/avrdude -C/Applications/Arduino.app/Contents/Java/hardware/tools/avr/etc/avrdude.conf -v -patmega328p -carduino -P/dev/cu.usbmodem14201 -b115200 -D -Uflash:w:$(IMG_DIR)/$(TARGET).hex:i 


clean:
	rm -rf $(IMG_DIR)
	rm -rf $(BUILD_DIR)

.PHONY: dump
dump:
	@echo $(SRC_OBJ)
	@echo $(MYAVR_OBJ)
