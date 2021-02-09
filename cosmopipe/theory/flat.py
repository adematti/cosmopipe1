import os
import logging

import numpy as np

from cosmopipe.pipeline import BaseModule, section_names


class FlatModel(BaseModule):

    logger = logging.getLogger('FlatModel')

    def setup(self):
        self.size = self.data_block[section_names.data,'y'].size

    def execute(self):
        a = self.data_block.get_float(section_names.parameters,'a',0.)
        self.data_block[section_names.model,'y'] = np.full(self.size,a,dtype='f8')

    def cleanup(self):
        return 0


class AffineModel(BaseModule):

    logger = logging.getLogger('AffineModel')

    def setup(self):
        self.size = self.data_block[section_names.data,'y'].size

    def execute(self):
        a = self.data_block.get_float(section_names.parameters,'a',0.)
        b = self.data_block.get_float(section_names.parameters,'b',0.)
        self.data_block[section_names.model,'y'] = a + b*self.data_block[section_names.data,'x']

    def cleanup(self):
        return 0
