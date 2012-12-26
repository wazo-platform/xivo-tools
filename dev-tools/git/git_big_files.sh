#!/usr/bin/env bash

# Shows the N biggest files in the Git history

top_n=50

function find_file_name {
    while read object_sha
    do
        git rev-list --all --objects | grep $object_sha | awk '{print $2}'
    done
}

git rev-list --all --objects | awk '{print $1}' | git cat-file --batch-check | sort -k3nr | awk '{print $1}' | head -n $top_n | find_file_name
