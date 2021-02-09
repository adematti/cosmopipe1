import os

from cosmopipe.utils import setup_logging
from cosmopipe.data.tests.test_data import make_data_covariance

from cobaya.yaml import yaml_load_file
from cobaya.run import run

setup_logging()
base_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(base_dir,'_data')
demo_dir = os.path.join(base_dir,'demos')
data_fn = os.path.join(data_dir,'data_{:d}.txt')
covariance_fn = os.path.join(data_dir,'covariance.txt')
os.chdir(base_dir)


def test_cobaya():

    mapping_proj = ['ell_0','ell_2','ell_4']
    make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=mapping_proj)
    info = yaml_load_file('./test_cobaya.yaml')
    updated_info, sampler = run(info)
    assert 'sample' in sampler.products()


if __name__ == '__main__':

    test_cobaya()
