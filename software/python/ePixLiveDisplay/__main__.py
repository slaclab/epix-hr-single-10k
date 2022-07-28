import argparse
import ePixLiveDisplay

parser = argparse.ArgumentParser('Pyrogue Client')

parser.add_argument('--serverList',
                    type=str,
                    help="Server address: 'host:port' or list of addresses: 'host1:port1,host2:port2'",
                    default='localhost:9099')

parser.add_argument('--dataReceiver',
                    type=str,
                    help='Rogue Data Receiver path string',
                    default=None)

parser.add_argument('cmd',
                    type=str,
                    choices=['image','pseudoscope','monitor'],
                    help='Client command to issue')
args = parser.parse_args()

if args.cmd == 'image':
    ePixLiveDisplay.ePixGUI.runEpixDisplay(dataReceiver=args.dataReceiver, serverList=args.server)

elif args.cmd == 'pseudoscope':
    ePixLiveDisplay.ePixGUIEnvMonitoring.runEpixDisplay(dataReceiver=args.dataReceiver, serverList=args.server)
elif args.cmd == 'monitor':
    ePixLiveDisplay.ePixGUIPseudoScope.runEpixDisplay(dataReceiver=args.dataReceiver, serverList=args.server)