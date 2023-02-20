# Controller Image
If you have access to the image of the controller. By default, once you boot the machine the process of the I2NSF controller
and PoT Controller will be started. Through a cloud-init configuration you can modify the environment variables used by the controllers.

This is the template we use for deploying the image of the controller. By default, the image uses debian/debian as the main user.
```yaml
#cloud-config 
password: debian 
ssh_pwauth: True
chpasswd:
  expire: false
write_files:
- path: /etc/environment
  content: |
    CONTROLLER_IP="CONTROLLER_IP"
    OPEN_API_IP="OPEN_API_IP"
    KAFKA_SERVERS="KAFKA_SERVERS"
  append: false
```

By default, all the contents from the different services are inside the debian use directory. Also, the environment 
variables are defined under `/etc/environment`. 

## Restarting the services
It could be the case were you want to restart one of the services.
* For the I2NSF Controller use `sudo systemctl restart i2nsf-controller.service`.
* For the PoT Controller, just restart the docker service by `sudo systemctl restart docker`

# Agent Image:

If you have access to the image of the controller. By default, once you boot the machine the process of the I2NSF
and PoT Agents will be started. Through a cloud-init configuration you can modify the environment variables used by the services.

This is the template we use for deploying the image of the nodes. By default, the image uses debian/debian as the main user. 
```yaml
#cloud-config
password: debian
ssh_pwauth: True
chpasswd:
  expire: false
write_files:
- path: /etc/environment
  content: |
    OPOT_CONTROLLER_IP="ControllerIP"
  append: false
```

## Restarting the services
It could be the case were you want to restart one of the services.
* For the I2NSF Agent use `sudo bash /home/debian/i2nsf-server/restart.sh`.
* For the PoT Node, just restart the docker service by `sudo systemctl restart docker`


# Example Usage
![](images/usage/I2NSF-OPoT_scenario.png)
## Scenario
The scenario where we have deployed 5 different machines.
* Controller: Will manage the requests to deploy the IPSec tunnel and the OPoT nodes. With the image i2nsf-pot_controller.qcow2
* Node1 and Node2: Create the communication between Alice and Bob. With the image i2nsf-pot_node.qcow2 
* Alice and Bob: Two computers that want to establish a secure communication.

Also, there are 4 different networks:
* Management: enables the communication between the nodes and the controller
    * Controller IP: 192.168.165.197
    * Node1 IP: 192.168.165.176
    * Node2 IP: 192.168.165.141
* Data: here both nodes will establish the IPSec tunnel
    * Node1 IP: 10.0.0.228
    * Node2 IP: 10.0.0.61
* Internal1: used to establish the connection between Alice and Node1
    * Alice IP: 192.168.100.94
    * Node1 IP: 192.168.100.158
* Internal2: used to establish the connection between Bob and Node2
    * Bob IP: 192.168.200.246
    * Node2 IP: 192.168.200.153

## Controller Config
This is the cloud-init config used to launch the controller:
```yaml
#cloud-config
password: debian
ssh_pwauth: True
chpasswd:
  expire: false
write_files:
- path: /etc/environment
  content: |
    CONTROLLER_IP=192.168.165.197
    OPEN_API_IP=192.168.165.197
append: false
```
Kafka has been disabled in this case. 

## Nodes Config 
This is the cloud-init config used to launch the nodes:
```yaml
#cloud-config
password: debian
ssh_pwauth: True
chpasswd:
  expire: false
write_files:
- path: /etc/environment
  content: |
    OPOT_CONTROLLER_IP=192.168.165.197
  append: false
```

## Deploying the I2NSF tunnel
Once the machines are ready and configured, we can deploy the I2NSF tunnel. One way is by using the Swagger-UI at http://192.168.165.197:5000/ui/#/I2NSF/api.create_i2nsf, where you can preview the requests, and you have some examples.
For this scenario, we will pass the following information:
```json
{
  "encAlg": [
    "3des",
    "des"
  ],
  "hardLifetime": 140,
  "intAlg": [
    "hmac-sha1-160"
  ],
  "nodes": [
    {
      "ipControl": "192.168.165.176",
      "ipData": "10.0.0.228",
      "networkInternal": "192.168.100.0/24"
    },
    {
      "ipControl": "192.168.165.141",
      "ipData": "10.0.0.61",
      "networkInternal": "192.168.200.0/24"
    }
  ],
  "softLifetime": 120
}
```
This will result in the following curl command
```bash
curl -X 'POST' \
  'http://192.168.165.197:5000/i2nsf' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "encAlg": [
    "3des",
    "des"
  ],
  "hardLifetime": 140,
  "intAlg": [
    "hmac-sha1-160"
  ],
  "nodes": [
    {
      "ipControl": "192.168.165.176",
      "ipData": "10.0.0.228",
      "networkInternal": "192.168.100.0/24"
    },
    {
      "ipControl": "192.168.165.141",
      "ipData": "10.0.0.61",
      "networkInternal": "192.168.200.0/24"
    }
  ],
  "softLifetime": 120
}'
```

For this demonstration, this has returned the following:
```json
{
  "i2nsfInfo": {
    "encAlg": "3des",
    "hardLifetime": 140,
    "intAlg": "hmac-sha1-160",
    "nodes": [
      {
        "ipControl": "192.168.165.141",
        "ipData": "10.0.0.61",
        "networkInternal": "192.168.200.0/24"
      },
      {
        "ipControl": "192.168.165.176",
        "ipData": "10.0.0.228",
        "networkInternal": "192.168.100.0/24"
      }
    ],
    "softLifetime": 120
  },
  "status": "running",
  "uuid": "bd16aed2-f1f3-45e5-9d70-d7a232583781"
}
```
It is important to keep the uuid, because it will be needed to remove the scenario.

## Deploy PoT Path:
The PoT Controller has also an API used to deploy the different PoT paths. One way to deploy the path is as before using the Swagger-UI at http://192.168.165.197:8080/opot_api/ui/#/opot/opot_sdk, where
there are examples of each endpoint. For this case, we have passed the following values.
```json
{
  "protocol":"UDP",
  "nodes":
  [
    {"mgmt_ip":"192.168.165.176","path_ip":"192.168.100.158"},
    {"mgmt_ip":"192.168.165.141","path_ip":"192.168.200.153"}
  ],
  "sender": {"ip":"192.168.100.158"},
  "receiver": {"ip":"192.168.200.153"}
}
```
Which is the same as executing 
```bash
curl -X POST \
 "http://192.168.165.197:8080/opot_api/path" -H \
 "accept: application/json" -H  "Content-Type: application/json" \ 
 -d '{
    "protocol":"UDP",
    "nodes": [
      {"mgmt_ip":"192.168.165.176","path_ip":"192.168.100.158"},
      {"mgmt_ip":"192.168.165.141","path_ip":"192.168.200.153"}
    ],
    "sender":{"ip":"192.168.100.158"},
    "receiver":{"ip":"192.168.200.153"}
  }'
```
In this case, the server has answered the following information

```json
{
  "Operative": 200,
  "creation_time": 1645198644741818,
  "masks": [
    [
      15780754819687272000,
      608917023191512600
    ]
  ],
  "nodes": [
    {
      "address": {
        "mgmt_ip": "192.168.165.176",
        "path_ip": "192.168.100.158",
        "port": 30582
      },
      "node_id": "c7869427ac53e9e1f7b3925f25746bfb",
      "node_position": 1,
      "node_type": "Ingress",
      "status": "Operative"
    },
    {
      "address": {
        "mgmt_ip": "192.168.165.141",
        "path_ip": "192.168.200.153",
        "port": 38834
      },
      "node_id": "747df83ccd881eeb3756f5465ace97d6",
      "node_position": 2,
      "node_type": "Egress",
      "status": "Operative"
    }
  ],
  "path_status": "Operative",
  "pot_id": "ab8d85ba-90d0-11ec-9b6f-fa163e0d4635",
  "protocol": "UDP"
}
```
As before, keep the uuid in order to remove the PoT path.

## Removing the I2NSF Tunnel:
To remove it just execute the following:
```bash
curl -X 'DELETE' \
  'http://192.168.165.197:5000/i2nsf/bd16aed2-f1f3-45e5-9d70-d7a232583781' \
  -H 'accept: application/json'
```
## Removing the controller Tunnel: 
To remove the PoT just execute the following:
```bash
curl -X 'DELETE' \
 'http://192.168.165.197:8080/opot_api/path/ab8d85ba-90d0-11ec-9b6f-fa163e0d4635' \ 
 -H  'accept: application/json'
```