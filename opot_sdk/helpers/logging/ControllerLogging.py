import logging
import queue
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener
from opot_sdk.helpers.Singleton import Singleton
from opot_sdk.helpers.default_params.ControllerParams import controller_params

default_formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(threadName)s:%(name)s] %(message)s")


class ControllerLogging(metaclass=Singleton):
    """
    Class that is used to configure the logs of the Nodes and NodeController
    """

    def __init__(self, test=False):
        super().__init__()
        # Let's make two queue, one will be used to log the events locally and the other one will be used to send the
        # events to the controller.
        # logging.getLogger().setLevel()
        self.listeners = []
        # Then we configure the loggers
        self.root_logger = logging.getLogger('root_logger')
        self.root_logger.propagate = False
        self.error_logger = logging.getLogger('error_logger')
        self.error_logger.propagate = False
        self.flow_logger = logging.getLogger('flow_logger')
        self.flow_logger.propagate = False
        self.valid_logger = logging.getLogger('valid_logger')
        self.add_queue_listener(self.error_logger, logging.ERROR,
                                handlers=self.default_handlers(f'{controller_params.logs_path}/error.log'))
        self.add_queue_listener(self.root_logger, logging.INFO,
                                handlers=self.default_handlers(f'{controller_params.logs_path}/info.log'))
        flow_handler = FlowLogHandler(f'{controller_params.logs_path}/flow.log')
        self.add_queue_listener(self.flow_logger, logging.DEBUG, handlers=[flow_handler])

        self.add_queue_listener(self.valid_logger, logging.DEBUG,
                                [logging.FileHandler(f'{controller_params.logs_path}/valid_{datetime.now}.log', mode='a')])

        for listener in self.listeners:
            listener.start()
        if test:
            self.root_logger.setLevel(logging.CRITICAL)
            self.flow_logger.setLevel(logging.CRITICAL)
            self.error_logger.setLevel(logging.ERROR)

    def add_queue_listener(self, logger, log_level, handlers):
        q = queue.Queue()
        handler = QueueHandler(queue=q)
        handler.setFormatter(default_formatter)
        logger.addHandler(QueueHandler(queue=q))
        self.listeners.append(QueueListener(q, *handlers))
        logger.setLevel(log_level)

    @staticmethod
    def default_handlers(filename):
        handlers = [
            logging.FileHandler(filename, mode='a'),
            logging.StreamHandler()
        ]
        for h in handlers:
            h.setFormatter(default_formatter)
        return handlers


class FlowLogHandler(logging.FileHandler):

    def __init__(self, filename, mode='a'):
        super().__init__(filename, mode=mode)

    def emit(self, record: logging.LogRecord) -> None:
        # record.msg = record.msg.convert_to_csv()
        logging.FileHandler.emit(self, record)


controller_logging = ControllerLogging()
