CURRENT_DIRECTORY=`pwd`

function install_controller () {
  cp ./install/docker/controller/Dockerfile .
  docker build -t opot_controller .
  rm ./Dockerfile
}

function install_node () {
  cp ./install/docker/node/Dockerfile .
  docker build -t opot_node .
  rm ./Dockerfile
}

if [ -z $1 ]
then
  echo "\$1 is empty"
else
  if [ "$1" == "node" ]; then
    echo "[+] You have selected to install a node."
    install_node
  elif [ "$1" == "controller" ]; then
    echo "[+] You have selected to install the controller."
    install_controller
  else
    echo "[!] Bad input, you must select \n ./install.sh node \n ./install.sh controller"
  fi
fi
