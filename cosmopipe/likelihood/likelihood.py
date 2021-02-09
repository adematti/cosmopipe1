import os
import logging

import numpy as np

from cosmopipe.pipeline import BaseModule, BasePipeline, section_names
from cosmopipe.data import DataVector, CovarianceMatrix


class BaseLikelihood(BasePipeline):

    logger = logging.getLogger('BaseLikelihood')

    def setup(self):
        super(BaseLikelihood,self).setup()
        self.set_data()

    def set_data(self):
        self.data = self.pipe_block[section_names.data,'y']
        for key in self.pipe_block.keys(section=section_names.data):
            self.data_block[key] = self.pipe_block[key]

    def set_model(self):
        self.model = self.data_block[section_names.model,'y'] = self.pipe_block[section_names.model,'y']

    def loglkl(self):
        return 0

    def execute(self):
        super(BaseLikelihood,self).execute()
        self.set_model()
        self.data_block[section_names.likelihood,'loglkl'] = self.loglkl()


class GaussianLikelihood(BaseLikelihood):

    logger = logging.getLogger('GaussianLikelihood')

    def setup(self):
        super(GaussianLikelihood,self).setup()
        self.set_covariance()

    def set_covariance(self):
        self.invcovariance = self.pipe_block[section_names.covariance,'invcov']
        self.nobs = self.pipe_block.get(section_names.covariance,'nobs',None)
        if self.nobs is None:
            self.logger.info('The number of observations used to estimate the covariance matrix is not provided,\
                            hence no Hartlap factor is applied to inverse covariance.')
            self.precision = self.invcovariance
        else:
            self.hartlap = (self.nobs - self.data.size - 2.)/(self.nobs - 1.)
            self.logger.info('Covariance matrix with {:d} points built from {:d} observations.'.format(self.data.size,self.nobs))
            self.logger.info('...resulting in Hartlap factor of {:.4f}.'.format(self.hartlap))
            self.precision = self.invcovariance * self.hartlap

    def loglkl(self):
        diff = self.model - self.data
        return -0.5*diff.T.dot(self.precision).dot(diff)


class SumLikelihood(BaseLikelihood):

    logger = logging.getLogger('SumLikelihood')

    def setup(self):
        BasePipeline.setup(self)

    def execute(self):
        for key in self.data_block.keys(section=section_names.parameters):
            self.pipe_block[key] = self.data_block[key]
        loglkl = 0
        for module in self:
            module.execute()
            loglkl += self.pipe_block[section_names.likelihood,'loglkl']
        self.data_block[section_names.likelihood,'loglkl'] = loglkl


class JointGaussianLikelihood(GaussianLikelihood):

    logger = logging.getLogger('JointGaussianLikelihood')

    def __init__(self, *args, join=[], modules=[], **kwargs):
        super(JointGaussianLikelihood,self).__init__(*args,modules=join + modules,**kwargs)
        self.join = join + self._get_modules_from_library(self.options.get_string('join',default='').split())
        self.after = [module for module in self.modules if module not in self.join]
        self.modules = self.join + self.after

    def setup(self):
        join = {}
        for module in self.join:
            module.setup()
            for key in self.pipe_block.keys(section=section_names.data):
                if key not in join: join[key] = []
                join[key].append(self.pipe_block[key])
        for key in join:
            self.data_block[key] = self.pipe_block[key] = np.concatenate(join[key])
        for module in self.after:
            module.setup()
        self.set_data()
        self.set_covariance()

    def execute(self):
        for key in self.data_block.keys(section=section_names.parameters):
            self.pipe_block[key] = self.data_block[key]
        join = {}
        for module in self.join:
            module.execute()
            for key in self.pipe_block.keys(section=section_names.model):
                if key not in join: join[key] = []
                join[key].append(self.pipe_block[key])
        for key in join:
            self.data_block[key] = self.pipe_block[key] = np.concatenate(join[key])
        for module in self.after:
            module.execute()
        self.set_model()
        self.data_block[section_names.likelihood,'loglkl'] = self.loglkl()
