#!/usr/bin/env bash

if [ -d "/mnt/s3" ]; then
    rm -rf /mnt/s3/*
else
    mkdir /mnt/s3
fi