import os

import numpy as np

from cosmopipe.data import DataVector,CovarianceMatrix,MockCovarianceMatrix
from cosmopipe import utils
from cosmopipe.utils import setup_logging


base_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(base_dir,'_data')
data_fn = os.path.join(data_dir,'_data_{:d}.txt')
covariance_fn = os.path.join(data_dir,'covariance.txt')

def make_data_covariance(data_fn=data_fn,covariance_fn=covariance_fn,mapping_proj=None,ndata=30,seed=42):
    utils.mkdir(os.path.dirname(data_fn))
    utils.mkdir(os.path.dirname(covariance_fn))
    x = np.linspace(0.,1.,4)
    rng = np.random.RandomState(seed=seed)
    list_data = []
    for i in range(ndata):
        y = [rng.uniform(-1.,1.,size=x.size) for i in range(len(mapping_proj))]
        data = DataVector(x=x,y=y,mapping_proj=mapping_proj)
        with open(data_fn.format(i),'w') as file:
            file.write('#Estimated shot noise: 3000.0\n')
            template = ' '.join(['{:.18e}']*(len(y)+1)) + '\n'
            y = np.array(y).T
            for ix,x_ in enumerate(x):
                file.write(template.format(x_,*y[ix]))
        list_data.append(data)
    cov = MockCovarianceMatrix.from_data(list_data)
    with open(covariance_fn,'w') as file:
        file.write('#Nobs: {:d}\n'.format(ndata))
        template = '{:d} {:d} {:.18e}\n'
        for i in range(cov.shape[0]):
            for j in range(cov.shape[1]):
                file.write(template.format(i,j,cov._covariance[i,j]))
    return list_data,cov


def test_data_vector():

    mapping_proj = ['ell_0','ell_2','ell_4']

    list_data = make_data_covariance(ndata=1,mapping_proj=mapping_proj)[0]
    mapping_header = {'shotnoise':'.*?Estimated shot noise: (.*)'}
    data = DataVector.load_txt(data_fn.format(0),mapping_header=mapping_header,mapping_proj=mapping_proj)
    assert np.allclose(data.x(),list_data[0].x())
    assert np.allclose(data.x(proj='ell_0'),list_data[0].x(proj='ell_0'))
    assert np.all(data.view(proj='ell_0').y() == data.y(proj='ell_0'))
    assert data.attrs['shotnoise'] == 3000.
    filename = os.path.join(data_dir,'data.npy')
    data.save(filename)
    data2 = DataVector.load(filename)
    assert np.all(data2.x(proj='ell_2') == data.x(proj='ell_2'))
    filename = os.path.join(data_dir,'data.txt')
    data.save_txt(filename)
    data2 = DataVector.load_txt(filename)
    assert np.all(data2.x(proj='ell_4') == data.x(proj='ell_4'))
    filename = os.path.join(data_dir,'plot_data.png')
    data2.plot(filename=filename,style='pk')

    mapping_proj = ['ell_0']

    list_data = make_data_covariance(ndata=1,mapping_proj=mapping_proj)[0]
    mapping_header = {'shotnoise':'.*?Estimated shot noise: (.*)'}
    data = DataVector.load_txt(data_fn.format(0),mapping_header=mapping_header)
    assert np.allclose(data.x(),list_data[0].x())
    assert data.attrs['shotnoise'] == 3000.
    filename = os.path.join(data_dir,'data.npy')
    data.save(filename)
    data2 = DataVector.load(filename)
    assert np.all(data2.x() == data.x())
    filename = os.path.join(data_dir,'data.txt')
    data.save_txt(filename)
    data2 = DataVector.load_txt(filename)
    assert np.all(data2.x() == data.x())
    filename = os.path.join(data_dir,'plot_data_0.png')
    data2.plot(filename=filename,style='pk')


def test_covariance():

    mapping_proj = ['ell_0','ell_2','ell_4']
    list_data,cov_ref = make_data_covariance(ndata=60,mapping_proj=mapping_proj)
    cov = CovarianceMatrix.load_txt(covariance_fn)
    assert np.allclose(cov.cov(),cov_ref.cov())
    cov2 = CovarianceMatrix.load_txt(covariance_fn,data=list_data[0])
    assert np.allclose(cov2.cov(),cov_ref.cov())
    assert np.allclose(cov2.x()[0],cov_ref.x()[0])
    filename = os.path.join(data_dir,'covariance.npy')
    cov2.save(filename)
    cov2 = CovarianceMatrix.load(filename)
    assert np.all(cov2.cov() == cov.cov())
    filename = os.path.join(data_dir,'covariance.txt')
    cov2.save_txt(filename)
    cov2 = CovarianceMatrix.load_txt(filename)
    assert np.allclose(cov2.cov(),cov.cov())
    for kwargs in [{'block':False},{'block':True},{'block':True,'proj':['ell_0','ell_2','ell_4']}]:
        assert np.allclose(cov2.cov().dot(cov2.invcov(**kwargs)),np.eye(*cov2.shape))
    filename = os.path.join(data_dir,'plot_covariance.png')
    cov2.plot(filename=filename,style='pk')

    mapping_proj = ['ell_0']
    list_data,cov_ref = make_data_covariance(ndata=60,mapping_proj=mapping_proj)
    data = DataVector.load_txt(data_fn.format(0))
    cov = CovarianceMatrix.load_txt(covariance_fn,data=data)
    assert np.allclose(cov.cov(),cov_ref.cov())
    filename = os.path.join(data_dir,'plot_covariance_0.png')
    cov.plot(filename=filename,style='pk')


if __name__ == '__main__':

    setup_logging()
    test_data_vector()
    test_covariance()
