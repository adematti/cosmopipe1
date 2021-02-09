import configparser
import yaml

from .block import DataBlock


class BaseConfigBlock(DataBlock):

    def __init__(self, filename=None, string='', json_on_str=False):
        self.filename = filename
        if filename is not None:
            with open(filename, 'r') as file:
                string = file.read()
        self.data = self.decode(string) if string else {}
        if json_on_str:
            self.apply_json(copy=False)

    def apply_json(self, copy=True):
        if copy:
            new = self.copy()
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


class YamlConfigBlock(BaseConfigBlock):

    @staticmethod
    def decode(string):
        config = yaml.safe_load(string)
        data = {(section,name):value for section in config for name,value in config[section].items()}
        return data


class IniConfigBlock(BaseConfigBlock):

    @staticmethod
    def decode(string):
        config = configparser.ConfigParser()
        config.read_string(string)
        data = {(section,name):value for section in config for name,value in config[section].items()}
        return data


def ConfigBlock(filename=None):

    if filename is None:
        return BaseConfigBlock()
    if isinstance(filename,BaseConfigBlock):
        return filename
    if filename.endswith('.ini'):
        return IniConfigBlock(filename)
    return YamlConfigBlock(filename)
