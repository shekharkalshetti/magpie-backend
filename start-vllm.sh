#!/bin/bash

echo "🚀 Starting vLLM server with Qwen2.5-1.5B-Instruct..."
echo ""
echo "Model: Qwen/Qwen2.5-1.5B-Instruct"
echo "Port: 1234"
echo "Host: 0.0.0.0"
echo ""

vllm serve Qwen/Qwen2.5-1.5B-Instruct \
  --port 1234 \
  --host 0.0.0.0 \
  --trust-remote-code \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.5 \
  --dtype auto

# Alternative: Run in background with nohup
# Uncomment below to run in background:
#
# echo "Starting vLLM in background..."
# nohup vllm serve Qwen/Qwen2.5-1.5B-Instruct \
#   --port 1234 \
#   --host 0.0.0.0 \
#   --trust-remote-code \
#   --max-model-len 4096 \
#   --gpu-memory-utilization 0.5 \
#   --dtype auto > vllm.log 2>&1 &
# 
# echo "vLLM started! Check logs with: tail -f vllm.log"
# echo "PID: $!"
