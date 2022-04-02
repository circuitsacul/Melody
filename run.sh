#!/bin/bash

while true
do
    $1 -m poetry run python -m music

    echo "Hit CTRL+C to stop..."
    sleep 5
done