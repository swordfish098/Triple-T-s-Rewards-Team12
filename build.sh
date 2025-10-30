#!/bin/bash
# This is a simple build script for AWS Amplify
echo "Starting build process for Triple-T's Rewards App"

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
flask db upgrade

echo "Build completed successfully"