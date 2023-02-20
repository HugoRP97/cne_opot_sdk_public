## Node
To install the node, you first need to copy the Dockerfile from the directory install/Dockerfiles/node/Dockerfile into the root folder of the repository.
```bash
cd cne-opot_sdk
cp ./install/Dockerfiles/node/Dockerfile
```
Then you need to build the image
```bash
docker build . -t opot_node
```
It is recommended to use the file env_vars under the node directory, and modify the necessary values. Those values will have the same utility as the file
in `/etc/default/`
