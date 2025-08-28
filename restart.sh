#!/bin/bash

# Dừng và xóa container + network
docker compose down

# Xóa volume database
docker volume rm environment_db-data

# Khởi động lại container
docker compose up
