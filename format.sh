#!/bin/bash

cd "$(dirname "$0")"

uv run yapf -r -i .
