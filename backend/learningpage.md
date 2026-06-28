#docker build -t wow-gear-api -t gives image fridnely name, image is named wow-gear-api
docker run -p 8000:8000 --name wow-api-container wow-gear-api  "docker run" starts new container, -8000 is port on container and pc
#image is packaged app, container is running app