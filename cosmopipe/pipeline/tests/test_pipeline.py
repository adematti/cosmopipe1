import os
import yaml

from cosmopipe.pipeline import BaseModule, BasePipeline, ConfigBlock, SectionBlock, BlockError, section_names
from cosmopipe.theory import FlatModel
from cosmopipe.likelihood import BaseLikelihood, JointGaussianLikelihood
from cosmopipe.utils import setup_logging

from cosmopipe.data.tests.test_data import make_data_covariance


base_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(base_dir,'_data')
demo_dir = os.path.join(base_dir,'demos')
data_fn = os.path.join(data_dir,'data_{:d}.txt')
covariance_fn = os.path.join(data_dir,'covariance.txt')


def test_demo1():

    os.chdir(base_dir)
    config_fn = os.path.join(demo_dir,'demo1.ini')
    graph_fn = os.path.join(demo_dir,'pipe1.ps')

    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)

    pipeline = BasePipeline(config_block=config_fn)
    pipeline.plot_pipeline_graph(graph_fn)
    pipeline.setup()
    pipeline.data_block[section_names.parameters,'a'] = 0.
    pipeline.execute()
    loglkl = pipeline.data_block[section_names.likelihood,'loglkl']
    pipeline.data_block[section_names.parameters,'a'] = 4.
    pipeline.execute()
    assert pipeline.data_block[section_names.likelihood,'loglkl'] != loglkl
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
    pipeline.data_block[section_names.parameters,'a'] = 0.
    pipeline.execute()
    loglkl = pipeline.data_block[section_names.likelihood,'loglkl']
    pipeline.data_block[section_names.parameters,'a'] = 4.
    pipeline.execute()
    assert pipeline.data_block[section_names.likelihood,'loglkl'] != loglkl
    pipeline.cleanup()


def test_demo3():

    config_fn_ini = os.path.join(demo_dir,'demo3.ini')
    config_fn_yaml = os.path.join(demo_dir,'demo3.yaml')
    config = ConfigBlock(config_fn_ini)
    with open(config_fn_yaml,'w') as file:
        yaml.dump(config.data, file)

    for config_fn in [config_fn_ini,config_fn_yaml]:

        graph_fn = os.path.join(demo_dir,'pipe3.ps')

        mapping_proj = ['ell_0','ell_2','ell_4']
        make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
        pipeline = BasePipeline(config_block=config_fn)
        pipeline.plot_pipeline_graph(graph_fn)
        pipeline.setup()
        pipeline.execute_parameter_values(a=0.)
        loglkl = pipeline.data_block[section_names.likelihood,'loglkl']
        pipeline.execute_parameter_values(a=4.)
        assert pipeline.data_block[section_names.likelihood,'loglkl'] != loglkl
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
    pipeline.data_block[section_names.parameters,'a'] = 0.
    pipeline.execute()
    loglkl = pipeline.data_block[section_names.likelihood,'loglkl']
    pipeline.data_block[section_names.parameters,'a'] = 4.
    pipeline.execute()
    assert pipeline.data_block[section_names.likelihood,'loglkl'] != loglkl
    pipeline.cleanup()


def test_demo4():

    config_fn = os.path.join(demo_dir,'demo4.ini')
    graph_fn = os.path.join(demo_dir,'pipe4.ps')

    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
    pipeline = BasePipeline(config_block=config_fn)
    pipeline.plot_pipeline_graph(graph_fn)
    pipeline.setup()
    pipeline.data_block[section_names.parameters,'a'] = 0.
    del pipeline.data_block[section_names.parameters,'a_model1']
    del pipeline.data_block[section_names.parameters,'b_model1']

    def test_error():
        ok = False
        try:
            pipeline.execute()
        except BlockError:
            ok = True
        assert ok

    test_error()
    pipeline.data_block[section_names.parameters,'a_model1'] = 0.
    test_error()
    pipeline.data_block[section_names.parameters,'b_model1'] = 0.
    assert (section_names.common,'y_data1') in pipeline.data_block
    assert (section_names.common,'y_data2') not in pipeline.data_block
    pipeline.cleanup()


if __name__ == '__main__':

    setup_logging()
    test_demo1()
    test_demo2()
    test_demo3()
    test_demo3b()
    test_demo4()
