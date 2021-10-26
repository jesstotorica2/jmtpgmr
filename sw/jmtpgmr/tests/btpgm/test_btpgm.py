import os

from click.testing import CliRunner
from jmtpgmr.jmtpgmr import btpgm
from jmtpgmr import __version__

def test_btpgm_run():
  runner = CliRunner()
  result = runner.invoke(btpgm, ['-i','test.hex','-t',"98:d3:11:fc:95:7a",'-d'])

  print(result.output)

test_btpgm_run()
