from connexion import problem
import traceback
import os
import logging
DEBUG = os.environ.get("FLASK_DEBUG", None)


def create_path_internal_error(e: Exception):
    """
    Returns the InternalServerError exception if the path was not created because there was an error in the
    OPoTController

    :param e: Exception that has been produced
    :return:
    :rtype: ConnexionResponse
    """
    logging.getLogger().exception("Error")
    return problem(status=500, title="There was an error in the server when creating the path",
                   detail=str(e))


def remove_path_internal_error(e: Exception):
    """
    Returns the InternalServerError exception if the path was not removed because there was an error in the
    OPoTController

    :param e: Exception that has been produced
    :return:
    :rtype: ConnexionResponse
    """
    return problem(status=500, title="There was an error in the server when removing the path",
                   detail=str(e))


def path_not_found(uuid):
    """
    Returns the NotFound exception if the passed path does not exists in the controller

    :return: NotFound
    :rtype: ConnexionResponse
    """
    return problem(status=404, title="The path does not exist in the controller", detail=f'The path with uuid "{uuid}" '
                                                                                         'does not exist in the '
                                                                                         'controller')
