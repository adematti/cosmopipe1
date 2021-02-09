import os
import sys
import functools
import logging
from collections import UserDict

import numpy as np

def get_base_dir():
    return os.path.dirname(os.path.realpath(__file__))


def setup_logging(level=logging.INFO, stream=sys.stdout, filename=None, filemode='w', **kwargs):
    """
    Set up logging.

    Parameters
    ----------
    level : string, int, default=logging.INFO
        Logging level.

    stream : _io.TextIOWrapper, default=sys.stdout
        Where to stream.

    filename : string, default=None
        If not ``None`` stream to file name.

    filemode : string, default='w'
        Mode to open file, only used if filename is not ``None``.

    kwargs : dict
        Other arguments for :func:`logging.basicConfig`.
    """
    # Cannot provide stream and filename kwargs at the same time to logging.basicConfig, so handle different cases
    # Thanks to https://stackoverflow.com/questions/30861524/logging-basicconfig-not-creating-log-file-when-i-run-in-pycharm
    if isinstance(level,str):
        level = {'info':logging.INFO,'debug':logging.DEBUG,'warning':logging.WARNING}[level]
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    fmt = logging.Formatter(fmt='%(asctime)s %(name)-25s %(levelname)-8s %(message)s',datefmt='%m-%d %H:%M ')
    if filename is not None:
        mkdir(os.path.dirname(filename))
        handler = logging.FileHandler(filename,mode=filemode)
    else:
        handler = logging.StreamHandler(stream=stream)
    handler.setFormatter(fmt)
    logging.basicConfig(level=level,handlers=[handler],**kwargs)


def mkdir(filename):
    try:
        os.makedirs(filename) # MPI...
    except OSError:
        return


def savefile(func):
    @functools.wraps(func)
    def wrapper(self, filename, *args, **kwargs):
        dirname = os.path.dirname(filename)
        mkdir(dirname)
        self.logger.info('Saving to {}.'.format(filename))
        return func(self,filename,*args,**kwargs)
    return wrapper


class BaseClass(object):

    def __setstate__(self,state):
        self.__dict__.update(state)

    def __getstate__(self):
        state = {}
        if hasattr(self,'attrs'): state['attrs'] = self.attrs
        return state

    @classmethod
    def from_state(cls, state):
        new = object.__new__(cls)
        new.__setstate__(state)
        return new

    @classmethod
    def load(cls, filename):
        cls.logger.info('Loading {}.'.format(filename))
        state = np.load(filename,allow_pickle=True)[()]
        return cls.from_state(state)

    @savefile
    def save(self, filename):
        np.save(filename,self.__getstate__())

    def copy(self):
        """Return shallow copy of ``self``."""
        new = object.__new__(self.__class__)
        new.__dict__.update(self.__dict__)
        return new


class OrderedMapping(BaseClass,UserDict):

    def __init__(self, d=None, order=None):
        self.data = d or {}
        if order is not None and not callable(order):

            def order_(key):
                try:
                    return order.index(key)
                except ValueError:
                    return -1

            self.order = order_
        else:
            self.order = order

    def keys(self):
        """Return keys sorted by chronological order in :mod:`legacypipe.runbrick`."""
        return sorted(self.data.keys(),key=self.order)

    def __iter__(self):
        """Iterate."""
        return iter(self.keys())


class MappingArray(BaseClass):

    def __init__(self, array, mapping=None, dtype=None):

        if isinstance(array,self.__class__):
            self.__dict__.update(array.__dict__)
            return

        if mapping is None:
            mapping = np.unique(array).tolist()
            mapping = {m:m for m in mapping}

        self.keys = mapping
        if dtype is None:
            nbytes = 2**np.ceil(np.log2(np.ceil((np.log2(len(self.keys)+1) + 1.)/8.)))
            dtype = 'i{:d}'.format(int(nbytes))

        try:
            self.array = - np.ones_like(array,dtype=dtype)
            array = np.array(array)
            keys = []
            for key in mapping.keys():
                keys.append(key)
                self.array[array.astype(type(key)) == key] = keys.index(key)
            self.keys = keys
        except AttributeError:
            self.array = np.array(array,dtype=dtype)

    def __eq__(self,other):
        if other in self.keys:
            return self.array == self.keys.index(other)
        return self.array == other

    def __getitem__(self, name):
        try:
            return self.keys[self.array[name]]
        except TypeError:
            new = self.copy()
            new.keys = self.keys.copy()
            new.array = self.array[name]
            return new

    def __setitem__(self, name, item):
        self.array[name] = self.keys.index(item)

    @property
    def shape(self):
        return self.array.shape

    @property
    def size(self):
        return self.array.size

    def asarray(self):
        return np.array([self.keys[a] for a in self.array.flat]).reshape(self.shape)

    def __getstate__(self):
        state = super(MappingArray,self).__getstate__()
        for key in ['array','keys']:
            state[key] = getattr(self,key)
        return state


def blockinv(blocks,inv=np.linalg.inv):
    A = blocks[0][0]
    if (len(blocks),len(blocks[0])) == (1,1):
        return inv(A)
    B = np.bmat(blocks[0][1:]).A
    C = np.bmat([b[0].T for b in blocks[1:]]).A.T
    invD = blockinv([b[1:] for b in blocks[1:]],inv=inv)

    def dot(*args):
        return np.linalg.multi_dot(args)

    invShur = inv(A - dot(B,invD,C))
    return np.bmat([[invShur,-dot(invShur,B,invD)],[-dot(invD,C,invShur), invD + dot(invD,C,invShur,B,invD)]]).A


def txt_to_latex(txt):
    latex = ''
    txt = list(txt)
    for c in txt:
        latex += c
        if c == '_':
            latex += '{'
            txt += '}'
    return latex


def snake_to_pascal_case(snake):
    words = snake.split('_')
    return ''.join(map(str.title,words))
