"""Definition of DataBlock and related classes."""

import re
import json
import logging

import numpy as np

from ..utils import BaseClass
from . import section_names

class MappingError(Exception):

    pass


class Mapping(BaseClass):

    def __init__(self, data=None):
        if isinstance(data,Mapping):
            self.__dict__.update(data.__dict__)
            return
        self.data = data or {}
        if isinstance(data,str):
            self.data = {}
            for tmap in data.split():
                old,new = (tuple(section_name.strip().split('.')) for section_name in tmap.split(','))
                if not len(old) == len(new):
                    raise MappingError('In mapping {} = {}, both terms should be same size (1 or 2)'.format(old,new))
                if len(old) == 1:
                    old,new = old[0],new[0]
                self.data[new] = old
        self._set_invdata()

    def _set_invdata(self):
        self.invdata = {val:key for key,val in self.data.items()}

    def update(self, other):
        try:
            self.data.update(other.data)
        except AttributeError:
            self.data.update(other)
        self._set_invdata()

    def get(self, *args):
        if len(args) == 1:
            return self.data.get(args[0],args[0])
        return self.data.get(args,args)

    def invget(self, args):
        if len(args) == 1:
            return self.invdata.get(args[0],args[0])
        return self.invdata.get(args,args)

    def copy(self):
        new = super(Mapping,self).copy()
        new.data = self.data.copy()
        new._set_invdata()
        return new

    def keys(self):
        return self.data.keys()

    def items(self):
        for key in self.keys():
            yield key,self.data[key]

    def __getstate__(self):
        return {'data':self.data,'invdata':self.invdata}

    def __str__(self):
        return str(self.data)


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


class DataBlock(BaseClass):
    """
    This is the data structure which is fed to all modules.

    It is essentially a dictionary, with elements to be accessed through the key (section, name).
    Most useful methods are those to get (get, get_type, get_[type]...) and set elements.

    >>> data_block = DataBlock({'section1':{'name1':1}})
    >>> data_block.get('section1','name1')
    1
    >>> data_block.get_int('section1','name1')
    1
    >>> data_block.get_string('section1','name1')
    Traceback (most recent call last):
        ...
    cosmopipe.pipeline.block.BlockError: Wrong type for "name1" in section [section1].
    """
    logger = logging.getLogger('DataBlock')

    def __init__(self, data=None, mapping=None):
        """
        Initialise :class:`DataBlock`.

        Parameters
        ----------
        data : dict, default=None
            Double level dictionary, where the element corresponding to ``section1``, ``name1`` can be accessed through::

                data[section1][name1]

        mapping : Mapping, dict, default=None
            Mapping ``key1`` -> ``key2``. When accessing the :class:`DataBlock` through ``key1``, will internally use ``key2``.
            ``key1`` and ``key2`` can be a section alone or a tuple ``section1``, ``name1``
        """
        mapping = Mapping(mapping)
        if isinstance(data,DataBlock):
            self.__dict__.update(data.__dict__)
            self.mapping.update(mapping)
            return
        self.data = data or {}
        for section in section_names.nocopy:
            self.data[section] = {}
        self.mapping = mapping

    def get_type(self, section, name, type_, *args, **kwargs):

        if not self.has_value(section,name):
            return self.get(section,name,*args,**kwargs)

        value = self.get(section,name)
        convert = {'double':'float','string':'str'}

        def get_type_from_str(type_):
            return __builtins__.get(type_,None)

        def get_nptype_from_str(type_):
            return {'bool':np.bool_,'int':np.integer,'float':np.floating,'str':np.string_}.get(type_,None)

        error = BlockError('wrong_type',section,name,type_=str(type_))
        if isinstance(type_,str):
            type_ = convert.get(type_,type_)
            type_py = get_type_from_str(type_)
            if type_py is not None:
                if not isinstance(value,type_py):
                    raise error
            else:
                match = re.match('(.*)_array_(.*)d',type_)
                if match is None:
                    raise error
                ndim,type_ = int(match.group(2)),match.group(1)
                if isinstance(value,list):
                    type_py = get_type_from_str(type_)
                    if type_py is None or not isinstance(value[0],type_py):
                        raise error
                else:
                    type_np = get_nptype_from_str(type_)
                    if type_np is None or not np.issubdtype(value.dtype,type_np) or not value.ndim == ndim:
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
        except json.decoder.JSONDecodeError:
            if callable(catch):
                value = catch(value)
            elif not catch:
                raise
        return value

    def get(self, section, name, *args, **kwargs):
        if self.has_value(section,name):
            section,name = self.mapping.get(section,name)
            return self.data[section][name]
        if 'default' in kwargs:
            return kwargs['default']
        if len(args):
            return args[0]
        raise BlockError('get_notfound',section,name)

    def put(self, section, name, value):
        if self.has_value(section, name):
            raise BlockError('put_exists',section,name)
        self.set(section,name,value)

    def replace(self, section, name, value):
        if not self.has_value(section,name):
            raise BlockError('replace_notfound',section,name)
        self.data[section][name] = value

    def set(self, section, name, value):
        section,name = self.mapping.get(section,name)
        if section not in self.sections():
            self.data[section] = {}
        self.data[section][name] = value

    def has_value(self, section, name):
        section,name = self.mapping.get(section,name)
        return section in self.data and name in self.data[section]

    def has_section(self, section):
        return section in self.sections()

    def delete_section(self, section):
        section = self.mapping.get(section)
        del self.data[section]

    def rename_section(self, old, new):
        if new in self.sections():
            raise BlockError('section_exists',new)
        new = self.mapping.get(new)
        old = self.mapping.get(old)
        self.data[new] = self.data[old]
        del self.data[old]

    def sections(self):
        return (self.mapping.invget(section) for section in self.data.keys())

    def keys(self, section=None):
        if section is None:
            sections = self.sections()
        else:
            sections = [section]
        for sec in sections:
            for name in self[sec]:
                yield sec,name

    def __str__(self):
        return str(self.data)

    def __getitem__(self, section_name):
        if isinstance(section_name,tuple):
            return self.get(*section_name)
        return self.data[self.mapping.get(section_name)]

    def __setitem__(self, section_name, value):
        if isinstance(section_name,tuple):
            self.set(*section_name,value)
        self.data[self.mapping.get(section_name)] = value

    def __delitem__(self, section_name):
        if isinstance(section_name,tuple):
            section,name = self.mapping.get(*section_name)
            del self.data[section][name]
        else:
            del self.data[self.mapping.get(section_name)]

    def __contains__(self, section_name):
        if isinstance(section_name,tuple):
            return self.has_value(*section_name)
        return section_name in self.data

    def items(self, section=None):
        for key in self.keys(section=section):
            yield key, self.get(*key)

    def __getstate__(self):
        return {'data':self.data,'mapping':self.mapping.__getstate__()}

    def __setstate__(self, state):
        super(DataBlock,self).__setstate__(state)
        self.mapping = Mapping.from_state(state)

    def update(self, other):
        if isinstance(other, dict):
            return self.data.update(other)
        return self.data.update(other.data)

    def datacopy(self, nocopy=None):
        if nocopy is None:
            nocopy = section_names.nocopy
        new = super(DataBlock,self).copy()
        new.data = self.data.copy()
        for section in nocopy:
            new.data[section] = self.data[section]
        new.mapping = self.mapping.copy()
        return new


def _make_getter(type_):

    def getter(self, section, name, *args, **kwargs):
        return self.get_type(section,name,type_,*args,**kwargs)

    return getter


for type_ in ['bool','int','float','string','double','int_array_1d']:
    setattr(DataBlock,'get_{}'.format(type_),_make_getter(type_))


class SectionBlock(object):

    def __init__(self, block, section):
        self.block = block
        self.section = section

    def __str__(self):
        return str(self.block[self.section])

    def items(self):
        yield from self.block[self.section].items()

    def has_value(self, name):
        return self.block.has_value(self.section,name)

    def __getitem__(self, key):
        return self.block[self.section,key]

    def __setitem__(self, key, value):
        self.block[self.section,key] = value

    def keys(self):
        return (name for section,name in self.block.keys(section=self.section))


def _make_getter(name):

    def getter(self, key, *args, **kwargs):
        return getattr(self.block,name)(self.section,key,*args,**kwargs)

    return getter


for name in dir(DataBlock):

    if name.startswith('get'):
        setattr(SectionBlock,name,_make_getter(name))
