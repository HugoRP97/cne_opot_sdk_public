from opot_sdk.helpers.descriptors.OPotLogDescriptor import OPoTLog
from opot_sdk.helpers.logging import log_pb2, log_pb2_grpc


class LogListener(log_pb2_grpc.LogReportServicer):
    """
    This class will handle the incoming OPoTLogs
    """

    def __init__(self, paths):
        self.paths = paths

    def ingressToController(self, request_iterator, context):
        log = OPoTLog.logGRPcBuilder(request_iterator)
        self.handleLog(log)
        return log_pb2.Empty()

    def middleToController(self, request_iterator, context):
        log = OPoTLog.logGRPcBuilder(request_iterator)
        self.handleLog(log)
        return log_pb2.Empty()

    def egressToController(self, request_iterator, context):
        log = OPoTLog.logGRPcBuilder(request_iterator)
        self.handleLog(log)
        return log_pb2.Empty()

    def handleLog(self,log):
        node_id = log.node_id
        path_id = log.path_id
        self.paths[path_id].update_flow_status(log)
