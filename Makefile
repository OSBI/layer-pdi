#!/usr/bin/make
PYTHON := /usr/bin/env python

all: lint build

lint:
	@flake8 reactive tests

build:
	@charm build --force