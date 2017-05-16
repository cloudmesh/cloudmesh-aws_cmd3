"""The AWS API does not provide a way to retrieve all available instance types.

This module provides such an implementation by scraping the **Instance
Types Matrix** athttps://aws.amazon.com/ec2/instance-types

This inspired by http://stackoverflow.com/a/42963435

"""


from bs4 import BeautifulSoup
import urllib2
from collections import OrderedDict

import logging
logger = logging.getLogger(__name__)


def get_table_2017_04_05(soup):
    title = soup.find(id='instance-type-matrix')
    table = title.parent.parent.parent.next_sibling.next_sibling
    rows = table.find_all('tr')
    return rows


def list_flavors(url='https://aws.amazon.com/ec2/instance-types', get_table=get_table_2017_04_05):
    """List the available AWS EC2 flavors

    The AWS API does not provide a method to list available instance
    types.  This methods implements such a call by parsing the
    **Instance Types Matrix** from the `webpage
    <https://aws.amazon.com/ec2/instance-types/>`_.

    :param str url: the url to parse
    :param func get_table: callback to get the HTML table (as BeautifulSoup) to process

    """

    logger.debug('Getting %s', url)
    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page, 'html.parser')

    logger.debug('Getting table using %s', get_table)
    table = get_table(soup)

    logger.debug('Finding column titles')
    titles = []
    for td in table[0].find_all('td'):
        t = ' '.join(list(td.strings)).encode('ascii', 'ignore').strip()

        if '(' in t:
            i = t.find('(')
            t = t[:i].strip()

        t = t.replace(' ', '_')
        logger.debug('Found: %s', t)
        titles.append(t)

    flavors = []
    for row in table[1:]:
        flavor = OrderedDict()
        for title, td in zip(titles, row.find_all('td')):
            value = ' '.join(list(td.strings)).encode('ascii', 'ignore').strip()
            flavor[title] = value
        logger.debug('Flavor: %s', dict(flavor))
        flavors.append(flavor)

    return flavors


def test_list_flavors():
    flavors = list_flavors()
    assert len(flavors) > 0

    for flavor in flavors:
        assert 'Instance_Type' in flavor
        assert 'vCPU' in flavor
        assert 'Memory' in flavor
        assert 'Storage' in flavor
        assert 'Networking_Performance' in flavor
        assert 'Physical_Processor' in flavor
        assert 'Clock_Speed' in flavor


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    test_list_flavors()
