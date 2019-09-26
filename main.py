import sys, argparse
import os
import numpy as np
import networkx as nx

"""
Usage:
    python3 ./main.py --complete --max 6 --outdir DIR
    python3 ./main.py --small --max 6 --outdir DIR
    python3 ./main.py --udg --dim 100 --num 200 --max-seed 10 --outdir DIR
    python3 ./main.py --binomial --prob 0.5 --num 200 --max-seed 10 --outdir DIR
"""

def generate_complete_graphs(max_size):
    return [nx.complete_graph(n) for n in range(2, max_size + 1)] 


def generate_small_graphs(max_size):
    return [g for g in nx.graph_atlas_g()[1:]
                if len(g) <= max_size and nx.is_connected(g)]


def generate_udg_graphs(dim, num, max_seed):
    graph_list = [None for _ in range(max_seed + 1)]
    for seed in range(max_seed + 1):
        graph = nx.random_geometric_graph(num, 1, dim=dim, seed=seed)
        graph_list[seed] = graph
    return graph_list
        
        
def generate_binomial_graphs(prob, num, max_seed):
    graph_list = [None for _ in range(max_seed + 1)]
    for seed in range(max_seed + 1):
        graph = nx.gnp_random_graph(num, prob, seed=seed)
        graph_list[seed] = graph
    return graph_list


def save_graph_list(graph_list, parameters, outdir):
    for i, g in enumerate(graph_list):
        graph_file = os.path.join(outdir, "%d.txt" % i)
        nx.write_adjlist(g, graph_file)
    
    index_file = os.path.join(outdir, "index.txt")
    index_list = [str(i) for i in range(len(graph_list))]
    with open(index_file, "w") as fo:
        fo.write("\n".join(index_list))

    params_file = os.path.join(outdir, "parameters.txt")
    with open(params_file, "w") as fo:
        fo.write(parameters)

    print("%d graphs saved in ./%s" % (len(graph_list), outdir))
     

if __name__=="__main__":
    parser = argparse.ArgumentParser(
                description="Simulate desynchronization algorithms.")
    
    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument("--complete", action="store_true",
                            help="Flag to generate complete graphs")
    type_group.add_argument("--small", action="store_true",
                            help="Flag to generate small connected graphs")
    type_group.add_argument("--udg", action="store_true",
                            help="Flag to generate geomteric graphs")
    type_group.add_argument("--binomial", action="store_true",
                            help="Flag to generate Erdos-Renyi graph")

    parser.add_argument("--outdir", required=True,
                       help="Output directory")
    # geometric graph attributes
    parser.add_argument("--dim", type=int,
                       help="Size of the grid for UDG placement")
    # random graph attributes
    parser.add_argument("--prob", type=float,
                       help="Link probability for Erdos-Renyi graphs") 
    # deterministically generated graphs
    parser.add_argument("--max", type=int,
                       help="Maximum number of nodes for complete/small")
    # randomly generated graphs
    parser.add_argument("--num", type=int,
                       help="Number of nodes for randomly generated graphs")
    parser.add_argument("--max-seed", type=int,
                       help="Max seed value for randomly generated graphs")

    args = parser.parse_args()
    if not os.path.isdir(args.outdir):
        parser.error("./%s does not exist." % args.outdir)
    if os.listdir(args.outdir):
        parser.error("./%s is not empty." % args.outdir)
    
    if args.small and (args.max is None):
        parser.error("--small requires --max.") 
    if args.udg and (None in [args.dim, args.num, args.max_seed]):
        parser.error("--udg requires --dim, --num, and --max-seed.")
    if args.binomial and (None in [args.prob, args.num, args.max_seed]):
        parser.error("--random requires --prob, --num, --max-seed.")

    if args.complete:
        graph_list = generate_complete_graphs(args.max)
    elif args.small:
        graph_list = generate_small_graphs(args.max)
    elif args.udg: 
        graph_list = generate_udg_graphs(args.dim, args.num, args.max_seed)
    elif args.binomial:
        graph_list = generate_binomial_graphs(args.prob, args.num, 
                                              args.max_seed)
    
    parameters = " ".join(sys.argv[1:])
    save_graph_list(graph_list, parameters, args.outdir)
