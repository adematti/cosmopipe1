import os
import sys
import logging

from .. import utils
from ..utils import BaseClass
from .block import DataBlock, SectionBlock
from . import section_names
from .config import ConfigBlock


class ModuleError(Exception):
    pass


def _import_pygraphviz():
    try:
        import pygraphviz as pgv
    except ImportError:
        raise ImportError('Please install pygraphviz: see https://github.com/pygraphviz/pygraphviz/blob/master/INSTALL.txt')
    return pgv


class BaseModule(BaseClass):

    logger = logging.getLogger('BaseModule')

    def __init__(self, name, options=None, config_block=None, data_block=None):
        self.name = name
        self.logger.info('Init module {}.'.format(self))
        self.set_config_block(options=options,config_block=config_block)
        self.set_data_block(data_block=data_block)

    def set_config_block(self, options=None, config_block=None):
        self.config_block = ConfigBlock(config_block)
        if options is not None:
            for name,value in options.items():
                self.config_block[self.name,name] = value
        self.options = SectionBlock(self.config_block,self.name)

    def set_data_block(self, data_block=None):
        self.data_block = data_block if data_block is not None else DataBlock()

    def setup(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def __str__(self):
        return '{} [{}]'.format(self.__class__.__name__,self.name)

    @classmethod
    def from_library(cls, name, options=None, config_block=None, data_block=None):

        options = options or {}
        base_dir = options.get('base_dir',utils.get_base_dir())
        try:
            module_file = options.get('module_file')
        except KeyError:
            raise ModuleError('Failed importing module [{}]. You must provide a module file!'.format(name))
        filename = os.path.join(base_dir,module_file)
        cls.logger.info('Importing library {} for module [{}].'.format(filename,name))
        dirname,filename = os.path.split(filename)
        impname = os.path.splitext(filename)[0]
        if os.path.isfile(os.path.join(dirname,'__init__.py')):
            sys.path.insert(0,os.path.dirname(dirname))
            mname = '.'.join([os.path.basename(dirname),impname])
            library = __import__(mname,fromlist=[impname])
        else:
            sys.path.insert(0,dirname)
            library = __import__(impname)
        sys.path.pop(0)

        module_class = options.get('module_class','Module')
        if hasattr(library,module_class):
            lib_cls = getattr(library,module_class)
            if issubclass(lib_cls,BaseModule):
                return lib_cls(name,options=options,config_block=config_block,data_block=data_block)

        clsname = utils.snake_to_pascal_case(impname)
        lib_cls = type(clsname,(BaseModule,),{'__init__':BaseModule.__init__, '__doc__':BaseModule.__doc__})

        steps = ['setup','execute','cleanup']

        def _make_func(library,step):
            f = getattr(library,options.get('{}_function'.format(step),step))

            def func(self):
                return f(name=self.name,config_block=self.config_block,data_block=self.data_block)

            return func

        for step in steps:
            setattr(lib_cls,step,_make_func(library,step))

        return lib_cls(name,options=options,config_block=config_block,data_block=data_block)

    @classmethod
    def plot_inheritance_graph(cls, filename, exclude=None):
        exclude = exclude or []
        pgv = _import_pygraphviz()
        graph = pgv.AGraph(strict=True,directed=True)

        def norm_name(cls):
            return cls.__name__

        def callback(curcls,prevcls):
            if norm_name(curcls) in exclude:
                return
            graph.add_node(norm_name(curcls),color='lightskyblue',style='filled',group='inheritance',shape='box')
            graph.add_edge(norm_name(curcls),norm_name(prevcls),color='lightskyblue',style='bold',arrowhead='none')
            for newcls in curcls.__subclasses__():
                callback(newcls,curcls)

        for newcls in cls.__subclasses__():
            callback(newcls,cls)

        graph.layout('dot')
        cls.logger.info('Saving graph to {}.'.format(filename))
        utils.mkdir(os.path.dirname(filename))
        graph.draw(filename)


class BasePipeline(BaseModule):

    logger = logging.getLogger('BasePipeline')

    def __init__(self, name='main', options=None, config_block=None, data_block=None, modules=None):
        self.modules = modules or []
        super(BasePipeline,self).__init__(name,options=options,config_block=config_block,data_block=data_block)
        self.modules += self._get_modules_from_library(self.options.get_string('modules',default='').split())

    def set_config_block(self, options=None, config_block=None):
        super(BasePipeline,self).set_config_block(options=options,config_block=config_block)
        for module in self:
            self.config_block.update(module.config_block)
        for module in self:
            module.set_config_block(config_block=self.config_block)
        self.options = SectionBlock(self.config_block,self.name)

    def set_data_block(self, data_block=None):
        super(BasePipeline,self).set_data_block(data_block=data_block)
        self.pipe_block = self.data_block.copy() # shallow copy
        for module in self:
            module.set_data_block(self.pipe_block)

    def _get_modules_from_library(self, names):
        modules = []
        for name in names:
            module = BaseModule.from_library(name=name,options=SectionBlock(self.config_block,name),config_block=self.config_block,data_block=self.pipe_block)
            modules.append(module)
        return modules

    def __iter__(self):
        yield from self.modules

    def setup(self):
        for module in self:
            module.setup()

    def execute(self):
        for key in self.data_block.keys(section=section_names.parameters):
            self.pipe_block[key] = self.data_block[key]
        for module in self:
            module.execute()

    def cleanup(self):
        for module in self:
            module.cleanup()
        del self.pipe_block

    def plot_pipeline_graph(self, filename):
        pgv = _import_pygraphviz()
        graph = pgv.AGraph(strict=True,directed=True)

        def norm_name(module):
            return '{}\\n[{}]'.format(module.__class__.__name__,module.name)

        def callback(module,prevmodule):
            graph.add_node(norm_name(module),color='lightskyblue',style='filled',group='pipeline',shape='box')
            graph.add_edge(norm_name(module),norm_name(prevmodule),color='lightskyblue',style='bold',arrowhead='none')
            if isinstance(module,BasePipeline):
                for newmodule in module.modules:
                    callback(newmodule,module)

        for module in self.modules:
            callback(module,self)

        graph.layout('dot')
        self.logger.info('Saving graph to {}.'.format(filename))
        utils.mkdir(os.path.dirname(filename))
        graph.draw(filename)
