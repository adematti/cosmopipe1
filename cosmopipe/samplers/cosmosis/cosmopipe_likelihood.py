from cosmosis.datablock import names as cosmosis_names
from cosmosis.datablock import SectionOptions

from cosmopipe.pipeline import BasePipeline, section_names


class CosmoPipeLikelihood(object):

    def __init__(self, options):
        self.pipeline = BasePipeline(config_block=options.get_string('config_file'))

    def setup(self):
        self.pipeline.setup()

    def execute(self, block):
        self.pipeline.execute()
        block[cosmosis_names.likelihoods,'cosmopipe_like'] = self.pipeline.pipe_block[section_names.likelihood,'loglkl']

    def cleanup(self):
        self.pipeline.cleanup()


def setup(options):
    options = SectionOptions(options)
    like = CosmoPipeLikelihood(options)
    like.setup()
    return like

def execute(block,config):
    like = config
    like.execute(block)
    return 0

def cleanup(config):
    like = config
    like.cleanup()
