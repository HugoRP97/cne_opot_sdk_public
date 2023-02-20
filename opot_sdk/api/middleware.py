"""
This file must define all the methods which are going to work as the endpoints of the API
The structure of the errors and the return values must follow what it has been specified in openapi.yaml
"""
from opot_sdk.api import errors
from opot_sdk.api.responses import create_path_response, create_default_response
from opot_sdk.opot_controller.OPoTController import OPoTController


def get_path_info(uuid):
    """
    Get the information about the path, if the uuid exists

    :param uuid: identifier of the  path
    :return: It may return the body as a dict or an error (message,error_number)
    """

    try:
        path = OPoTController().paths[uuid]
    except KeyError as e:
        return errors.path_not_found(uuid)

    return create_path_response(path)


def destroy_path(uuid):
    """
    Destroy the passed path

    :param uuid:
    :return:
    """
    try:
        OPoTController().destroy_path(uuid)
    except KeyError as e:
        return errors.path_not_found(uuid)
    except Exception as e:
        return errors.create_path_internal_error(e)
    return create_default_response('The path has been removed')


def create_path(body):
    """
    Create the requested path

    :param body: Data with a json format that will be used to create a path
    :return:
    """
    # TODO Verify that the body is correct (e.g. that two nodes are not using the same ip and port). If path not
    #  valid return 400
    try:
        uuid = OPoTController().create_path(body)
        return get_path_info(uuid)
    # TODO verify which exceptions can be thrown by the controller when creating a path.
    except Exception as e:
        return errors.create_path_internal_error(e)
