import boto3

from collections import namedtuple

from cloudmesh.api.provider import Provider as ProviderInterface
from cloudmesh.api.provider import Result
from cloudmesh.aws.flavors import list_flavors

from cloudmesh.util import Dotdict

import logging
logger = logging.getLogger(__name__)


class Provider(ProviderInterface):

    def __init__(self, **kwargs):

        self._client = boto3.client('ec2')

    @property
    def name(self):
        return 'ec2'

    def nodes(self):
        """List the instances running on EC2

        This is a result of querying the AWS API using
        ``DescribeInstances`` and concatenating the ``Instances`` for
        each ``Reservations`` entry.

        See the **Response Structure** description in the `Boto3
        EC2.Client.describe_instances()
        <https://boto3.readthedocs.io/en/stable/reference/services/ec2.html#EC2.Client.describe_instances>`_
        documentation.
        """

        logger.debug('Listing EC2 nodes')
        x = Dotdict(self._client.describe_instances())
        logger.debug('Response: %s', x.ResponseMetadata.HTTPStatusCode)
        if x.ResponseMetadata.HTTPStatusCode == 200:
            reservations = x.Reservations
            instances = []
            for r in reservations:
                for i in r.Instances:
                    result = Result(i.InstanceId, i)
                    instances.append(result)
            return instances
        else:
            raise NotImplementedError(x.ResponseMetadata.HTTPStatusCode)

    def secgroups(self):
        """List the security groups

        See `Boto3 EC2 Client describe_security_groups()
        <https://boto3.readthedocs.io/en/stable/reference/services/ec2.html#EC2.Client.describe_security_groups>`_

        """

        logger.debug('Listing EC2 security groups')
        x = Dotdict(self._client.describe_security_groups())
        logger.debug('Response: %s', x.ResponseMetadata.HTTPStatusCode)

        if x.ResponseMetadata.HTTPStatusCode == 200:
            return [Result(sg.GroupId, sg) for sg in x.SecurityGroups]
        else:
            raise NotImplementedError(x.ResponseMetadata.HTTPStatusCode)


    def flavors(self):
        """List the available instance types

        """

        logger.debug('Listing EC2 instance types (flavors)')
        flavors = Dotdict(list_flavors())
        return [Result(f.Instance_Type, Dotdict(f)) for f in flavors]


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


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    for name in 'requests botocore cloudmesh.aws.flavors'.split():
        logging.getLogger(name).setLevel('INFO')

    p = Provider()

    print 'Nodes'
    for n in p.nodes():
        print n.id, n.ImageId, n.InstanceType, n.PrivateIpAddress, n.LaunchTime, n.KeyName
    print

    print 'Security groups'
    for g in p.secgroups():
        print g.GroupName, g.Description
    print

    print 'Flavors'
    flavors = p.flavors()
    for f in flavors[:min(10, len(flavors))]:
        print f.Instance_Type, f.vCPU, f.Memory, f.Storage, f.Networking_Performance
    print
