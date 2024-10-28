#!/bin/bash

cd "$(dirname "$0")"

make -C src/advice_bot/proto/

uv run src/main.py $@
