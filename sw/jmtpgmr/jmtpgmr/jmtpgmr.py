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
@click.option('--infile','-i', required=True, help='Input .hex file')
@click.option('--target','-t', required=True, help='Bluetooth device mac address')
@click.option('--debug','-d', required=False, is_flag=True,  help='Print debug information during programming')
@click.option('--verify','-v', required=False, is_flag=True, help='Verify programming by reading back flash memory')
@click.option('--echo','-e', required=False, is_flag=True, help='Enter echo mode after programming is finished')

def btpgm(infile,target,debug,verify,echo):
  """
  Use btpgm to program Atmega328 microcontroller via bluetooth.
  """
  click.echo("infile={}".format(infile))
  click.echo("target={}".format(target))
  BTpgmr = BTprogrammer()
  BTpgmr.btpgm(infile, target, debug=debug, verify=verify, echo=echo)



#if __name__ == '__main__':
#  btpgm()
