import os
import logging
import re
import functools

from matplotlib import pyplot as plt

from . import utils

logger = logging.getLogger('Plotting')

def saveplot(giveax=True):
    """
    Decorate plotting methods, to achieve the following behaviour for the decorated method:

    If ``ax`` is provided, add image to ``ax``.
    Else, if ``filename`` is provided, save image to ``filename``, with arguments ``kwargs_fig``.
    Else, show image.

    Parameters
    ----------
    giveax : bool, default=True
        If ``True``, provide ``ax`` to decorated method.
        Else, ``ax`` is not provided.
    """
    def decorator(func):

        @functools.wraps(func)
        def wrapper(self, ax=None, filename=None, kwargs_fig=None, **kwargs):
            isax = True
            if giveax:
                if ax is None:
                    isax = False
                    ax = plt.gca()
                func(self,ax,**kwargs)
            else:
                isax = False
                func(self,**kwargs)
                if ax is None:
                    ax = plt.gca()
            if filename is not None:
                kwargs_fig = kwargs_fig or {}
                savefig(filename,**kwargs_fig)
            elif not isax:
                plt.show()
            return ax
        return wrapper

    return decorator


def savefig(filename, bbox_inches='tight', pad_inches=0.1, dpi=200, **kwargs):
    """Save matplotlib figure to ``filename``."""
    utils.mkdir(os.path.dirname(filename))
    logger.info('Saving figure to {}.'.format(filename))
    plt.savefig(filename,bbox_inches=bbox_inches,pad_inches=pad_inches,dpi=dpi,**kwargs)
    plt.close(plt.gcf())


def suplabel(axis,label,shift=0,labelpad=5,ha='center',va='center',**kwargs):
    """
    Add super ylabel or xlabel to the figure. Similar to matplotlib.suptitle.
    Taken from https://stackoverflow.com/questions/6963035/pyplot-axes-labels-for-subplots.

    Parameters
    ----------
    axis : str
        'x' or 'y'.
    label : str
        label.
    shift : float, optional
        shift.
    labelpad : float, optional
        padding from the axis.
    ha : str, optional
        horizontal alignment.
    va : str, optional
        vertical alignment.
    kwargs : dict
        kwargs for :meth:`matplotlib.pyplot.text`

    """
    fig = plt.gcf()
    xmin = []
    ymin = []
    for ax in fig.axes:
        xmin.append(ax.get_position().xmin)
        ymin.append(ax.get_position().ymin)
    xmin,ymin = min(xmin),min(ymin)
    dpi = fig.dpi
    if axis.lower() == 'y':
        rotation = 90.
        x = xmin - float(labelpad)/dpi
        y = 0.5 + shift
    elif axis.lower() == 'x':
        rotation = 0.
        x = 0.5 + shift
        y = ymin - float(labelpad)/dpi
    else:
        raise Exception('Unexpected axis {}; chose between x and y'.format(axis))
    plt.text(x,y,label,rotation=rotation,transform=fig.transFigure,ha=ha,va=va,**kwargs)


class BasePlottingStyle(object):

    def __init__(self, style=None, **kwargs):

        if isinstance(style, self.__class__):
            self.__dict__.update(style.__dict__)
            self.update(**kwargs)
            return

        self.set_sorted_projs()
        self.xlabel = None
        self.ylabel = None
        self.color = None
        self.linestyle = '-'
        self.xscale = 'linear'
        self.yscale = 'linear'
        self.labelsize = 17
        self.ticksize = 15
        self.update(**kwargs)

    def set_ax(self, ax):
        ax.set_xlabel(self.xlabel,fontsize=self.labelsize)
        ax.set_ylabel(self.ylabel,fontsize=self.labelsize)
        ax.set_xscale(self.xscale)
        ax.set_yscale(self.yscale)
        ax.tick_params(labelsize=self.ticksize)

    def set_sorted_projs(self, projs=None):
        projs = projs or []
        self.projs = sorted(projs)
        if not self.projs: self.projs = [None]

    def y(self, x, y):
        return y

    def proj_to_label(self, proj):
        if not proj:
            return None
        match = re.match('ell_(.*)',proj)
        if match:
            return '$\\ell = {}$'.format(match.group(1))
        return '${}$'.format(utils.txt_to_latex(proj))

    def proj_to_kwplt(self, proj):

        if self.color is None:
            color = 'C{:d}'.format(self.projs.index(proj))
        elif isinstance(self.color,str):
            color = self.color
        elif isinstance(self.color,dict):
            color = self.color[proj]
        else:
            color = self.color[self.projs.index(proj)]
        if isinstance(self.linestyle,str):
            linestyle = self.linestyle
        elif isinstance(self.linestyle,dict):
            linestyle = self.linestyle[proj]
        else:
            linestyle = self.linestyle[self.projs.index(proj)]
        return {'color':color,'linestyle':linestyle}

    def update(self, **kwargs):
        for key,val in kwargs.items():
            if val is not None:
                setattr(self,key,val)


class PowerSpectrumPlottingStyle(BasePlottingStyle):

    def __init__(self, style=None, **kwargs):

        BasePlottingStyle.__init__(self,style=style)
        self.xlabel = '$k$ [$h \ \\mathrm{Mpc}^{-1}$]'
        self.ylabel = '$k P(k)$ [$(\\mathrm{Mpc} \ h)^{-1})^{2}$]'
        self.update(**kwargs)

    def y(self, x, y):
        return x*y


class CorrelationFunctionPlottingStyle(BasePlottingStyle):

    def __init__(self, style=None, **kwargs):

        BasePlottingStyle.__init__(self,style=style)
        self.xlabel = '$s$ [$\\mathrm{Mpc} \ h$]'
        self.ylabel = '$s^{2} \\xi(s)$ [$(\\mathrm{Mpc} \ h)^{-1})^{2}$]'
        self.update(**kwargs)

    def y(self, x, y):
        return x**2*y


def PlottingStyle(style, **kwargs):

    if isinstance(style, BasePlottingStyle):
        style.update(**kwargs)
        return style

    styles = {'pk':PowerSpectrumPlottingStyle,'xi':CorrelationFunctionPlottingStyle}
    return styles[style](**kwargs)
