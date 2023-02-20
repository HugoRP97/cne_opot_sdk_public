import json
import socket
import logging


def prepare_socket_for_connection(server_address, service=None, protocol='TCP'):
    """
    Method which prepares the socket for incoming connections

    :param server_address: address that we will be listening for
    :param service: type of service that is running this socket
    :param protocol: protocol used UDP or TCP
    :return:
    """
    # return the socket ready for receive data.
    if protocol == 'TCP':
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(server_address)
        sock.listen(1)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(server_address)
    return sock


def send_raw_data_to_address(main_socket, data_to_send, server_address, protocol='TCP'):
    """
    Method to send data as a byte array without any encoding

    :param main_socket:
    :param data_to_send: information that is going to be sent
    :param server_address: address of the destination
    :param protocol: protocol to use TCP or UDP
    :return:
    """
    # It is important to remark that this function is just for sending a raw packet information.
    try:
        # main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM if protocol == 'TCP' else socket.SOCK_DGRAM)
        if protocol == 'TCP':
            main_socket.connect(server_address)
            main_socket.sendall(data_to_send)
            # main_socket.shutdown(socket.SHUT_RDWR)
            # main_socket.close()
        else:
            main_socket.sendto(data_to_send, server_address)
        # main_socket.close()
    except Exception as e:
        logging.exception(f'Error when sending data to {server_address}')
        raise


def extract_raw_data_from_socket(socket_connection, protocol='TCP'):
    """
    Method that will listen for an incoming packet

    :param socket_connection: socket that will listen for the incoming connections
    :type socket_connection: sock
    :param protocol: protocol where we expect to receive the information TCP or UDP
    :return: bytearray with the contents of the packet
    """
    # It is important to remark that this function do not close the socket connection.
    # It is intended to use for sending this socket to other process and extract raw byte data information.
    data_received_condition = False
    while not data_received_condition:
        if protocol == 'TCP':
            connection, client_address = socket_connection.accept()
            data = connection.recv(65507)
        else:
            data, client_address = socket_connection.recvfrom(4096)
        if not data:
            break
        data_received_condition = True
    return data


def extract_data_from_socket(socket_connection, protocol='TCP'):
    """
    Method that will listen for an incoming packet

    :param socket_connection: socket that will listen for the incoming connections
    :type socket_connection: sock
    :param protocol: protocol where we expect to receive the information TCP or UDP
    :return: json with the contents of the packet
    """

    # It is important to remark that this function do not close the socket connection.
    # It is intended to use for sending this socket to other process.
    data_received_condition = False
    data_received = {'data_error': 'Not received anything'}
    while not data_received_condition:
        if protocol == 'TCP':
            connection, client_address = socket_connection.accept()
            data = connection.recv(65507)
        else:
            data, client_address = socket_connection.recvfrom(4096)
        if not data:
            break
        data_received = data.decode('utf8')
        data_received_condition = True
    try:
        json.loads(data_received)
    except:
        pass
    return json.loads(data_received)
