#!/bin/bash
set -e

MODEL=$1

echo "====================================="
echo " Starting Documentor Action"
echo " Workspace: $(pwd)"
echo " Model: $MODEL"
echo "====================================="

# GitHub Actions will mount the user's codebase in the current working directory.
documentor generate . --model "$MODEL"

echo "====================================="
echo " Documentation successfully generated!"
echo "====================================="
