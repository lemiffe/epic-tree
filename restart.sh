#!/bin/bash
docker stop epictree && docker rm epictree && docker rmi epictree_web
docker-compose up -d