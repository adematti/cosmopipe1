import argparse

from .utils import setup_logging
from .main import main as cosmopipe_main

def main(args=None):
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config-fn', type=str, required=True,
                        help='Name of configuration file')
    parser.add_argument('--pipe-graph-fn', type=str, default=None,
                        help='If provided, save graph of the pipeline to this file name')
    opt = parser.parse_args(args=args)
    return cosmopipe_main(config=opt.config_fn,pipe_graph_fn=opt.pipe_graph_fn)


if __name__ == '__main__':

    setup_logging()
    main()
