#!/bin/bash
# example: show today's calendar events

gog calendar events primary --today --json | jq -r '.events[] | "\(.startLocal) - \(.summary)"'
