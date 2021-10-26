# AVR Library
MYAVRLIB_PATH=~/projects/my_avr_lib.git

TARGET=btprogrammer
SRC_DIR=../src
IMG_DIR=./image
SRC_FILES=$(SRC_DIR)/$(TARGET).cpp 

INCLUDES= $(MYAVRLIB_PATH)/include

MCU=atmega328
F_CPU=16000000
CC=avr-gcc
OBJCOPY=avr-objcopy
CFLAGS= -Wall -g -Os -mmcu=$(MCU) -DF_CPU=$(F_CPU) -I $(INCLUDES)

MYAVR_OBJ_FILES=$(MYAVRLIB_PATH)/build/darwin/object_files/*.o
OBJ_FILES=$(MYAVR_OBJ_FILES)


# Create hexfile image for flash programming
.PHONY: hex
hex: dirs
	cd $(MYAVRLIB_PATH)/build/darwin && make compile
	$(CC) $(CFLAGS) $(OBJ_FILES) -o $(IMG_DIR)/$(TARGET).bin $(SRC_FILES)
	$(OBJCOPY) -j .text -j .data -O ihex $(IMG_DIR)/$(TARGET).bin $(IMG_DIR)/$(TARGET).hex

# Dirs
dirs:
	@mkdir -p $(IMG_DIR)

hex_debug:
	${CC} ${CFLAGS} -o ${TARGET}.bin ${SRCS} | >> compErrs.txt
	${OBJCOPY} -j .text -j .data -O ihex ${TARGET}.bin ${TARGET}.hex 

flash:
	/Applications/Arduino.app/Contents/Java/hardware/tools/avr/bin/avrdude -C/Applications/Arduino.app/Contents/Java/hardware/tools/avr/etc/avrdude.conf -v -patmega328p -carduino -P/dev/cu.usbmodem14201 -b115200 -D -Uflash:w:$(TARGET).hex:i 


clean:
	rm -rf $(IMG_DIR)
