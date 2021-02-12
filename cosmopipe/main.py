from .pipeline import BasePipeline

def main(config=None,pipe_graph_fn=None):
    pipeline = BasePipeline(config_block=config)
    if pipe_graph_fn is not None:
        pipeline.plot_pipeline_graph(graph_fn)
    pipeline.setup()
    pipeline.execute()
    pipeline.cleanup()
