import configparser
import yaml
import logging

from .block import DataBlock, Mapping


class BaseConfigBlock(DataBlock):

    logger = logging.getLogger('BaseConfigBlock')

    def __init__(self, filename=None, string='', json_on_str=False, parse=None):
        self.filename = filename
        if parse is not None: self.parse = parse
        if filename is not None:
            with open(filename, 'r') as file:
                string = file.read()
        self.data = self.parse(string) if string else {}
        self.mapping = Mapping()
        if json_on_str:
            self.apply_json(copy=False)

    def apply_json(self, copy=True):
        if copy:
            new = self.datacopy()
        else:
            new = self
        for (section,name),value in self.items():
            if not isinstance(value,str):
                continue
            new[section,name] = self.get_json(section,name)
        return new

    def __getstate__(self):
        state = super(BaseConfigBlock,self).__getstate__()
        state['filename'] = self.filename
        return state


def parse_yaml(string):
    config = yaml.safe_load(string)
    data = dict(config)
    return data


def parse_ini(string):
    config = configparser.ConfigParser()
    config.read_string(string)
    data = {}
    for section in config.sections():
        data[section] = {}
        for name in config[section]:
            data[section][name] = config[section][name]
    return data


def ConfigBlock(filename=None):

    if filename is None:
        return BaseConfigBlock()
    if isinstance(filename,BaseConfigBlock):
        return filename
    if filename.endswith('.ini'):
        return BaseConfigBlock(filename,parse=parse_ini)
    return BaseConfigBlock(filename,parse=parse_yaml)
