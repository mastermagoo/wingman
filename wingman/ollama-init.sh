#!/bin/bash

# Ollama Initialization Script
# This script runs inside the Ollama container to set up Mistral 7B

set -e

echo "Waiting for Ollama service to be ready..."
until curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "Ollama not ready, waiting..."
    sleep 2
done

echo "Ollama service is ready!"

# Check if Mistral 7B is already installed
if ollama list | grep -q "mistral:7b"; then
    echo "Mistral 7B is already installed"
else
    echo "Installing Mistral 7B model..."
    ollama pull mistral:7b
    echo "Mistral 7B model installed successfully"
fi

# Test the model
echo "Testing Mistral 7B..."
ollama run mistral:7b "Test: respond with 'OK'" --verbose

echo "Ollama initialization complete!"