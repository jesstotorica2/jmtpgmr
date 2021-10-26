#!/bin/bash
JMTPGMR_BINDIR=$(cd ../../bin && echo ${PWD})
JMTPGMR_RUNDIR=$(cd ../../sw/ && echo ${PWD})

# Create bash executable to execut jmtpgmr module
echo "#!/bin/bash
export PYTHONPATH=${JMTPGMR_RUNDIR}
python -m jmtpgmr.jmtpgmr \"\$@\"" > ${JMTPGMR_BINDIR}/jmtpgmr

chmod 744 ${JMTPGMR_BINDIR}/jmtpgmr

# Add to bash profile
BASH_FILE=~/.bash_profile
BASH_LINE="export PATH=\"${JMTPGMR_BINDIR}:\$PATH\""
if [ -f "$BASH_FILE" ]; then
	IN_PROFILE=$(cat $BASH_FILE | grep "$BASH_LINE")
	if [ -z "$IN_PROFILE" ]; then
		$(echo "" >> $BASH_FILE)
		$(echo "#### Line added by jmtpgmr tool ####" >> $BASH_FILE)
		$(echo "$BASH_LINE" >> $BASH_FILE)
		$(echo "####################################" >> $BASH_FILE)
		$(echo "" >> $BASH_FILE)
	fi
fi
