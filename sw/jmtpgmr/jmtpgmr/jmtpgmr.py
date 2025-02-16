#!/Users/jesstotorica/anaconda3/bin/python
import sys
import click
from . import __version__

# Package submodules
#from .btpgm.btpgm import BTprogrammer
from .pgm.pgm import AtmegaProgrammer
from .sockets.btsock import BTSock
from .sockets.wifisock import WifiSock

@click.group(invoke_without_command=True)
@click.version_option(__version__, '--version','-v')
@click.option( '--debug', '-d', is_flag=True, default=False, help='Display debug information')
@click.option('--infile','-i',  required=False, help='Input .hex file')
@click.option('--debug','-d',   required=False, is_flag=True,  help='Print debug information during programming')
@click.option('--verify','-v',  required=False, is_flag=True, help='Verify programming by reading back flash memory')
@click.option('--echo','-e',    required=False, is_flag=True, help='Enter echo mode after programming is finished')
@click.option('--eesave',       required=False, is_flag=True, help='Enable eeprom save fuse bit')
@click.option('--no_eesave',    required=False, is_flag=True, help='Disable eeprom save fuse bit')
@click.pass_context
def cli(ctx,infile,debug,verify,echo,eesave,no_eesave):

  if debug:
    click.echo('Debug mode is on')

  click.echo("infile={}".format(infile))

  if(eesave):
    click.echo("eesave=True")
    eesave = True
  elif(no_eesave):
    click.echo("no_eesave=True")
    eesave = False
  else:
    eesave = None

  # Create programmer
  pgmr = AtmegaProgrammer( infile, debug=debug, verify=verify, echo=echo, eesave=eesave )

  ctx.obj = {
    'debug' : debug,
    'pgmr'  : pgmr
  }


#
# Subcommand: btpgm
#
@cli.command()
@click.option('--target','-t', required=False, default="98:d3:11:fc:95:7a", help='Bluetooth device mac address')
@click.pass_context
def btpgm(ctx, target):
  """
  Use btpgm to program Atmega328 microcontroller via bluetooth.
  """

  # Create Bluetooth Socket
  btsock = BTSock( target )
  ctx.obj['pgmr'].set_socket( btsock )
  ctx.obj['pgmr'].pgm()

#
# Subcommand: wifipgm
#
@cli.command()
@click.option('--target','-t', required=False, default="192.168.0.232", help='Wifi device IP address')
@click.pass_context
def wifipgm(ctx, target):
  """
  Use wifipgm to program Atmega328 microcontroller via wifi.
  """

  # Create Bluetooth Socket
  wifisock = WifiSock( target )
  ctx.obj['pgmr'].set_socket( wifisock )
  ctx.obj['pgmr'].pgm()

