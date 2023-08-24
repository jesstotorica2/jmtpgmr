#!/Users/jesstotorica/anaconda3/bin/python
import sys
import click
from . import __version__

# Package submodules
from .btpgm.btpgm import BTprogrammer

@click.group(invoke_without_command=True)
@click.version_option(__version__, '--version','-v')
@click.option( '--debug', '-d', is_flag=True, default=False, help='Display debug information')
@click.pass_context

def cli(ctx, debug):
  ctx.obj = {
    'debug':debug
  }
  
  if debug:
    click.echo('Debug mode is on')


#
# Subcommand: btpgm
#
@cli.command()
#@click.command()
@click.option('--target','-t', required=True, help='Bluetooth device mac address')
@click.option('--infile','-i', required=False, help='Input .hex file')
@click.option('--debug','-d', required=False, is_flag=True,  help='Print debug information during programming')
@click.option('--verify','-v', required=False, is_flag=True, help='Verify programming by reading back flash memory')
@click.option('--echo','-e', required=False, is_flag=True, help='Enter echo mode after programming is finished')
@click.option('--eesave', required=False, is_flag=True, help='Enable eeprom save fuse bit')
@click.option('--no_eesave', required=False, is_flag=True, help='Disable eeprom save fuse bit')

def btpgm(infile,target,debug,verify,echo,eesave,no_eesave):
  """
  Use btpgm to program Atmega328 microcontroller via bluetooth.
  """
  click.echo("target={}".format(target))
  click.echo("infile={}".format(infile))
  
  if(eesave):
    click.echo("eesave=True")
    eesave = True
  elif(no_eesave):
    click.echo("no_eesave=True")
    eesave = False
  else:
    eesave = None

  BTpgmr = BTprogrammer()
  BTpgmr.btpgm(infile, target, debug=debug, verify=verify, echo=echo, eesave=eesave)



#if __name__ == '__main__':
#  btpgm()
