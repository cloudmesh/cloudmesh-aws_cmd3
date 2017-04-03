import boto3

from collections import namedtuple

from cloudmesh.api.provider import Provider as ProviderInterface
from cloudmesh.api.provider import Result

from cloudmesh.util import Dotdict

import logging
logger = logging.getLogger(__name__)


class Provider(ProviderInterface):

    def __init__(self, **kwargs):

        self._ec2 = boto3.client('ec2')

    @property
    def name(self):
        return 'ec2'

    def nodes(self):
        raise NotImplementedError()

    def secgroups(self):
        raise NotImplementedError()

    def flavors(self):
        raise NotImplementedError()

    def images(self):
        raise NotImplementedError()

    def addresses(self):
        raise NotImplementedError()

    def networks(self):
        raise NotImplementedError()

    ################################ nodes

    def allocate_node(self, name=None, image=None, flavor=None, network=None, **kwargs):
        raise NotImplementedError()


    def deallocate_node(self, ident):
        raise NotImplementedError()

    def get_node(self, ident):
        raise NotImplementedError()

    ################################ images

    def allocate_ip(self):
        raise NotImplementedError()

    def deallocate_ip(self, ident):
        raise NotImplementedError()

    def associate_ip(self, ip_ident, node_ident):
        raise NotImplementedError()

    def disassociate_ip(self, ip_ident, node_ident):
        raise NotImplementedError()

    def get_ip(self, ident):
        raise NotImplementedError()

    ################################ security groups

    def allocate_secgroup(self, *args, **kwargs): raise NotImplementedError()
    def deallocate_secgroup(self, *args, **kwargs): raise NotImplementedError()
    def modify_secgroup(self, *args, **kwargs): raise NotImplementedError()
    def get_secgroup(self, *args, **kwargs): raise NotImplementedError()

    ################################ keys

    def allocate_key(self, name, value, fingerprint):
        raise NotImplementedError()

    def deallocate_key(self, ident):
        raise NotImplementedError()

    def modify_key(self, name, value, fingerprint):
        raise NotImplementedError()

    def get_key(self, ident):
        raise NotImplementedError()

    ################################ images

    def allocate_image(self, *args, **kwargs): raise NotImplementedError()
    def deallocate_image(self, *args, **kwargs): raise NotImplementedError()
    def get_image(self, *args, **kwargs): raise NotImplementedError()



def test_provider():
    Provider()

