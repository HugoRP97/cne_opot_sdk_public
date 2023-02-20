from opot_sdk.helpers.logging.log_pb2 import EgressLog, MiddleLog, IngressLog


class OPoTLog:

    def __init__(self, *args, **kwargs):
        self.node_id = kwargs['node_id']
        self.path_id = kwargs['path_id']
        self.cml = kwargs['cml']
        self.secret = kwargs.get('secret',None)
        self.sequence_number = kwargs['sequence_number']
        self.timestamp = kwargs['timestamp']
        self.valid = kwargs.get('valid', None)

    # TODO this should be done inside FlowFileHandler
    def __str__(self):
        return self.convert_to_csv()

    def convert_to_csv(self):
        return f'{self.path_id},{self.node_id},{self.secret},{self.cml},{self.sequence_number},{self.valid},{self.timestamp}'

    @staticmethod
    def logGRPcBuilder(log):
        data = {}
        if type(log) is EgressLog:
            data['valid'] = log.valid
        if type(log) is IngressLog:
            data['secret'] = log.secret
        data['cml'] = log.cml
        data['node_id'] = log.node_id
        data['path_id'] = log.path_id
        data['timestamp'] = log.timestamp
        data['sequence_number'] = log.sequence_number
        return OPoTLog(**data)