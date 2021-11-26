import configparser
import os

class nvconfig :

    _instance = None

    @classmethod
    def _getInstance(cls):
        return cls._instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls._instance = cls(*args, **kargs)
        cls.instance = cls._getInstance

        return cls._instance

    def setInit(self, config_dir_path ):
        if config_dir_path == None :
            self._config_dir_path = os.getcwd()
        else:
            self._config_dir_path = config_dir_path

        self._config_file_path =os.path.join(self._config_dir_path, 'nvconfig.ini')
            #self._config_file_path =os.path.join(config_file_path, 'nvconfig.ini')


    def load_file(self):
        try:
            config = configparser.ConfigParser()
            config.read(self._config_file_path, 'utf-8')
            print(self._config_file_path)
            self._TELEGRAM_CHAT_ID = config['COMMON']['TELEGRAM_CHAT_ID']
            self._TELEGRAM_TOKEN = config['COMMON']['TELEGRAM_TOKEN']
            self._IMAGE_DIR_PATH = config['COMMON']['IMAGE_DIR_PATH']
            self._JSON_DIR_PATH = config['COMMON']['JSON_DIR_PATH']
            self._logDir = config['OUTPUT']['LOG_DIR_PATH']
            self._logFileName = config['OUTPUT']['LOG_FILE_NAME']
            self._logFilePath = os.path.join(self._logDir, config['OUTPUT']['LOG_FILE_NAME'])

            self._outDir = config['OUTPUT']['CTC_OUTPUT_DIR_PATH']
            self._CTC_INFO_01_FILE_PATH = os.path.join(self._outDir, config['OUTPUT']['CTC_INFO_01_TXT_FILENAME'])
            self._CTC_INFO_02_FILE_PATH = os.path.join(self._outDir, config['OUTPUT']['CTC_INFO_02_TXT_FILENAME'])
            self._CTC_INFO_03_FILE_PATH = os.path.join(self._outDir, config['OUTPUT']['CTC_INFO_03_TXT_FILENAME'])



            # chck input file
            '''
            if os.path.exists(self._LINK_FILE_PATH) == False:
                print(self._LINK_FILE_PATH + ' no file')
                return -1
            '''

            if os.path.isdir(self._logDir) == False:
                os.makedirs(os.path.join(self._logDir))

            return 0
        except KeyboardInterrupt:
            print('\n\rquit')

def run():
    try:

        cc = nvconfig('')
        #cc = cleanrp_config('')
        cc.load_file()

        print(cc._loginId)
        print(cc._loginPwd)
        print(cc._initUrl)

        print(cc._logDir)
        print(cc._logFileName)

        print('complete !!')

    except KeyboardInterrupt:
        print('\n\rquit')


if __name__ == '__main__':
    run()