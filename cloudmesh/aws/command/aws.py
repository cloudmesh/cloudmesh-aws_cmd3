from __future__ import print_function, absolute_import

from cloudmesh.common.Printer import Printer
from cloudmesh.shell.command import PluginCommand, command

from ..api.provider import Provider

from socket import gethostname


def list_flavors():
    p = Provider()
    flavors = p.flavors()
    print(Printer.list(flavors))
    # for f in flavors:
    #     print(f.Instance_Type, f.vCPU, f.Memory, f.Storage, f.Networking_Performance)


def allocate_node(image='ami-c58c1dd3', flavor='t2.micro', key=gethostname()):
    p = Provider()
    p.allocate_node(name='hello', key=gethostname(), image='ami-c58c1dd3', flavor='t2.micro')


def deallocate_node(id):
    p = Provider()
    i = p._ec2.Instance(id)
    i.terminate()


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
