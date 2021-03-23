#!/bin/sh
mypy forum --strict --allow-untyped-decorators
pylint forum
