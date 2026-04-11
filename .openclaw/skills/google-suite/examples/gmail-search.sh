#!/bin/bash
# example: search recent emails

gog gmail search 'newer_than:7d' --json --max 5 | jq -r '.threads[] | "[\(.id)] \(.snippet)"'
