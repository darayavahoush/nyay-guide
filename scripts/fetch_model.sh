#!/bin/sh
# Download the int8 multilingual-e5-small encoder (about 120 MB) into backend/models/. Safe to re-run. Never fails the build.
D="${1:-backend/models/multilingual-e5-small}"; B="https://huggingface.co/Xenova/multilingual-e5-small/resolve/main"
mkdir -p "$D"
[ -s "$D/tokenizer.json" ] || curl -fsSL --retry 3 -o "$D/tokenizer.json" "$B/tokenizer.json" || echo "tokenizer download failed"
[ -s "$D/model_quantized.onnx" ] || curl -fsSL --retry 3 -o "$D/model_quantized.onnx" "$B/onnx/model_quantized.onnx" || echo "model download failed"
ls -la "$D"; exit 0
