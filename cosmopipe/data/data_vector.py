import re
import logging
import copy
import json

import numpy as np

from cosmopipe.utils import BaseClass, savefile, MappingArray
from cosmopipe.plotting import PlottingStyle, saveplot


class DataVector(BaseClass):

    logger = logging.getLogger('DataVector')

    def __init__(self, x=None, y=None, proj=None, mapping_proj=None, **attrs):

        if isinstance(x,self.__class__):
            self.__dict__.update(x.__dict__)
            self.attrs.update(attrs)
            return

        self.attrs = attrs
        self._index_view = None
        if x is None:
            x = np.arange(len(y))
        if y is None:
            y = np.full(len(x),np.nan)

        y2dim = not np.isscalar(y[0])
        if y2dim:
            y2dim = len(y)
            self._x = np.tile(x.T,y2dim).T
            self._y = np.concatenate(y,axis=0)
        else:
            self._x = np.asarray(x)
            self._y = np.asarray(y)

        if len(self._x) != len(self._y):
            raise ValueError('x and y shapes cannot be matched.')

        self._proj = None
        if y2dim:
            if mapping_proj is None:
                mapping_proj = list(range(y2dim))
            lens = [0] + np.cumsum([len(y_) for y_ in y]).tolist()
            proj = - np.ones(self.size,dtype=int)
            for ip,il,iu in zip(range(len(mapping_proj)),lens[:-1],lens[1:]):
                proj[il:iu] = ip
            self._proj = MappingArray(proj,mapping=mapping_proj)
        elif proj is not None:
            self._proj = MappingArray(proj,mapping=mapping_proj)

    def get_index(self, concat=True, **kwargs):

        def _get_one_index(xlim=None, proj=None):
            mask = np.ones(self.size,dtype='?')
            if xlim is not None:
                tmp = (self._x >= xlim[0]) & (self._x <= xlim[-1])
                if self.ndim > 1: tmp = tmp.all(axis=-1)
                mask &= tmp
            if proj is not None:
                mask &= self._proj == proj
            index = np.flatnonzero(mask)
            if self._index_view is not None:
                index = self._index_view[np.isin(self._index_view,index)]
            return index

        if not kwargs:
            if concat:
                return _get_one_index()
            return [_get_one_index()]

        index = []
        for key,val in kwargs.items():
            if not isinstance(val,(list,np.ndarray)):
                kwargs[key] = [val]
        n = len(list(kwargs.values())[0])
        if not all(len(val) == n for val in kwargs.values()):
            raise IndexError('Input parameters {} have different lengths.'.format(kwargs))
        for i in range(n):
            index.append(_get_one_index(**{key:val[i] for key,val in kwargs.items()}))

        if concat:
            return np.concatenate(index)
        return index

    def projs(self):
        return self._proj.keys if self.has_proj() else None

    def has_proj(self):
        return self._proj is not None

    def view(self, **kwargs):
        new = self.copy()
        new._index_view = self.get_index(**kwargs)
        return new

    def __getitem__(self, mask):
        new = self.copy()
        new.attrs = copy.deepcopy(self.attrs)
        for key in ['_x','_y']:
            setattr(new,key,getattr(self,key)[mask])
        if self.has_proj(): new._proj = self._proj[mask]
        if new._index_view is not None:
            index = mask
            try:
                if isinstance(np.empty(1,dtype=mask.dtype)[0],np.bool_):
                    index = np.flatnonzero(mask)
            except AttributeError:
                pass
            new._index_view = new._index_view[np.isin(new._index_view,index)]
        return new

    def x(self, **kwargs):
        """Return x-coordinate of the data vector."""
        index = self.get_index(**kwargs)
        return self._x[index]

    def y(self, **kwargs):
        """Return y-coordinate of the data vector."""
        index = self.get_index(**kwargs)
        return self._y[index]

    def proj(self, **kwargs):
        """Return projection."""
        index = self.get_index(**kwargs)
        return self._proj[index].asarray()

    @property
    def ndim(self):
        if len(self.shape) > 1: return self.shape[1]
        return 1

    def __len__(self):
        return self.size

    @property
    def size(self):
        return self.shape[0]

    @property
    def shape(self):
        return self._x.shape

    @classmethod
    def read_header_txt(cls, file, mapping_header=None, comments='#'):
        attrs = {}
        mapping_header = mapping_header or {}
        mapping_header.setdefault('proj','.*?projection = (.*)')
        for line in file:
            if not line.startswith(comments):
                break
            for key,pattern in mapping_header.items():
                if isinstance(pattern,tuple):
                    pattern,decode = pattern
                else:
                    decode = None
                match = re.match(pattern,line[len(comments):])
                if match is not None:
                    val = match.group(1)
                    cls.logger.info('Setting attribute {} = {} from header.'.format(key,val))
                    if decode is None:
                        val = json.loads(val)
                    elif isinstance(decode,str):
                        val = {'int':int,'float':float,'bool':bool}[decode](val)
                    else:
                        val = decode(val)
                    cls.logger.info('...of type {}.'.format(type(val)))
                    attrs[key] = val
        if 'proj' in attrs and not isinstance(attrs['proj'],bool):
            attrs['mapping_proj'] = attrs['proj']
            attrs['proj'] = True
        return attrs

    @classmethod
    def load_txt(cls, filename, mapping_header=None, xdim=None, comments='#', usecols=None, skip_rows=0, max_rows=None, **attrs):

        cls.logger.info('Loading {}.'.format(filename))
        with open(filename,'r') as file:
            header = cls.read_header_txt(file,mapping_header=mapping_header,comments=comments)

        attrs = {**header,**attrs}
        col_proj = isinstance(attrs.get('proj',None),bool) and attrs['proj']
        x,y,proj = [],[],[]

        def str_to_y(e):
            return float(e)

        def str_to_x(row):
            return [float(e) for e in row]

        with open(filename,'r') as file:
            for iline,line in enumerate(file):
                if iline < skip_rows: continue
                if max_rows is not None and iline >= skip_rows + max_rows: break
                if line.startswith(comments): continue
                row = line.split()
                if usecols is None:
                    usecols = range(len(row))
                if xdim is None:
                    if len(usecols) == 2:
                        xdim = 1
                    elif col_proj:
                        xdim = len(usecols) - 2
                    elif attrs.get('mapping_proj',None) is not None:
                        xdim = len(usecols) - len(attrs['mapping_proj'])
                    else:
                        raise ValueError('You should provide xdim!')

                row = [row[icol] for icol in usecols]
                if col_proj:
                    x.append(str_to_x(row[1:-1]))
                    y.append(str_to_y(row[-1]))
                    proj.append(row[0])
                else:
                    x.append(str_to_x(row[:xdim]))
                    y.append(str_to_x(row[xdim:]))

        x,y = np.squeeze(x),np.squeeze(y).T
        if col_proj:
            attrs['proj'] = proj

        attrs.setdefault('filename',filename)
        return cls(x=x,y=y,**attrs)

    @savefile
    def save_txt(self, filename, comments='#', fmt='.18e'):
        with open(filename,'w') as file:
            for key,val in self.attrs.items():
                file.write('{}{} = {}\n'.format(comments,key,json.dumps(val)))
            if self.has_proj():
                file.write('{}projection = {}\n'.format(comments,json.dumps(True)))
            for ix,x in enumerate(self._x):
                if self.has_proj():
                    file.write('{} {:{fmt}} {:{fmt}}\n'.format(self._proj[ix],self._x[ix],self._y[ix],fmt=fmt))
                else:
                    file.write('{:{fmt}} {:{fmt}}\n'.format(self._x[ix],self._y[ix],fmt=fmt))

    def __getstate__(self):
        state = super(DataVector,self).__getstate__()
        for key in ['_x','_y','_index_view','_proj']:
            state[key] = getattr(self,key)
        if self.has_proj():
            state['_proj'] = self._proj.__getstate__()
        return state

    def __setstate__(self, state):
        super(DataVector,self).__setstate__(state)
        if self._proj is not None:
            self._proj = MappingArray.from_state(self._proj)

    @saveplot()
    def plot(self, ax, style=None, **kwargs_style):
        if self.ndim > 1:
            raise NotImplementedError('No plot method defined for {:d}-dimensional data vector.'.format(self.ndim))
        style = PlottingStyle(style,**kwargs_style)
        if style.projs == [None]: style.set_sorted_projs(self.projs())
        style.set_ax(ax)
        for proj in style.projs:
            ax.plot(self.x(proj=proj),style.y(self.x(proj=proj),self.y(proj=proj)),label=style.proj_to_label(proj),**style.proj_to_kwplt(proj))
        if style.projs != [None]: ax.legend(fontsize=style.labelsize)


### Pipeline stuff ###
from cosmopipe.pipeline import SectionBlock, section_names

def get_data_from_options(options):
    data_file = options.get_string('data_file')
    if data_file.split('.')[-1] == 'txt':
        kwargs = {'xdim':options.get_int('xdim',None),'comments':options.get_string('comments','#'),'usecols':options.get_int_array_1d('usecols',None)}
        kwargs.update({'skip_rows':options.get_int('skip_rows',0),'max_rows':options.get_int('max_rows',None)})
        kwargs['proj'] = options.get_bool('col_proj',False)
        kwargs['mapping_header'] = options.get_json('mapping_header',None)
        kwargs['mapping_proj'] = options.get_json('mapping_proj',None,catch=lambda s: s.split())
        data = DataVector.load_txt(data_file,**kwargs)
    else:
        data = DataVector.load(data_file)
    return data

def setup(name, config_block, data_block):
    options = SectionBlock(config_block,name)
    data = get_data_from_options(options)
    projs = data.projs()
    if options.has_value('xlim'):
        xlims = options.get_json('xlim')
        if not isinstance(xlims,list):
            projs = list(xlims.keys())
            xlims = [xlims[proj] for proj in projs]
    else:
        xlims = [[-np.inf,np.inf] for proj in projs]
    data = data.view(proj=projs,xlim=xlims)

    data_block[section_names.data,'xlims'] = np.array(xlims)
    data_block[section_names.data,'projs'] = np.array(projs)
    data_block[section_names.data,'proj'] = data.proj()
    data_block[section_names.data,'x'] = data.x()
    data_block[section_names.data,'y'] = data.y()
    return 0

def execute(name, config_block, data_block):
    return 0

def cleanup(name, config_block, data_block):
    return 0
