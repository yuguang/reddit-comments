docker network create redditor
# docker run -d --network redditor --network-alias mysql --name=mysql-reddit1 -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=yuguang_reddit mysql:5.7
export DOCKER_BUILDKIT=1
docker build -t reddit-comments:0.2 .
docker rm redditor && docker run --name redditor --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -p 8000:8000 reddit-comments:0.2 # -v `pwd`/sqlite:/sqlite
