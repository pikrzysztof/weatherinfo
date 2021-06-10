.PHONY: all build lint lint-dockerfile lint-python test

all: lint build test

build: apikey Dockerfile weather.py requirements.txt
	docker build . -t weather:latest

lint: lint-dockerfile lint-python

lint-dockerfile:
	hadolint Dockerfile

lint-python:
	mypy weather.py
	pylint weather.py

test: build
	docker run --env-file apikey --rm -t weather:latest
