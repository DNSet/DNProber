# coding:utf-8

import os
from urllib.parse import urljoin

__name__ = "dnsprobe"
__version__ = "0.1.alpha.3"
__description__ = "Domain Name System Probe."
__url_home__ = "https://github.com/DNSet/DNSProber"
__url_code__ = __url_home__
__url_docs__ = __url_home__
__url_bugs__ = urljoin(__url_home__, "issues")

# author
__author__ = "Mingzhe Zou"
__author_email__ = "zoumingzhe@outlook.com"

# deamon
__deamon_name__ = "dnsprobed"
__deamon_description__ = "Domain Name System Probe Deamon."

# config
DEFAULT_CONFIG_FILE = os.path.join("/", "etc", "dnsprobe.conf")
DEFAULT_SERVERS_DIR = os.path.join("/", "etc", "dnsprobe.nameservers")
