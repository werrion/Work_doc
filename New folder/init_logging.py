import logging

loggers = {}


def get_logger(name, file_name=None, log_level_stream=logging.ERROR, log_level_file=logging.DEBUG,
               formatter=None, log_local=True):
    """
    loggers - dictionary of all available loggers with keys=names
    :param name:
    :param file_name: log file name without .log
    :param log_level_stream: set level logging for console
    :param log_level_file: set level logging for log file
    :param formatter:
    :param log_local:
    :return:
    """
    import os
    global loggers
    """
        Level	Numeric value
        CRITICAL	50
        ERROR	    40
        WARNING	    30
        INFO	    20
        DEBUG	    10
        NOTSET	     0
    """

    if loggers.get(name):
        return loggers.get(name)
    else:
        logger = logging.getLogger(name)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logger.setLevel(logging.DEBUG)

        if not formatter:
            formatter = logging.Formatter("%(asctime)s %(levelname)s " + "[%(name)s:%(lineno)d]%(message)s")
        if file_name:
            if log_local:
                path = os.getcwd()
                if not os.path.exists(path):
                    os.makedirs(path)
                full_file_name = os.getcwd() + f'/{file_name}.log'
            else:
                full_file_name = os.getcwd() + f'/{file_name}.log'

            file_handler = logging.FileHandler(full_file_name, 'a', 'utf-8')
            file_handler.setLevel(log_level_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(log_level_stream)
        logger.addHandler(stream_handler)
        loggers[name] = logger
        return logger


if __name__ == '__main__':
    my_str = '甜猫会向随机障碍或者前方糖果进攻'
    for each in range(1):
        log = get_logger(__name__, file_name='test', log_local=True)
        log.debug('new: {!s}'.format(my_str))
        log.debug(f'new: {my_str}')
        log.info('info')
        log.warning('warning')
        log.error('error')
        log.critical('critical')
