import os

from cosmopipe.pipeline import BaseModule, BasePipeline, ConfigBlock, SectionBlock, section_names
from cosmopipe.theory import FlatModel
from cosmopipe.likelihood import BaseLikelihood, JointGaussianLikelihood
from cosmopipe.utils import setup_logging

from cosmopipe.data.tests.test_data import make_data_covariance


setup_logging()
base_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(base_dir,'_data')
demo_dir = os.path.join(base_dir,'demos')
data_fn = os.path.join(data_dir,'data_{:d}.txt')
covariance_fn = os.path.join(data_dir,'covariance.txt')
os.chdir(base_dir)


def test_demo1():

    config_fn = os.path.join(demo_dir,'demo1.ini')
    graph_fn = os.path.join(demo_dir,'pipe1.ps')

    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)

    pipeline = BasePipeline(config_block=config_fn)
    pipeline.plot_pipeline_graph(graph_fn)
    pipeline.setup()
    pipeline.execute()
    loglkl = pipeline.pipe_block[section_names.likelihood,'loglkl']
    pipeline.pipe_block[section_names.parameters,'a'] = 4.
    pipeline.execute()
    assert pipeline.pipe_block[section_names.likelihood,'loglkl'] != loglkl
    pipeline.cleanup()

    graph_fn = os.path.join(demo_dir,'inheritance.ps')
    BaseModule.plot_inheritance_graph(graph_fn,exclude=['AffineModel'])


def test_demo2():

    config_fn = os.path.join(demo_dir,'demo2.ini')
    graph_fn = os.path.join(demo_dir,'pipe2.ps')

    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)

    pipeline = BasePipeline(config_block=config_fn)
    pipeline.plot_pipeline_graph(graph_fn)
    pipeline.setup()
    pipeline.execute()
    loglkl = pipeline.pipe_block[section_names.likelihood,'loglkl']
    pipeline.pipe_block[section_names.parameters,'a'] = 4.
    pipeline.execute()
    assert pipeline.pipe_block[section_names.likelihood,'loglkl'] != loglkl
    pipeline.cleanup()


def test_demo3():

    for config_fn in [os.path.join(demo_dir,'demo3.ini'),os.path.join(demo_dir,'demo3.yaml')]:

        graph_fn = os.path.join(demo_dir,'pipe3.ps')

        mapping_proj = ['ell_0','ell_2','ell_4']
        make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
        pipeline = BasePipeline(config_block=config_fn)
        pipeline.plot_pipeline_graph(graph_fn)
        pipeline.setup()
        pipeline.execute()
        loglkl = pipeline.pipe_block[section_names.likelihood,'loglkl']
        pipeline.pipe_block[section_names.parameters,'a'] = 4.
        pipeline.execute()
        assert pipeline.pipe_block[section_names.likelihood,'loglkl'] != loglkl
        pipeline.cleanup()


def test_demo3b():

    config_fn = os.path.join(demo_dir,'demo3.ini')
    graph_fn = os.path.join(demo_dir,'pipe3b.ps')

    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
    config_block = ConfigBlock(config_fn)
    data1 = BaseModule.from_library(name='data1',options=SectionBlock(config_block,'data1'))
    model1 = FlatModel(name='model1')
    data2 = BaseModule.from_library(name='data2',options=SectionBlock(config_block,'data2'))
    model2 = BaseModule.from_library(name='model2',options=SectionBlock(config_block,'model2'))
    cov = BaseModule.from_library(name='cov',options=SectionBlock(config_block,'cov'))
    like1 = BaseLikelihood(name='like1',modules=[data1,model1])
    like2 = BaseLikelihood(name='like2',modules=[data2,model2])
    like = JointGaussianLikelihood(name='like',join=[like1,like2],modules=[cov])
    pipeline = BasePipeline(modules=[like])
    pipeline.plot_pipeline_graph(graph_fn)
    pipeline.setup()
    pipeline.execute()
    loglkl = pipeline.pipe_block[section_names.likelihood,'loglkl']
    pipeline.pipe_block[section_names.parameters,'a'] = 4.
    pipeline.execute()
    assert pipeline.pipe_block[section_names.likelihood,'loglkl'] != loglkl
    pipeline.cleanup()


def test_demo4():

    config_fn = os.path.join(demo_dir,'demo4.ini')
    graph_fn = os.path.join(demo_dir,'pipe4.ps')

    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
    pipeline = BasePipeline(config_block=config_fn)
    pipeline.plot_pipeline_graph(graph_fn)
    pipeline.setup()
    pipeline.execute()
    pipeline.cleanup()


if __name__ == '__main__':

    test_demo1()
    test_demo2()
    test_demo3()
    test_demo3b()
    #test_demo4()
