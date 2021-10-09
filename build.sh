docker network create redditor
docker run -d --network redditor --network-alias mysql --name=mysql-reddit1 -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=yuguang_reddit mysql:5.7
export DOCKER_BUILDKIT=1
docker build -t reddit-comments:0.1 .
docker rm redditor && docker run --network redditor --name redditor -p 8000:8000 reddit-comments:0.1
