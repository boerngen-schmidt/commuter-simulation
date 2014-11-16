__author__ = 'benjamin'

import logging
import logging.config

import yaml
from helper import file_finder


try:
    cfg_file = file_finder.find('logging.conf')
    with open(cfg_file, 'rt') as f:
        cfg= yaml.load(f.read())
        logging.config.dictConfig(cfg)
except:
    raise