#!/bin/bash

docker-compose -f ../local.yml run --rm django sphinx-apidoc -f -o ./docs/modules ./pomodorr/ */migrations/* */tests/*
