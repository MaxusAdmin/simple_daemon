""" Simple Daemon - очень простая имитация системного сервиса или daemon

Задачи, которые решает данный модуль:
 > Ведение логирования на основе модуля logging(https://docs.python.org/3/library/logging.html)
 > Обработка сигналов signal.SIGINT, signal.SIGTERM на основе модуля signal(https://docs.python.org/3/library/signal.html)
 > Простая интеграция в качестве daemon в Systemd(https://ru.wikipedia.org/wiki/Systemd)
 > Два режима прерывания программы (агрессивный и пассивный см. ниже)

Описание возможностей:
    1. Обработка сигналов прерывания. Когда используется цикл работы программы типа - "While True: pass", то нужно
       иметь возможно корректно прерывать работы данного цикла. Прервать работу можно агрессивно (когда нужно чтобы
       программа не завершала какие-либо действия и просто закончила свою работу) и пассивно (когда нужно выполнить
       какие-либо действия без прерывания а после прервать закончить свою работу (break)).

       Класс SimpleDaemon имеет параметр interrupt_mode, который определяет режим прерываний (True - агрессивный,
       False - пассивный).

       При агрессивном режиме работы будет возбуждаться исключение SimpleDaemonExit.
       При пассивном режиме работы переменная interrupted == True и исключение не возбуждается.

    2. Подсистема логирования. Подсистема логирования базируется но модуле logging.
                         +--------------+
                         | SimpleDaemon |
                         +------+-------+
                                |
           +--------------------+--------------------+
           |                    |                    |
        +-----------------+  +-----------------+  +-------------+
        | stream_handlers |  | syslog_handlers |  | FileHandler |
        +-----------------+  +-----------------+  +-------------+

       Наименование приложения - SimpleDaemon.name_app
       Формат сообщений (можно переопределить) - SimpleDaemon.log_format

       HandlerS:
         - FileHandler:
            Основное метсо журнала событий (log - файла, можно переопределить) - SimpleDaemon.log_path
            Основное наименованиа журнала событий (log - файла, можно переопределить) - - SimpleDaemon.log_name
         - Stream(Stdout)
            Вывод сообщений в stdout (default: False, можно переопределить) - SimpleDaemon.stream
         - Syslog(Systemd)
            Вывод сообщений в /dev/log (default: False, можно переопределить) - SimpleDaemon.syslog

            Фильтрация событий journalctl
                1. journalctl -f (real time)
                2. journalctl _PID=$PID (filter on PID)
                3. journalctl _UID=$ID (filter on user $ID)
                4. journalctl -F _UID (Вывести на консоль список пользователей, о которых имеются записи в логах)

       Ротация журнала событий:
         Максимальный размер журнала в мегабайт (можно переопределить, default: 1mb) - SimpleDaemon.max_size_byte_log
         Максимальное кол-во файлов ротации (можно переопределить, default: 2) - SimpleDaemon.max_count_file_rotation

       Уровни логирования:
       > DEBUG(10)    Detailed information, typically of interest only when diagnosing problems.
       > INFO(20)     Confirmation that things are working as expected.
       > WARNING(30)  An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
       > ERROR(40)    Due to a more serious problem, the software has not been able to perform some function.
       > CRITICAL(50) A serious error, indicating that the program itself may be unable to continue running.
       > NOTSET(0)    Mute

    3. Подсистема анализа затраченного времени - Timekeeper.

        Когда нужно подсчитать время работы основного While: True, то первое решение это t_end - t_start...
        Но когда нужно посдчитать время работы в разных модулях, то хочется чего-то более просто и не брасающегося в галаза.
        Timekeeper - простой класс, который сможет сказать сколько было потрачено времени на выполнение полного цикла
        While: True + он может еще и подождать (run_interval_sec = 60 sec) если это нужно.

        Иногда это очень полезно...


Алгоритм работы:
    1. Инициализация подсистемы логирования __get_logger()
    2. Инициализация обработчиков сигналов прерывания __signal_handler()
    3. Возвращение объекта класса SimpleDaemon
    4. Ожидание прерывания
        4.1 Возбуждение исключения SimpleDaemonExit, при interrupt_mode == True
        4.2 Изменение переменной interrupted == True, при interrupt_mode == False

Примеры использования:
    Для пассивного режима прерывания
    --------------------------------

    from time import sleep as sp
    from simple_daemon import SimpleDaemon

    with SimpleDaemon('MyDaemon') as sdh:
        while True:
            if sdh.interrupted: break

            sp(60)

            if sdh.interrupted: break

    log:
    2018-11-27 13:47:59,971 - MyDaemon - INFO - PID: 9215
    2018-11-27 13:47:59,972 - MyDaemon - DEBUG - Set signal handler: 2
    2018-11-27 13:47:59,972 - MyDaemon - DEBUG - Set signal handler: 15
    2018-11-27 13:47:59,972 - MyDaemon - INFO - Mode: PASSIVE


    kill SIGTERM
    2018-11-27 13:50:07,032 - MyDaemon - INFO - interrupted == True
    2018-11-27 13:50:07,032 - MyDaemon - INFO - Received 2 signal.




    Для агрессивного режима прерывания
    ----------------------------------
    from time import sleep as sp
    from simple_daemon import SimpleDaemon

    try:
        with SimpleDaemon('MyDaemon', interrupted_mode=True) as sdh:
            while True:
                sp(60)
    except Exception as e:
        pass

    stdout:
    SimpleDaemon Exit

    log:
    2018-11-27 13:57:16,124 - MyDaemon - INFO - PID: 9450
    2018-11-27 13:57:16,125 - MyDaemon - DEBUG - Set signal handler: 2
    2018-11-27 13:57:16,125 - MyDaemon - DEBUG - Set signal handler: 15
    2018-11-27 13:57:16,125 - MyDaemon - INFO - Mode: AGGRESSIVE

    kill SIGTERM
    2018-11-27 13:57:39,517 - MyDaemon - INFO - Received 2 signal.
    2018-11-27 13:57:39,517 - MyDaemon - INFO - Graceful Interrupt...



"""
import os
import signal
import logging
from logging.handlers import RotatingFileHandler, SysLogHandler
from datetime import datetime
from time import sleep

__author__ = 'Maxus Admin'
__status__ = 'production'
__version__ = '0.1'
__all__ = ['SimpleDaemon', 'Timekeeper']


class SimpleDaemonExit(Exception):
    pass


class SimpleDaemonUnknownAttribute(AttributeError):
    pass


class SimpleDaemon(object):
    # PRIVATE_Variables
    # ------------------------------------------------------------------------------------------------------------------
    _interrupted = False
    _signals = [signal.SIGINT, signal.SIGTERM]

    # PUBLIC_Variables
    # ------------------------------------------------------------------------------------------------------------------
    interrupt_mode = False
    name_app = 'SimpleDaemon'.upper()
    log_lvl = 10
    log_path = '/tmp/'
    log_name = 'simple_daemon.log'
    log_format = '%(asctime)s - APP:[%(name)s] - [%(levelno)s]%(levelname)s - MSG:> %(message)s'
    stream = False
    syslog = False

    # Rotation log const
    max_size_byte_log = 1*1024*1024
    max_count_file_rotation = 2

    def __init__(self, name_app: "The name of the application for logging", **kwargs: "see self description"):
        """I accept only named arguments. see self description.

        :param name_app: The name of the application for logging
        :param kwargs: see self description
        """
        if name_app:
            self.name_app = name_app
        public_key = [i for i in SimpleDaemon.__dict__.keys() if not i.startswith("_")]
        for key, value in kwargs.items():
            if key in public_key:
                setattr(self, key, value)
            else:
                raise SimpleDaemonUnknownAttribute("SimpleDaemon: Unknown or private class attribute: {0}".format(key))

    def __exit__(self, *args, **kwargs):
        """ exit

        :param args:
        :param kwargs:
        :return: None
        """
        self.log.info('SimpleDaemon: Graceful Interrupt...')

    def __enter__(self) -> object:
        """init log system, init signal_handler

        :return: self
        """
        self.__get_logger()

        self.log.info("PID: {0}".format(os.getpid()))
        for sig in self._signals:
            signal.signal(sig, self.__signal_handler)
            self.log.debug("SimpleDaemon: Set signal handler: {0}".format(sig))
        self.log.info("SimpleDaemon: Mode: {0}".format('aggressive'.upper() if self.interrupt_mode else 'passive'.upper()))
        return self

    def __signal_handler(self, signum, frame) -> None:
        """ Обработчик прерываний ОС

        :param signum: int number signal
        :param frame: Not use
        :return: None
        """
        if not self.interrupt_mode:
            self._interrupted = True
            self.log.debug("SimpleDaemon: Interrupted: {0}".format(self._interrupted))

        self.log.info("SimpleDaemon: Received {0} signal.".format(signum))
        if self.interrupt_mode:
            raise SimpleDaemonExit('SimpleDaemon: SimpleDaemon Exit')

    def __get_logger(self) -> None:
        """ Инициализация подсистемы логирования.

        Если self.stream_handlers == True, то лог будет выводится в stdout
        :return: None
        """
        self.log = logging.getLogger(self.name_app)
        file_handler = RotatingFileHandler(
            os.path.join(self.log_path, self.log_name),
            maxBytes=self.max_size_byte_log,
            backupCount=self.max_count_file_rotation
        )
        file_handler.setFormatter(logging.Formatter(self.log_format))
        self.log.setLevel(self.log_lvl)
        self.log.addHandler(file_handler)
        if self.stream:
            stream__handler = logging.StreamHandler()
            stream__handler.setFormatter(logging.Formatter(self.log_format))
            self.log.addHandler(stream__handler)
        if self.syslog:
            syslog__handler = SysLogHandler(address='/dev/log')
            syslog__handler.setFormatter(logging.Formatter(self.log_format))
            self.log.addHandler(syslog__handler)

    @property
    def interrupted(self):
        return self._interrupted


class Timekeeper(object):
    def __init__(self, log, run_interval_sec=60):
        self.log = log
        self.time_start = datetime.now()
        # Базовый интервал ожидания == 60 sec
        self.run_interval_sec = run_interval_sec

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.time_stop = datetime.now()
        difference = (self.time_stop - self.time_start)
        if difference.seconds == 0:
            self.log.info(f"RunTimeLoop: {difference.microseconds} microseconds")
        else:
            self.log.info(f"RunTimeLoop: {difference.seconds} seconds, {difference.microseconds} microseconds")
        if self.run_interval_sec:
            if difference.seconds < self.run_interval_sec:
                delta_sec = self.run_interval_sec - difference.seconds
                self.log.debug(f"SleepAfterLoop: {delta_sec} sec")
                sleep(delta_sec)
