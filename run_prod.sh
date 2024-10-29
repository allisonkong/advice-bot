#!/bin/bash

cd "$(dirname "$0")"

uv run src/main.py --alsologtostderr --env=prod $@
