### **Simple Daemon** - очень простая имитация системного сервиса или daemon

**Ссылки на литературу**
* [PEP 3143 -- Standard daemon process library](https://www.python.org/dev/peps/pep-3143/)
* [Daemon-is-not-a-service](https://www.python.org/dev/peps/pep-3143/#a-daemon-is-not-a-service)
* [zdaemon process controller for Unix-based systems](https://github.com/zopefoundation/zdaemon)
* [virtualenv](https://virtualenv.pypa.io/en/latest/)

**Задачи, которые решает данный модуль:**
* Ведение логирования на основе модуля [logging](https://docs.python.org/3/library/logging.html)
* Обработка сигналов signal.SIGINT, signal.SIGTERM на основе модуля [signal](https://docs.python.org/3/library/signal.html)
* Простая интеграция в качестве daemon в [Systemd](https://ru.wikipedia.org/wiki/Systemd)
* Два режима прерывания программы (агрессивный и пассивный см. ниже)


### **Описание возможностей:**
1. _**Логирование**_
    
    | Переменная    | Значение           | Краткое описание |
    | ------------- |:-------------------| ----------------|
    | name_app      | 'SimpleDaemon'.upper()    | наименование приложения |
    | log_lvl       | 10 | уровень логирования |
    | log_path      | '/tmp/' | директорий, где будет находиться лог файл |
    | log_name      | 'simple_daemon.log' | наименование лог файла|
    | log_format    | `'%(asctime)s - APP:[%(name)s] - [%(levelno)s]%(levelname)s - MSG:> %(message)s'` | Базовый формат ([список всех атрибутов записей в журнала](https://docs.python.org/3/library/logging.html#logrecord-attributes))  |
    
    Уровни логирования класса SimpleDaemon:
    
    | Level     | levelno  | When it’s used |
    | --------- | :---  | -------------- |
    | DEBUG    | 10 | Detailed information, typically of interest only when diagnosing problems. |
    | INFO 	   | 20 | Confirmation that things are working as expected. |
    | WARNING  | 30 | An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected. |
    | ERROR    | 40 | Due to a more serious problem, the software has not been able to perform some function. |
    | CRITICAL | 50 | A serious error, indicating that the program itself may be unable to continue running. |
    | NOTSET   | 0  | Mute
    
    см. класс SimpleDaemon.
    
    **HandlerS**
     * FileHandler:
       * Основное метсо журнала событий (log - файла, _можно переопределить_) - SimpleDaemon.log_path
       * Основное наименованиа журнала событий (log - файла, _можно переопределить_) - - SimpleDaemon.log_name
         
     * Stream(Stdout). Вывод сообщений в stdout (default: False, _можно переопределить_) - SimpleDaemon.stream
        
     * Syslog(Systemd). Вывод сообщений в /dev/log (default: False, _можно переопределить_) - SimpleDaemon.syslog
      
     Фильтрация событий journalctl
   * journalctl -f (real time)
   * journalctl _PID=$PID (filter on PID)
   * journalctl _UID=$ID (filter on user $ID)
   * journalctl -F _UID (Вывести на консоль список пользователей, о которых имеются записи в логах)

    **Ротация журнала событий**
     * Максимальный размер журнала в мегабайт (default: 1mb, _можно переопределить_) - SimpleDaemon.max_size_byte_log
     * Максимальное кол-во файлов ротации (default: 2, _можно переопределить_) - SimpleDaemon.max_count_file_rotation
  
2. **Подсистема анализа затраченного времени - Timekeeper.**
    
   Когда нужно подсчитать время работы основного While: True, то первое решение это t_end - t_start...
   Но когда нужно посдчитать время работы в разных модулях, то хочется чего-то более просто и не брасающегося в галаза.
   Timekeeper - простой класс, который сможет сказать сколько было потрачено времени на выполнение полного цикла 
   While: True + он может еще и подождать (run_interval_sec = 60 sec) если это нужно.
   
   Иногда это очень полезно...
   
 
 **Алгоритм работы:**
1. Инициализация подсистемы логирования __get_logger()
2. Инициализация обработчиков сигналов прерывания __signal_handler()
3. Возвращение объекта класса SimpleDaemon
4. Ожидание прерывания
    1. Возбуждение исключения SimpleDaemonExit, при interrupt_mode == True
    2. Изменение переменной interrupted == True, при interrupt_mode == False
    
## Примеры использования: ##
**Для пассивного режима прерывания:**
```python
from time import sleep as sp
from simple_daemon import SimpleDaemon

with SimpleDaemon('MyDaemon') as sdh:
    while True:
        if sdh.interrupted: 
            break
        sp(60)
    
        if sdh.interrupted:
            break
```
tail -f /tmp/simple_daemon.log

    2018-11-27 13:47:59,971 - MyDaemon - INFO - PID: 9215
    2018-11-27 13:47:59,972 - MyDaemon - DEBUG - Set signal handler: 2
    2018-11-27 13:47:59,972 - MyDaemon - DEBUG - Set signal handler: 15
    2018-11-27 13:47:59,972 - MyDaemon - INFO - Mode: PASSIVE

kill -15 $PID

    2018-11-27 13:50:07,032 - MyDaemon - INFO - interrupted == True
    2018-11-27 13:50:07,032 - MyDaemon - INFO - Received 2 signal.
    
**Для агрессивного режима прерывания:**
```python
    from time import sleep as sp
    from simple_daemon import SimpleDaemon

    try:
        with SimpleDaemon('MyDaemon', interrupted_mode=True) as sdh:
            while True:
                sp(60)
    except Exception as e:
        pass
```
stdout
    
    SimpleDaemon Exit
   
tail -f /var/log/simple_daemon.log
    
    2018-11-27 13:57:16,124 - MyDaemon - INFO - PID: 9450
    2018-11-27 13:57:16,125 - MyDaemon - DEBUG - Set signal handler: 2
    2018-11-27 13:57:16,125 - MyDaemon - DEBUG - Set signal handler: 15
    2018-11-27 13:57:16,125 - MyDaemon - INFO - Mode: AGGRESSIVE

kill -15 $PID

    2018-11-27 13:57:39,517 - MyDaemon - INFO - Received 2 signal.
    2018-11-27 13:57:39,517 - MyDaemon - INFO - Graceful Interrupt...

**Timekeeper: сколько врмени занял весь while True:**
```python
    from simple_daemon import Timekeeper as timekeeper
    from simple_daemon import SimpleDaemon as loop_daemon
    
    with loop_daemon(name_app='MyBestSimpleDaemon', log_path='/tmp', log_name='loop_simple_daemon.log', stream=True, log_lvl=10) as dh:
        with timekeeper(log=dh.log):
            while True:
                if dh.interrupted: break  # <- я обычно так выхожу и цикла
                
                # to do something interesting    
                pass
                
                if dh.interrupted: break  # <- я обычно так выхожу и цикла
```

**Timekeeper: пусть цикл работает с интервалом в 60 сек**
```python
    from simple_daemon import Timekeeper as timekeeper
    from simple_daemon import SimpleDaemon as loop_daemon
    
    with loop_daemon(name_app='MyBestSimpleDaemon', log_path='/tmp', log_name='loop_simple_daemon.log', stream=True, log_lvl=10) as dh:
        # run_interval_sec - указаывает сколько нужно будет подождать до следующего запуска цикла
        # + эффективный sleep - это значит, что если цикл отработал за 6 секунд а run_interval_sec = 60
        # то время ожидание будет 60 - 6 = 54 сек.
        with timekeeper(log=dh.log, run_interval_sec=60):
            while True:
                if dh.interrupted: break  # <- я обычно так выхожу и цикла
                
                # to do something interesting    
                pass
                
                if dh.interrupted: break  # <- я обычно так выхожу и цикла
```