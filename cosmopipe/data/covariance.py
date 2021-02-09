import logging
import json

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize

from .data_vector import DataVector
from cosmopipe.utils import BaseClass, savefile, blockinv
from cosmopipe.plotting import PlottingStyle, suplabel, saveplot


class CovarianceMatrix(DataVector):

    logger = logging.getLogger('CovarianceMatrix')

    def __init__(self, covariance, x=None, mean=None, proj=None, mapping_proj=None, **attrs):

        if isinstance(covariance,self.__class__):
            self.__dict__.update(covariance.__dict__)
            self.attrs.update(attrs)
            return

        if not isinstance(x,tuple):
            x = (x,)*covariance.ndim
        if not isinstance(mean,tuple):
            mean = (mean,)*covariance.ndim
        if not isinstance(proj,tuple):
            proj = (proj,)*covariance.ndim
        if not isinstance(mapping_proj,tuple):
            mapping_proj = (mapping_proj,)*covariance.ndim
        self._x = list(DataVector(x=x_,y=mean_,proj=proj_,mapping_proj_=mapping_proj_)\
                                for x_,mean_,proj_,mapping_proj_ in zip(x,mean,proj,mapping_proj))
        self._covariance = covariance
        self.attrs = attrs

    def get_index(self, axes=None, **kwargs):
        if axes is None:
            axes = range(self.ndim)
        if np.isscalar(axes):
            axes = [axes]
        for key,val in kwargs.items():
            if not isinstance(val,tuple):
                kwargs[key] = (val,)*len(axes)
        index = [None for axis in range(self.ndim)]
        for axis in axes:
            index[axis] = self._x[axis].get_index(**{key:val[axis] for key,val in kwargs.items()})
        return index

    def copy(self):
        new = super(CovarianceMatrix,self).copy()
        for axis,x in enumerate(self._x):
            new._x[axis] = x.copy()
        return new

    def view(self, **kwargs):
        new = self.copy()
        masks = self.get_index(**kwargs)
        for iaxis,x in enumerate(new._x):
            x._index_view = masks[iaxis]
        return new

    def __getitem__(self, mask):
        new = self.copy()
        if not isinstance(mask,tuple):
            mask = (mask,)*self.ndim
        for ix,m in enumerate(mask):
            self._x[ix] = self._x[ix][m]
        new._covariance = new._covariance[np.ix_(*mask)]
        return new

    def x(self, **kwargs):
        """Return x-coordinates of the data vector."""
        indices = self.get_index(**kwargs)
        return [x.x()[index] for x,index in zip(self._x,indices)]

    def y(self, **kwargs):
        """Return mean data vector."""
        indices = self.get_index(**kwargs)
        return [x.y()[index] for x,index in zip(self._x,indices)]

    def std(self, **kwargs):
        return np.diag(self.cov(**kwargs))**0.5

    def cov(self, **kwargs):
        return self._covariance[np.ix_(*self.get_index(**kwargs))]

    def invcov(self, block=True, inv=np.linalg.inv, **kwargs):
        if block:
            indices = self.get_index(concat=False,**kwargs)
            cov = [[self._covariance[np.ix_(ind1,ind2)] for ind2 in indices[-1]] for ind1 in indices[0]]
            return blockinv(cov,inv=inv)
        return inv(self.cov(**kwargs))

    def corr(self, **kwargs):
        cov = self.cov(**kwargs)
        stdinv = np.diag(1./np.diag(cov)**0.5)
        return stdinv.dot(cov).dot(stdinv)

    @property
    def ndim(self):
        return len(self.shape)

    @property
    def shape(self):
        return tuple(x.size for x in self._x)

    def __getstate__(self):
        state = BaseClass.__getstate__(self)
        for key in ['_covariance']:
            state[key] = getattr(self,key)
        state['_x'] = [x.__getstate__() for x in self._x]
        return state

    def __setstate__(self,state):
        BaseClass.__setstate__(self,state)
        self._x = [DataVector.from_state(x) for x in self._x]

    @classmethod
    def load_txt(cls, filename, data=None, mapping_header=None, xdim=None, comments='#', usecols=None, skip_rows=0, max_rows=None, **attrs):
        cls.logger.info('Loading {}.'.format(filename))

        with open(filename,'r') as file:
            header = cls.read_header_txt(file,mapping_header=mapping_header,comments=comments)

        attrs = {**header,**attrs}
        col_proj = isinstance(attrs.get('proj',None),bool) and attrs['proj']
        x,cov,mapping = [[],[]],[],[]
        proj,projx = [[],[]],[[],[]]

        def str_to_y(e):
            return float(e)

        if data is not None:

            def str_to_x(row):
                return [int(e) for e in row]

        else:

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
                ixl = 2 if col_proj else 0
                if xdim is None:
                    nx = len(usecols) - 1 - ixl
                    if nx % 2 == 0:
                        xdim = (nx//2,nx//2)
                    else:
                        raise ValueError('x vectors do not have the same dimensions; please provide xdim')
                slx = (slice(ixl,ixl+xdim[0]),slice(ixl+xdim[0],ixl+xdim[0]+xdim[1]))
                row = [row[icol] for icol in usecols]
                mapping_ = []
                if col_proj:
                    for i in range(2):
                        x_ = str_to_x(row[slx[i]])
                        projx_ = tuple([row[i]] + x_)
                        if projx_ not in projx[i]:
                            projx[i].append(projx_)
                            proj[i].append(row[i])
                            x[i].append(x_)
                        mapping_.append(projx[i].index(projx_))
                else:
                    for i in range(2):
                        x_ = str_to_x(row[slx[i]])
                        if x_ not in x[i]:
                            x[i].append(x_)
                        mapping_.append(x[i].index(x_))
                mapping.append(mapping_)
                cov.append(str_to_y(row[-1]))

        mapping = np.array(mapping).T
        mcov = np.full(mapping.max(axis=-1)+1,np.nan)
        mcov[tuple(mapping)] = cov

        x = tuple(np.squeeze(x_) for x_ in x)
        if col_proj:
            attrs['proj'] = tuple(np.array(p) for p in proj)

        attrs.setdefault('filename',filename)
        if data is not None:
            x = tuple(data[ix] for ix in x)

        return cls(mcov,x=x,**attrs)

    @savefile
    def save_txt(self, filename, comments='#', fmt='.18e'):
        with open(filename,'w') as file:
            for key,val in self.attrs.items():
                file.write('{}{} = {}\n'.format(comments,key,json.dumps(val)))
            if self._x[0].has_proj():
                file.write('{}projection = {}\n'.format(comments,json.dumps(True)))
            for ix1,x1 in enumerate(self._x[0]._x):
                for ix2,x2 in enumerate(self._x[1]._x):
                    if self._x[0].has_proj():
                        file.write('{} {} {:{fmt}} {:{fmt}} {:{fmt}}\n'.format(self._x[0]._proj[ix1],self._x[1]._proj[ix2],x1,x2,\
                                                                                self._covariance[ix1,ix2],fmt=fmt))
                    else:
                        file.write('{:{fmt}} {:{fmt}} {:{fmt}}\n'.format(x1,x2,self._cov[ix1,ix2],fmt=fmt))

    @saveplot(giveax=False)
    def plot(self, corr=True, style=None, norm=None, barlabel=None, wspace=0.18, hspace=0.18, figsize=None, ticksize=13, **kwargs_style):

        if not isinstance(style,tuple):
            style = (style,)*self.ndim
        styles = []
        for s,x in zip(style,self._x):
            if x.ndim > 1:
                raise NotImplementedError('No plot method defined for {:d}-dimensional data vector.'.format(x.ndim))
            s = PlottingStyle(s,**kwargs_style)
            if s.projs == [None]: s.set_sorted_projs(x.projs())
            styles.append(s)

        mat = self.corr() if corr else self.cov()
        if norm is None:
            norm = Normalize(vmin=mat.min(),vmax=mat.max())
        x = [[x.x(proj=proj) for proj in s.projs] for s in styles]
        mat = [[mat[np.ix_(*self.get_index(proj=(proj1,proj2)))] for proj1 in styles[0].projs] for proj2 in styles[1].projs]

        nrows = len(x[1])
        ncols = len(x[0])
        width_ratios = list(map(len,x[1]))
        height_ratios = list(map(len,x[0]))
        if figsize is None: figsize = np.clip(sum(width_ratios)/7,6,10)
        xextend = 0.8
        fig,lax = plt.subplots(nrows=nrows,ncols=ncols,sharex=False,sharey=False,
                                    figsize=(figsize/xextend,figsize),
                                    gridspec_kw={'width_ratios':width_ratios,'height_ratios':height_ratios},squeeze=False)
        fig.subplots_adjust(wspace=wspace,hspace=hspace)

        for i in range(ncols):
            for j in range(nrows):
                ax = lax[nrows-1-j][i]
                mesh = ax.pcolor(x[0][i],x[1][j],mat[i][j].T,norm=norm,cmap=plt.get_cmap('jet_r'))
                if i>0: ax.yaxis.set_visible(False)
                if j>0: ax.xaxis.set_visible(False)
                ax.tick_params(labelsize=ticksize)
                label1,label2 = styles[0].proj_to_label(styles[0].projs[i]),styles[1].proj_to_label(styles[1].projs[j])
                if label1 is not None or label2 is not None:
                    text = '{}\nx {}'.format(label1,label2)
                    ax.text(0.05,0.95,text,horizontalalignment='left',verticalalignment='top',\
                            transform=ax.transAxes,color='black',fontsize=styles[0].labelsize)

        suplabel('x',styles[0].xlabel,shift=0,labelpad=17,size=styles[0].labelsize)
        suplabel('y',styles[1].xlabel,shift=0,labelpad=17,size=styles[0].labelsize)
        fig.subplots_adjust(right=xextend)
        cbar_ax = fig.add_axes([xextend+0.05,0.15,0.03,0.7])
        cbar_ax.tick_params(labelsize=ticksize)
        cbar = fig.colorbar(mesh,cax=cbar_ax)
        cbar.set_label(barlabel,fontsize=styles[0].labelsize,rotation=90)


class MockCovarianceMatrix(CovarianceMatrix):

    logger = logging.getLogger('MockCovarianceMatrix')

    @classmethod
    def from_data(cls, list_data):
        list_x,list_y = [],[]
        for data in list_data:
            list_x.append(data.x())
            list_y.append(data.y())
        x = np.mean(list_x,axis=0)
        mean = np.mean(list_y,axis=0)
        covariance = np.cov(np.array(list_y).T,ddof=1)
        x = DataVector(x=x,y=mean,proj=data._proj)
        return cls(covariance=covariance,x=x,mean=mean,nobs=len(list_y))

    @classmethod
    def from_files(cls, reader, filenames, **kwargs):
        filenames = filenames or []
        list_data = (reader(filename, **kwargs) for filename in filenames)
        return cls.from_data(list_data)


### Pipeline stuff ###
from cosmopipe.pipeline import SectionBlock, section_names

def setup(name, config_block, data_block):
    options = SectionBlock(config_block,name)
    if options.get_string('format','txt') == 'txt':
        kwargs = {'xdim':options.get_int('xdim',None),'comments':options.get_string('comments','#'),'usecols':options.get_int_array_1d('usecols',None)}
        kwargs.update({'skip_rows':options.get_int('skip_rows',0),'max_rows':options.get_int('max_rows',None)})
        kwargs['mapping_header'] = options.get_json('mapping_header',None)
        kwargs['mapping_proj'] = options.get_json('mapping_proj',None,catch=lambda s: s.split())
        if options.has_value('data'):
            from .data_vector import get_data_from_options
            kwargs['data'] = get_data_from_options(SectionBlock(config_block,options.get_string('data')))
        cov = CovarianceMatrix.load_txt(options.get_string('covariance_file'),**kwargs)
    else:
        cov = CovarianceMatrix.load(options.get_string('covariance_file'))

    projs = data_block[section_names.data,'projs']
    xlims = data_block[section_names.data,'xlims']
    cov = cov.view(proj=projs,xlim=xlims)

    data_block[section_names.covariance,'cov'] = cov.cov()
    data_block[section_names.covariance,'invcov'] = cov.invcov()
    data_block[section_names.covariance,'nobs'] = cov.attrs.get('nobs',0)
    return 0

def execute(name, config_block, data_block):
    return 0

def cleanup(name, config_block, data_block):
    return 0
