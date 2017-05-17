from __future__ import print_function, absolute_import

from cloudmesh.common.Printer import Printer
from cloudmesh.shell.command import PluginCommand, command

from ..api.provider import Provider

from socket import gethostname


def list_flavors():
    p = Provider()
    flavors = p.flavors()
    print(Printer.list(flavors))


def allocate_node(image=None, flavor=None, key=None, public_ip=None):

    # default kwargs can't be used due to docopt

    name      = 'cloudmesh'
    image     = image      or 'ami-c58c1dd3'
    flavor    = flavor     or 't2.micro'
    key       = key        or gethostname()
    public_ip = public_ip  or False

    p = Provider()
    node = p.allocate_node(name=name, key=key, image=image, flavor=flavor)
    print('Booted', node.id)


def deallocate_node(id):
    p = Provider()
    p.deallocate_node(id)



class AwsCommand(PluginCommand):

    @command
    def do_aws(self, args, arguments):
        """
        ::
            Usage:
               aws flavors
               aws boot [--image=IMAGE] [--flavor=FLAVOR] [--key=KEY]
               aws delete --id=ID
        """


        if arguments['flavors']:
            list_flavors()

        elif arguments['boot']:
            allocate_node(
                image=arguments['--image'],
                flavor=arguments['--flavor'],
                key=arguments['--key'])

        elif arguments['delete']:
            deallocate_node(
                id=arguments['--id'])

        else:
            raise ValueError('Invalid call to `aws`')
