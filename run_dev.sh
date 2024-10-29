#!/bin/bash

cd "$(dirname "$0")"

make -C src/advice_bot/proto/ || exit

uv run src/main.py --alsologtostderr $@
