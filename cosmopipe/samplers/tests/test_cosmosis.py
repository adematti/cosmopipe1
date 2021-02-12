import os

from cosmopipe.utils import setup_logging
from cosmopipe.data.tests.test_data import make_data_covariance
from cosmopipe.main import main

from cosmosis.runtime.config import CosmosisConfigurationError
from cosmosis.runtime.config import Inifile
from cosmosis.runtime.pipeline import LikelihoodPipeline


base_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(base_dir,'_data')
demo_dir = os.path.join(base_dir,'demos')
data_fn = os.path.join(data_dir,'data_{:d}.txt')
covariance_fn = os.path.join(data_dir,'covariance.txt')


def test_internal():
    os.chdir(base_dir)
    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
    import cosmosis
    try: # not finished
        main(config='demo3.ini')
    except CosmosisConfigurationError:
        pass

def test_external():

    os.chdir(base_dir)
    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
    ini = Inifile('test_cosmosis.ini')
    pipeline = LikelihoodPipeline(ini)
    data = pipeline.run_parameters([0.2])
    assert data['likelihoods','cosmopipe_like'] != 0.

    from cosmosis.samplers.emcee.emcee_sampler import EmceeSampler
    from cosmosis.output.in_memory_output import InMemoryOutput
    output = InMemoryOutput()
    sampler = EmceeSampler(ini, pipeline, output)
    sampler.config()

    while not sampler.is_converged():
        sampler.execute()


if __name__ == '__main__':

    setup_logging()
    test_internal()
    test_external()
