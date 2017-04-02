#!/usr/bin/env bash
# run_scraper.sh

### bash script for running the pub_scraper
### Useful for setting up an entry in your crontab

# ./run_scraper.sh script.py search_file.txt

# Ben Ober-Reynolds

script=$1
search_file=$2

source ~/venvs/py3k/bin/activate

python $script -sf $search_file

deactivate
