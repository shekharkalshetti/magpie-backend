#!/bin/sh -e
# Lint and format script using ruff
set -x

ruff check --fix src
ruff format src
