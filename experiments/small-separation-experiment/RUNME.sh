#!/bin/bash
set -e

ROOT_DIR=../../
GRAPH_DIR=./graphs/
LOG_DIR=./logs/
ANALYSIS_DIR=./analysis/
FIG_DIR=./figs/

rm -rf $GRAPH_DIR
rm -rf $ANALYSIS_DIR
rm -rf $FIG_DIR
mkdir empty_dir
rsync -a --delete empty_dir/ $LOG_DIR
rm -rf $LOG_DIR
rmdir empty_dir

mkdir $GRAPH_DIR
mkdir $LOG_DIR
mkdir $ANALYSIS_DIR
mkdir $FIG_DIR

SEED_FILE=./seeds.txt

python $ROOT_DIR/graph-generate/main.py --small --max 6 --outdir $GRAPH_DIR
echo "Generated small graphs."

seq 0 999 > $SEED_FILE
echo "Generated seed file."

for ALGO in sleepwell desync solo2 ;
do
    ALGO_DIR=./logs/$ALGO
    mkdir -p $ALGO_DIR
    python $ROOT_DIR/graph-simulate/main.py --graph-dir $GRAPH_DIR \
        --outdir $ALGO_DIR --seed-list $SEED_FILE --algo $ALGO --alpha 50

    CONVERGENCE_FILE=$ANALYSIS_DIR/$ALGO-convergence
    python $ROOT_DIR/graph-simulate/analyze.py --logdir $ALGO_DIR \
        --converge-time --outfile $CONVERGENCE_FILE

    DEFICIT_FILE=$ANALYSIS_DIR/$ALGO-deficit
    python $ROOT_DIR/graph-simulate/analyze.py --logdir $ALGO_DIR \
        --deficit --last --outfile $DEFICIT_FILE
    
    echo "Analyzed ALGO=$ALGO"
done

python plot.py
