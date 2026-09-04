import logging

class IgnorePendingCountFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'admin/pending-count/' not in message
