#!/bin/bash

# Run this to restore the department node if the VM is destroyed.

echo "Bootstrapping B.A.D. Department Node..."

# Update package list
sudo apt-get update

# Install Python3 and pip if not present
sudo apt-get install -y python3 python3-pip

# Install Python dependencies
pip3 install discord.py PyGithub python-dotenv

echo "Dependencies installed."
echo "Ensure .env file is populated with DISCORD_TOKEN, GITHUB_TOKEN, and REPO_NAME."
