#!/bin/bash

cat run_args.txt | xargs -I CMD --max-procs=6 bash -c CMD
