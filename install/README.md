# Installation Guide
## Install the necessary packages
The project is being developed using **Python 3**.8. However, it is compatible with **Python 3.5**.

For the initial setup, execute the executable **install.sh**, which will automatically download and compile all the dependencies of the project.

If you want to install the necessary requirements for the OPoTController execute:
```bash
./install.sh controller
```

Otherwise, if you are installing only the Node execute:
```bash
./install.sh node
```

The biggest difference here, is that for the node we need to install the netopeer and sysrepo library whereas the OPoTController does not need them.  

## Controller Configuration
Once the script has been executed, we can define in the file `/etc/default/opot_controller.ini`, where it is recommended to define the following variables

```.ini
[CONTROLLER]
; IP where the Controller is going to be listening to the nodes
OPOT_CONTROLLER_IP
; Port where the controller is going to be listening for the logs of the nodes. (Default )
GRPC_CONTROLLER_PORT
; Port used by the nodes in order to establish the netconf session with nccliient
NETCONF_SSH_PORT
; Define here a value if a API to generate the keys is going to be used.
KEY_GENERATOR_API
; IP address where the controller is going to be listening for the requests of prometheus.
PROMETHEUS_IP
; Port used to open the service for the prometheus server.
PROMETHEUS_PORT
[OPENAPI]
; IP where the OpenAPI service is going to be listening for the requests.
OPEN_API_IP
; Port where the OpenAPI service is going to be listening for the requests. (Default 8080)
OPEN_API_PORT
[KAFKA]
; One or more addresses of kafka servers host1,host2:port,host3
SERVERS
; Kafka topic where the consumer is going to be subscribed.
TOPIC
```

When the file has been defined as the **example_controller_config**, you can run the service by typing python -n opot_controller.
If you want to disable kafka, you only need to remove the [KAFKA] tag and if you did setup some KAFKA options as environment variables you will need to remove them. 

## Node configuration
Like with the Controller configuration, here we must define in `/etc/default/node_config.ini` the configuration parameters for the NodeController.
These variables can be also defined as environment variables.

```.ini
[NODE]
; IP of the controller.
OPOT_CONTROLLER_IP
; Port to send the gRPC messages to the controller.
GRPC_CONTROLLER_PORT
; IP address where the node is going to be listening for netconf requests
```

When the file has been defined as the **example_node_config**, you can run the service by typing python -n opot_controller
Consider that if you want to change the netconf_ssh_port, you should change the configuration of netopeer2.

## Controller Initialization:
In order to initialize only the controller with the API on the machine, just run the following commands 

```shell
python3 -m opot_sdk -a
```

## Node Initialization:
Before running the node, first you must make sure that netopeer server is installed. By default, the script `install.sh`, installs a service and enables it in your machine. Also, the yang model for the PoT should be installed in the machine.
# Docker
There is an option to install both the controller and the node as a docker container. More information can be found [here]().
