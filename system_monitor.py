import psutil
from prometheus_client import start_http_server, Gauge
import time
import sys

# Define Prometheus Gauges for system and process CPU and Memory usage
system_memory_volume_gauge = Gauge('system_memory_volume_mb', 'Total system memory volume in MB')
system_cpu_cores_gauge = Gauge('system_cpu_cores', 'Total number of CPU cores')
system_memory_usage_gauge = Gauge('system_memory_usage_percent', 'Percentage of memory used in the system')
system_cpu_usage_gauge = Gauge('system_cpu_usage_percent', 'Percentage of CPU used in the system')
process_cpu_usage_gauge = Gauge('process_cpu_usage', 'CPU Usage of a specific process', ['process_name'])
process_memory_usage_gauge = Gauge('process_memory_usage', 'Memory Usage of a specific process in MB', ['process_name'])
process_memory_percentage_usage_gauge = Gauge('process_memory_percentage_usage', 'Percentage of Memory Usage of a specific process', ['process_name'])

def find_process_by_name(name):
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_info']):
        try:
            if proc.info['exe'] and name in proc.info['exe']:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def get_system_info():
    # Total memory available in MB
    total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)  # Convert bytes to MB
    total_cores = psutil.cpu_count()  # Total number of CPU cores
    return total_memory_mb, total_cores

def get_system_usage():
    memory_usage_percent = psutil.virtual_memory().percent  # Memory usage in percentage
    cpu_usage_percent = psutil.cpu_percent(interval=None)  # Total CPU usage in percentage
    return memory_usage_percent, cpu_usage_percent

if __name__ == '__main__':
    
    if len(sys.argv) != 3:
        print("Usage: python system_monitor.py <process_name> <port_prometheus>")
        sys.exit(1)

    process_name = sys.argv[1]
    port = int(sys.argv[2])

    start_http_server(port)

    # Get total system memory volume and CPU core count
    total_memory, total_cores = get_system_info()
    system_memory_volume_gauge.set(total_memory)
    system_cpu_cores_gauge.set(total_cores)

    while True:
        
        # Get current system usage
        memory_usage, cpu_usage = get_system_usage()

        system_memory_usage_gauge.set(memory_usage)
        system_cpu_usage_gauge.set(cpu_usage)

        # Get the CPU and Memory usage for the specified process
        process = find_process_by_name(process_name)
        if process:
            try:
                process_name = process.info['name']
                pid = str(process.info['pid'])
                process_cpu_usage = process.info['cpu_percent']
                process_memory_usage = process.info['memory_info'].rss / (1024 * 1024)  # Convert bytes to MB
                process_memory_usage_percentage = process_memory_usage/total_memory * 100
                process_cpu_usage_gauge.labels(process_name=process_name).set(process_cpu_usage)
                process_memory_usage_gauge.labels(process_name=process_name).set(process_memory_usage)
                process_memory_percentage_usage_gauge.labels(process_name=process_name).set(process_memory_usage_percentage)

                print(f"{'System Specification:':<30} Memory: {total_memory:.2f} MB {'':<12}   | System CPU Cores: {total_cores}")
                print(f"{'System Usage:':<30} Memory Usage: {memory_usage}%  {'':<12}  | CPU Usage: {cpu_usage}%")
                print(f"{'Process ' + process_name + ':('+ pid +')':<30} Memory Usage: {process_memory_usage:.2f} MB ({process_memory_usage_percentage:.2f}%) {'':<3} | CPU Usage: {process_cpu_usage}%\n")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"Process {process_name} not found or access denied.")
        else:
            print(f"Process {process_name} not found.")

        time.sleep(1)