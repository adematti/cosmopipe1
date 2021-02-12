from cobaya.likelihood import Likelihood

from cosmopipe.pipeline import BasePipeline, section_names


class CosmoPipeLikelihood(Likelihood):

    def initialize(self):
        self.pipeline = BasePipeline(config_block=self.config_file)
        self.pipeline.setup()

    def get_requirements(self):
        return {}

    def logp(self, **kwargs):
        for key,val in kwargs.items():
            self.pipeline.data_block[section_names.parameters,key] = val
        self.pipeline.execute()
        return self.pipeline.data_block[section_names.likelihood,'loglkl']

    def clean(self):
        pass
