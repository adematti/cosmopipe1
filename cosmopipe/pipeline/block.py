import re
import json
import logging
from collections import UserDict

import numpy as np

from ..utils import BaseClass


class BlockError(Exception):

    _messages = {'put_exists': 'Tried to overwrite "{name}" in section [{section}]. Use the replace function to over-write.',
                'replace_notfound': 'Tried to replace "{name}" in section [{section}], which does not exist. Use the put function to add a new key.',
                'get_notfound': 'Tried to get "{name}" in section [{section}], which does not exist.',
                'wrong_type': 'Wrong type for "{name}" in section [{section}].',
                'section_exists': 'Section [{section}] already exists.'}

    def __init__(self, status, section, name=None, type_=None):
        self.status = status
        self.name = name
        self.section = section
        self.type_ = type_

    def __str__(self):
        return self._messages[self.status].format(name=self.name,section=self.section,type_=type_)


class DataBlock(UserDict,BaseClass):

    logger = logging.getLogger('DataBlock')

    def get_type(self, section, name, type_, *args, **kwargs):

        if not self.has_value(section,name):
            return self.get(section,name,*args,**kwargs)

        value = self.get(section, name)
        convert = {'double':'float','string':'str'}

        def get_type_from_str(type_):
            return __builtins__[type_]

        def get_nptype_from_str(type_):
            return {'bool':np.bool_,'int':np.integer,'float':np.floating,'str':np.string_}[type_]

        error = BlockError('wrong_type',section,name,type_=str(type_))
        if isinstance(type_,str):
            type_ = convert.get(type_,type_)
            try:
                type_ = get_type_from_str(type_)
                if not isinstance(value,type_):
                    raise error
            except KeyError:
                try:
                    match = re.match('(.*)_array_(.*)d',type_)
                    type_,ndim = match.group(1),int(match.group(2))
                    if isinstance(value,list) and not isinstance(value[0],get_type_from_str(type_)):
                        raise error
                    type_ = get_nptype_from_str(type_)
                    if not np.issubdtype(value.dtype,type_) or not value.ndim == ndim:
                        raise error
                except (AttributeError,KeyError):
                    raise error
        elif not isinstance(value,type_):
            raise error
        return value

    def get_json(self, section, name, *args, catch=True, **kwargs):

        if not self.has_value(section,name):
            return self.get(section,name,*args,**kwargs)

        try:
            value = self.get_string(section,name)
        except BlockError as e:
            if e.status == 'wrong_type':
                return self.get(section,name)
            raise e
        try:
            value = json.loads(value)
        except json.decoder.JSONDecodeError as e:
            if callable(catch):
                value = catch(value)
            elif not catch:
                raise e
        return value

    def get(self, section, name, *args, **kwargs):
        if (section,name) in self.data:
            return self.data[section,name]
        if 'default' in kwargs:
            return kwargs['default']
        try:
            return args[0]
        except IndexError:
            raise BlockError('get_notfound',section,name)

    def put(self, section, name, value):
        if self.has_value(section, name):
            raise BlockError('put_exists',section,name)
        self.data[section,name] = value

    def replace(self, section, name, value):
        if not self.has_value(section, name):
            raise BlockError('replace_notfound',section,name)
        self.data[section,name] = value

    def set(self, section, name, value):
        self.data[section,name] = value

    def has_value(self, section, name):
        return (section,name) in self.data

    def has_section(self, section):
        return section in self.sections()

    def delete_section(self, section):
        for key in self.data.keys():
            if key[0] == section:
                del self[key]

    def rename_section(self, old, new):
        if new in self.sections():
            raise BlockError('section_exists',new)
        for (section,name) in self.data.keys():
            if section == old:
                self.set(new,name,self.data[section,name])

    def sections(self):
        return [key[0] for key in self.data.keys()]

    def keys(self, section=None):
        if section is None:
            sections = self.sections()
        else:
            sections = [section]
        keys = []
        for key in self.data.keys():
            if key[0] in sections:
                keys.append(key)
        return keys

    def __getstate__(self):
        return {'data':self.data}


def _make_getter(type_):

    def getter(self, section, name, *args, **kwargs):
        return self.get_type(section,name,type_,*args,**kwargs)

    return getter


for type_ in ['bool','int','float','string','double','int_array_1d']:
    setattr(DataBlock,'get_{}'.format(type_),_make_getter(type_))


class SectionBlock(UserDict):

    def __init__(self, block, section):
        self.block = block
        self.section = section
        self.data = {key[1]:block[key] for key in block.keys(section=section)}

    def has_value(self, name):
        return self.block.has_value(self.section,name)

    def __getitem__(self, key):
        return self.block[self.section,key]


def _make_getter(name):

    def getter(self, key, *args, **kwargs):
        return getattr(self.block,name)(self.section,key,*args,**kwargs)

    return getter


for name in dir(DataBlock):

    if name.startswith('get'):
        setattr(SectionBlock,name,_make_getter(name))
