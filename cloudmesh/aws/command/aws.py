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

    if public_ip:
        addr = None
        for a in p.addresses():
            if not a.instance_id:
                print('Using old ip', a.public_ip)
                addr = a
                break

        if not addr:
            print('Allocating new ip')
            addr = p.allocate_ip()

        print('Waiting for node')
        node.wait_until_running()
        print('Associating public ip', addr.public_ip)
        addr.associate(InstanceId=node.id)



def deallocate_node(id):
    p = Provider()
    p.deallocate_node(id)


def list_nodes():
    p = Provider()
    nodes = []
    for n in p.nodes():
        d = {}
        d['id'] = n.id
        d['key'] = n.key_name
        d['image_id'] = n.image_id
        d['private_ip'] = n.private_ip_address
        d['public_ip'] = n.public_ip_address
        d['state'] = n.state['Name']
        nodes.append(d)

    print(Printer.list(nodes))



class AwsCommand(PluginCommand):

    @command
    def do_aws(self, args, arguments):
        """
        ::
            Usage:
               aws nodes
               aws flavors
               aws boot [--image=IMAGE] [--flavor=FLAVOR] [--key=KEY] [--public-ip]
               aws delete --id=ID
        """

        if arguments['nodes']:
            list_nodes()

        elif arguments['flavors']:
            list_flavors()

        elif arguments['boot']:
            allocate_node(
                image=arguments['--image'],
                flavor=arguments['--flavor'],
                key=arguments['--key'],
                public_ip=arguments['--public-ip'])

        elif arguments['delete']:
            deallocate_node(
                id=arguments['--id'])

        else:
            raise ValueError('Invalid call to `aws`')
