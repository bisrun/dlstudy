import logging
import logging.handlers


class Logger:
    _instance = None

    @classmethod
    def _getInstance(cls):
        return cls._instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls._instance = cls(*args, **kargs)
        cls.instance = cls._getInstance
        return cls._instance


    def setLogger(self, log_file_path):
        self.log_file_path = log_file_path
        self.logger = logging.getLogger("ctc")
        self.logger.setLevel(logging.DEBUG)

        #formatter
        formatter = logging.Formatter('%(asctime)s > %(message)s')


        self.fileHandler = logging.FileHandler(log_file_path)
        self.streamHandler = logging.StreamHandler()

        self.fileHandler.setFormatter(formatter)
        self.streamHandler.setFormatter(formatter)

        #Handler를 logging에 추가
        self.logger.addHandler(self.fileHandler)
        self.logger.addHandler(self.streamHandler)


    def getLogger(self):
        return self.logger
