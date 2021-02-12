import logging

from cosmopipe.pipeline import BasePipeline, section_names


class CosmosisSampler(BasePipeline):

    logger = logging.getLogger('CosmosisSampler')

    def setup(self):

        super(CosmosisSampler,self).setup()
        self.sampler_name = self.options['sampler']

        from cosmosis.runtime.config import Inifile
        from cosmosis.runtime.pipeline import LikelihoodPipeline
        from cosmosis.samplers.sampler import Sampler

        self.sampler_class = Sampler.registry[self.sampler_name]
        override = {}
        override['pipeline','modules'] = ''
        self.ini = Inifile(filename=None,override=override)
        self.pipeline = LikelihoodPipeline(self.ini)

    def execute(self):
        from cosmosis.output.in_memory_output import InMemoryOutput
        output = InMemoryOutput()
        sampler = self.sampler_class(self.ini, self.pipeline, output)
        sampler.config()

        while not sampler.is_converged():
            sampler.execute()

        self.data_block[section_names.likelihoods,'samples'] = output

    def cleanup(self):
        return 0
