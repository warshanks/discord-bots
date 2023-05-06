#!/bin/sh

# Set the name of your Docker image
ImageName="warshanks/discord-bots:slim"

# Build the Docker image
docker build -t $ImageName -f dockerfile .

# Set the paths to the directories you want to mount
LocalDir1="/Users/Ben/Documents/GitHub/discord-bots/fastf1_cache"
LocalDir2="/Users/Ben/Documents/GitHub/discord-bots/src"

# Set the paths where you want to mount these directories in container
ContainerDir1="/fastf1_cache"
ContainerDir2="/app"

# Run Docker container with two directory mounts in detached mode
docker run -d -v ${LocalDir1}:${ContainerDir1} -v ${LocalDir2}:${ContainerDir2} ${ImageName}