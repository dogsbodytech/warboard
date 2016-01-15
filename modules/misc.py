from time import strftime
from config import warboard_log

def log_errors(error):
    lf = open(warboard_log, 'wb')
    current_time = strftime("%d-%m-%Y %H:%M:%S: ")
    lf.write(current_time+error)
    lf.close()
