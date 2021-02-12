import logging
from collections import UserList
import math
import re

import numpy as np

from ..utils import BaseClass
from .config import parse_yaml, parse_ini


class ParamError(Exception):

    pass


class BaseParamBlock(UserList):

    logger = logging.getLogger('BaseParamBlock')

    def __init__(self, filename=None, string='', parse=None):
        self.filename = filename
        if parse is not None: self.parse = parse
        if filename is not None:
            with open(filename, 'r') as file:
                string = file.read()
        data = self.parse(string) if string else {}
        self.data = []
        for name,conf in data.items():
            self.data.append(Param(name=name,**conf))

    def __getitem__(self, name):
        if isinstance(name,str):
            name = self._get_index(name)
        return self.data[name]

    def __setitem__(self, name, item):
        if isinstance(name,str):
            if item.name != name:
                raise KeyError('Parameter {} should be indexed by name (incorrect {})'.format(item.name,name))
            try:
                name = self._get_index(name)
            except ValueError:
                self.append(item)
                return
        self.data[name] = item

    def keys(self):
        return (item.name for item in self.data)

    def _get_index(self, name):
        return list(self.keys()).index(name)

    def __contains__(self, name):
        if isinstance(name,str):
            return name in self.keys()
        return name in self.data

    def update(self, other):
        for name in other.keys():
            self[name] = other[name]


def ParamBlock(filename=None):

    if filename is None:
        return BaseParamBlock()
    if isinstance(filename,BaseParamBlock):
        return filename
    if filename.endswith('.ini'):
        return BaseParamBlock(filename,parse=parse_ini)
    return BaseParamBlock(filename,parse=parse_yaml)


class Param(BaseClass):

    def __init__(self, name=None, value=None, fixed=None, limit=None, prior=None, ref=None, latex=None):
        self.name = name
        if isinstance(limit,str):
            limit = tuple(float(m) for m in limit.split())
        elif limit is not None:
            limit = tuple(limit)
        self.prior = Prior(prior,limit=limit)
        if value is None:
            if self.prior.proper():
                self.value = np.mean(self.prior.limit)
            else:
                raise ParamError('An initial value must be provided for parameter {}'.format(self.name))
        else:
            self.value = float(value)
        if ref is not None:
            self.ref = Prior(ref,limit=limit)
        else:
            self.ref = self.prior.copy()
        self.latex = latex or self.name
        if fixed is None:
            if limit is not None or prior is not None:
                fixed = False
            else:
                fixed = True
        if isinstance(fixed,str):
            convert = {'true':True,'false':False,'t':True,'f':False,'yes':True,'no':False,'y':True,'n':False}
            if fixed.lower() in convert:
                fixed = convert[fixed.lower()]
            else:
                raise ParamError('Cannot convert fixed = {} into a boolean for parameter {};\
                                it should be one of {}'.format(fixed,self.name,list(convert.keys())))
        self.fixed = bool(fixed)

    def add_suffix(self, suffix):
        self.name = '{}_{}'.format(self.name,suffix)
        match1 = re.match('(.*)_(.)$',self.latex)
        match2 = re.match('(.*)_{(.*)}$',self.latex)
        if match1 is not None:
            self.latex = '%s_{%s,\\mathrm{%s}}' % (match1.group(1),match1.group(2),self.name)
        elif match2 is not None:
            self.latex = '%s_{%s,\\mathrm{%s}}' % (match2.group(1),match2.group(2),self.name)
        else:
            self.latex = '%s_{\\mathrm{%s}}' % (self.latex,self.name)

    def __getstate__(self):
        state = {}
        for key in ['name','value','limit','latex','fixed']:
            state[key] = getattr(self,key)
        for key in ['prior','ref']:
            state[key] = getattr(self,key).__getstate__()


def Prior(prior,limit=None):

    if isinstance(prior,BasePrior):
        if limit is not None:
            prior.set_limit(limit)
        return prior

    if prior is None:
        return UniformPrior()

    args = prior.split()
    cls = args[0].strip()
    convert = {'uniform':UniformPrior,'normal':NormalPrior}
    if cls.lower() in convert:
        cls = convert[cls.lower()]
    else:
        raise ParamError('Unable to understand prior {}; it should be one of {}'.format(cls,list(convert.keys())))

    args = [float(arg) for arg in args[1:]]
    if cls is UniformPrior:
        if limit is not None:
            if len(args) == 2:
                cls.logger.warning('Limits are provided in addition to uniform prior; use the limits of the latter.')
            else:
                args = limit
        return cls(*args)

    return cls(*args,limit=limit)


class PriorError(Exception):

    pass


class BasePrior(BaseClass):

    logger = logging.getLogger('BasePrior')
    _leys = ['limit']

    def __init__(self, dist='uniform', limit=None):
        if isinstance(dist,BasePrior):
            self.__dict__.update(dist.__dict__)
            if limit is not None:
                self.set_limit(limit)

    def set_limit(self, limit):
        if not limit:
            limit = (-np.inf,np.inf)
        self.limit = limit
        if self.limit[1] <= self.limit[0]:
            raise PriorError('Prior range {} has min greater than max'.format(self.limit))
        if np.isinf(self.limit).any():
            return 1
        return 0

    def isin(self, x):
        return  self.limit[0] < x < self.limit[1]

    def __call__(self, x):
        raise NotImplementedError

    def __setstate__(self,state):
        super(BasePrior,self).__setstate__(state)
        self.set_limit(self.limit)

    def __getstate__(self):
        state = {}
        for key in self._keys:
            state[key] = getattr(self,key)
        return state

    def proper(self):
        return True


class UniformPrior(BasePrior):

    logger = logging.getLogger('UniformPrior')

    def __init__(self, *limit):
        self.set_limit(limit)

    def set_limit(self, limit):
        if super(UniformPrior,self).set_limit(limit) == 1:
            self.norm = 0.  # we tolerate improper priors
        else:
            self.norm = -np.log(limit[1] - limit[0])

    def __call__(self, x):
        if not self.isin(x):
            return -np.inf
        return self.norm

    def sample(self, size=None, seed=None, rng=None):
        if not self.proper():
            raise PriorError('Cannot sample from improper prior')
        self.rng = rng or np.random.RandomState(seed=seed)
        return self.rng.uniform(*self.limit,size=size)

    def proper(self):
        return not np.isinf(self.limit).any()

class NormalPrior(BasePrior):

    logger = logging.getLogger('NormalPrior')
    _keys = ['limit','loc','scale']

    def __init__(self, loc=0., scale=1., limit=None):
        self.loc = loc
        self.scale = scale
        self.set_limit(limit)

    @property
    def scale2(self):
        return self.scale**2

    def set_limit(self, limit):
        super(NormalPrior,self).set_limit(limit)

        def cdf(x):
            return 0.5*(math.erf(x/math.sqrt(2.)) + 1)

        a,b = [(x-self.loc)/self.scale for x in limit]
        self.norm = np.log(cdf(b) - cdf(a)) + 0.5*np.log(2*np.pi*self.scale**2)

    def __call__(self, x):
        if not self.isin(x):
            return -np.inf
        return -0.5 * ((x-self.loc) / self.scale)**2 - self.norm

    def sample(self, size=None, seed=None, rng=None):
        self.rng = rng or np.random.RandomState(seed=seed)
        if self.limit == (-np.inf,np.inf):
            return self.rng.normal(loc=self.loc,scale=self.scale,size=size)
        samples = []
        isscalar = size is None
        if isscalar: size = 1
        while len(samples) < size:
            x = self.rng.normal(loc=self.loc,scale=self.scale)
            if self.isin(x):
                samples.append(x)
        if isscalar:
            return samples[0]
        return np.array(samples)
