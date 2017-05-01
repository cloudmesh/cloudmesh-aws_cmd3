import boto3

from collections import namedtuple

from cloudmesh.api.provider import Provider as ProviderInterface
from cloudmesh.api.provider import Result
from cloudmesh.aws.flavors import list_flavors
from cloudmesh.util import Dotdict

from munch import munchify

import logging
logger = logging.getLogger(__name__)


TAG_OWNER = 'cloudmesh'
TAG_NAME = 'cloudmesh'
VPC_CIDR_BLOCK = '192.168.1.0/24'
SECGROUP_NAME = 'cloudmesh'
SECGROUP_DESCRIPTION = 'Cloudmesh security group'


class Ec2Exception(Exception):
    pass


def _assign_tags(resource):
    resource.create_tags(Tags=[{'Key': 'Name', 'Value': TAG_NAME},
                               {'Key': 'Owner', 'Value': TAG_OWNER}])


def _find_resources(resource):
    gen = resource.filter(Filters=[{'Name': 'tag:Name', 'Values': [TAG_NAME]},
                                   {'Name': 'tag:Owner', 'Values': [TAG_OWNER]}])
    gen = iter(gen)

    try:
        result = gen.next()
    except StopIteration:
        return

    # sanity check to ensure uniqueness
    count = 0
    for x in gen:
        count += 1

    if count > 0:
        msg = 'Multiple (%s) cloudmesh resources were found' % count
        logger.error(msg)
        raise Ec2Exception(msg)

    return result


def _authorize_secgroup_rules(bound_method, **kwargs):
    try:
        bound_method(**kwargs)
    except boto3.exceptions.botocore.exceptions.ClientError as e:
        if e.message.endswith('already exists'):
            pass
        else:
            raise


def _initialize_ec2(ec2):

        # ensure that a VPC exists
    logger.info('Ensuring VPC')
    vpc = _find_resources(ec2.vpcs)
    if vpc:
        logger.info('Found VPC %s', vpc.id)
    else:
        vpc = ec2.create_vpc(CidrBlock=VPC_CIDR_BLOCK)
        vpc.wait_until_available()
        _assign_tags(vpc)
        logger.info('Created VPC %s', vpc.id)

    # ensure there is an internet gateway
    logger.info('Ensuring Internet Gateway')
    gw = _find_resources(ec2.internet_gateways)
    if gw:
        logger.info('Found Internet Gateway %s', gw.id)
    else:
        gw = ec2.create_internet_gateway()
        _assign_tags(gw)
        logger.info('Created Internet Gateway %s', gw)
        for rt in gw.route_tables.all():
            _assign_tags(rt)

    # the Gateway should be attached to the VPC
    vpcgw = _find_resources(vpc.internet_gateways)
    if vpcgw:
        assert vpcgw.id == gw.id  # FIXME
    else:
        logger.info('Attached Gateway %s to VPC %s', gw.id, vpc.id)
        gw.attach_to_vpc(VpcId=vpc.id)

    # ensure gateway has a routetable with destination 0.0.0.0/0
    logger.info('Ensuring VPC Route Table supports ingress')
    rt = _find_resources(vpc.route_tables)
    assert rt
    rt.create_route(DestinationCidrBlock='0.0.0.0/0', GatewayId=gw.id)

    # ensure there is a subnet
    logger.info('Ensuring VPC has a subnet')
    subnet = _find_resources(vpc.subnets)
    if subnet:
        logger.info('Found Subnet %s', subnet.id)
    else:
        subnet = vpc.create_subnet(VpcId=vpc.id, CidrBlock=vpc.cidr_block)
        _assign_tags(subnet)
        logger.info('Created Subnet %s', subnet.id)

    # ensure security groups allow ingress/egress
    logger.info('Ensuring Security Groups')
    secgroup = _find_resources(vpc.security_groups)
    if secgroup:
        logger.info('Found Security Group %s', secgroup.id)
    else:
        secgroup = vpc.create_security_group(GroupName=SECGROUP_NAME, Description=SECGROUP_DESCRIPTION)
        _assign_tags(secgroup)
        logger.info('Created Security Group %s', secgroup.id)

    logger.info('Ensuring security group allows pinging')
    _authorize_secgroup_rules(secgroup.authorize_ingress, IpPermissions=[
        {'IpProtocol': 'icmp',
         'FromPort': -1,
         'ToPort': -1,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ])
    logger.info('Ensuring security group allows SSH')
    _authorize_secgroup_rules(secgroup.authorize_ingress, IpPermissions=[
        {'IpProtocol': 'tcp',
         'FromPort': 22,
         'ToPort': 22,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ])
    logger.info('Ensuring security group allows outbound traffic')
    _authorize_secgroup_rules(secgroup.authorize_egress, IpPermissions=[
        {'IpProtocol': '-1',
         'FromPort': -1,
         'ToPort': -1,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
        }
    ])


    return munchify(dict(vpc=vpc, gw=gw, rt=rt, subnet=subnet, secgroup=secgroup))


class Provider(ProviderInterface):

    def __init__(self, **kwargs):

        self._ec2 = boto3.resource('ec2')
        x = _initialize_ec2(self._ec2)
        self._vpc = x.vpc
        self._gateway = x.gw
        self._routing_table = x.rt
        self._subnet = x.subnet
        self._secgroup = x.secgroup


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
        x = self._ec2.instances.all()
        instances = []
        for i in x:
            result = Result(i.instance_id, dict(id=i.id))
            instances.append(result)
        return instances


    def secgroups(self):
        """List the security groups

        See `Boto3 EC2 Client describe_security_groups()
        <https://boto3.readthedocs.io/en/stable/reference/services/ec2.html#EC2.Client.describe_security_groups>`_

        """

        logger.debug('Listing EC2 security groups')
        x = self._ec2.security_groups.all()
        return [Result(sg.id, {}) for sg in x]


    def flavors(self):
        """List the available instance types

        """

        logger.debug('Listing EC2 instance types (flavors)')
        flavors = Dotdict(list_flavors())
        return [Result(f.Instance_Type, Dotdict(f)) for f in flavors]

    def images(self):
        raise NotImplementedError()

    def addresses(self):
        """List Elastic IP address

        """

        logger.debug('Listing EC2 elastic IP addresses')
        import pdb; pdb.set_trace()
        x = Dotdict(self._client.describe_addresses())
        logger.debug('Response: %s', x.ResponseMetadata.HTTPStatusCode)

        if x.ResponseMetadata.HTTPStatusCode == 200:
            return [Result(a.PublicIp, a) for a in x.Addresses]
        else:
            raise NotImplementedError(x.ResponseMetadata.HTTPStatusCode)

    def networks(self):
        raise NotImplementedError()

    ################################ nodes

    def allocate_node(self, name=None, key=None, image=None,
                      flavor=None, network=None, security_groups=None, dry_run=False,
                      **kwargs):


        ################ parameter massages
        security_groups = security_groups or []
        min_count = kwargs.pop('min_count', 1)
        max_count = kwargs.pop('max_count', 1)

        ################ sanity checks
        assert name is not None
        assert key is not None
        assert image is not None
        assert flavor is not None
        assert type(security_groups) is list, security_groups

        ################ boot
        logger.debug('Allocating EC2 node')
        response = self._resource.create_instances(
            DryRun=dry_run,
            MinCount=min_count,
            MaxCount=max_count,
            ImageId=image,
            KeyName=key,
            SecurityGroupIds=security_groups,
            InstanceType=flavor,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name',
                     'Value': name,
                    },
                ]
            }],
        )

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
    # for name in 'boto3'.split():
    #     logging.getLogger(name).setLevel('WARNING')

    p = Provider()
    i = p._subnet.create_instances(ImageId='ami-c58c1dd3',
                                   MinCount=1, MaxCount=1,
                                   KeyName='gambit', InstanceType='t2.micro',
                                   SecurityGroupIds=[p._secgroup.id])[0]
    i.wait_until_running()
    ip = p._ec2.VpcAddress('eipalloc-2f96be1e')
    ip.associate(InstanceId=i.id)

    # print 'Nodes'
    # for n in p.nodes():
    #     n = p._ec2.Instance(n.id)
    #     print n.id, n.image_id, n.instance_type, n.private_ip_address, n.launch_time, n.key_name
    # print

    # print 'Security groups'
    # for g in p.secgroups():
    #     g = p._ec2.SecurityGroup(g.id)
    #     print g.group_name, g.description
    # print

    # print 'Flavors'
    # flavors = p.flavors()
    # for f in flavors[:min(10, len(flavors))]:
    #     print f.Instance_Type, f.vCPU, f.Memory, f.Storage, f.Networking_Performance
    # print

    # print 'Addresses'
    # for a in p.addresses():
    #     print a.id, a.attrs
    # print

    # print 'Allocate'
    # p.allocate_node(name='hello', key='gambit', image='ami-49c9295f', flavor='m1.small')
