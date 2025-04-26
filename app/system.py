import time
import psutil
import os
import threading


def measure_performance(func):
    """
    Декоратор для измерения времени выполнения, потребления памяти и пикового потребления памяти функции.
    
    :param func: Функция, которую нужно измерить.
    """
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())  # берем текущий процесс
        
        start_memory = process.memory_info().rss
        peak_memory = start_memory
        
        stop_monitoring = threading.Event()
        
        def monitor_memory():
            nonlocal peak_memory  # переменная родительской функции

            while not stop_monitoring.is_set():
                current_memory = process.memory_info().rss
                peak_memory = max(peak_memory, current_memory)

                time.sleep(0.1)
        
        memory_monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        memory_monitor_thread.start()
        
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
        finally:
            stop_monitoring.set()
            memory_monitor_thread.join()
        
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        peak_memory_used = peak_memory / (1024 ** 2)  # в мб
        
        print(f"[{func.__name__}] Time: {elapsed_time:.2f} seconds")
        print(f"[{func.__name__}] Peak memory used: {peak_memory_used:.3f} MB")
        
        return result
    
    return wrapper
