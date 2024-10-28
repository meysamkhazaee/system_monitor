import psutil
from prometheus_client import start_http_server, Gauge
import time
import argparse
import socket
from logger import logger

def parse_args():
    parser = argparse.ArgumentParser(description='Expose system and process memory and CPU usage using Prometheus')
    parser.add_argument('--pids', type=int, nargs="*", help='PIDs of the processes to monitor')
    parser.add_argument('--port', type=int, nargs="?",help='Port number to push metrics for Prometheus server (default: 9990)')
    return parser.parse_args()

# Define Prometheus Gauges for monitoring system CPU, Memory, and Network usage
system_memory_volume_gauge = Gauge('system_memory_volume_mb', 'Total system memory volume in MB', ['host_info'])
system_cpu_cores_gauge = Gauge('system_cpu_cores', 'Total number of CPU cores', ['host_info'])
system_memory_usage_gauge = Gauge('system_memory_usage_percent', 'Percentage of memory used in the system', ['host_info'])
system_cpu_usage_gauge = Gauge('system_cpu_usage_percent', 'Percentage of CPU used in the system', ['host_info'])
net_io_sent_gauge = Gauge('net_io_sent', 'KiloBytes sent over network', ['host_info'])
net_io_recv_gauge = Gauge('net_io_recv', 'KiloBytes received over network', ['host_info'])

# Define Prometheus Gauges for monitoring process CPU, Memory, and Network usage
process_cpu_usage_gauge = Gauge('process_cpu_usage', 'CPU Usage of a specific process', ['pid'])
process_memory_usage_gauge = Gauge('process_memory_usage', 'Memory Usage of a specific process in MB', ['pid'])
process_memory_percentage_usage_gauge = Gauge('process_memory_percentage_usage', 'Memory Usage Percentage of a specific process', ['pid'])

def find_process(pid):
    if pid == -1:
        logger.warning("no input process. the process monitoring is disable.")
        return None
    try:
        return psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        logger.warning(f"Process with PID {pid} not found or access denied.")
        return None

def get_system_info():
    total_memory_mb = psutil.virtual_memory().total / (1024 * 1024)  # Convert bytes to MB
    total_cores = psutil.cpu_count()  # Total number of CPU cores
    return total_memory_mb, total_cores

def get_system_cpu_usage():
    all_core = psutil.cpu_percent(interval=1, percpu=True)  # Total CPU usage in percentage
    cpu_usage_percent = sum(all_core) / len(all_core)
    return cpu_usage_percent

def get_system_usage():
    memory_usage_percent = psutil.virtual_memory().percent  # Memory usage in percentage    
    return memory_usage_percent, get_system_cpu_usage()

if __name__ == '__main__':

    args = parse_args()
    pids = args.pids or [int(pid) for pid in input("Enter processes PIDs (or press Enter to ignore processes monitoring): ").split() if pid.isdigit()] or [-1]
    port = args.port or input(f"Enter prometheus client port (default: 9990): ") or 9990
    start_http_server(port)

    try:
        host_ip = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        host_ip = None

    total_memory, total_cores = get_system_info()
    system_memory_volume_gauge.labels(host_info=host_ip).set(total_memory)
    system_cpu_cores_gauge.labels(host_info=host_ip).set(total_cores)

    net_io_stats = {'bytes_sent': 0, 'bytes_recv': 0}

    while True:
        memory_usage, cpu_usage = get_system_usage()
        system_memory_usage_gauge.labels(host_info=host_ip).set(memory_usage)
        system_cpu_usage_gauge.labels(host_info=host_ip).set(cpu_usage)

        logger.debug("")
        logger.debug("============================ system monitoring ============================")
        logger.debug("")
        logger.debug(f"{'System Specification:':<30}")
        logger.debug(f"Memory: {total_memory:.2f} MB {'':<12}   | System CPU Cores: {total_cores}")
        logger.debug("")
        logger.debug(f"{'System Usage:':<30} ")
        logger.debug(f"Memory Usage: {memory_usage:.2f}%  {'':<12} | CPU Usage: {cpu_usage:.2f}%")
        logger.debug("")
        logger.debug("Network(i/o):")

        bytes_sent = 0
        bytes_recv = 0
        for iface, stats in psutil.net_io_counters(pernic=True).items():
            bytes_sent += stats.bytes_sent
            bytes_recv += stats.bytes_recv

        net_io_stats['bytes_sent'] = bytes_sent - net_io_stats['bytes_sent']
        net_io_stats['bytes_recv'] = bytes_recv - net_io_stats['bytes_recv']

        net_io_sent_gauge.labels(host_info=host_ip).set(bytes_sent / 1024)
        net_io_recv_gauge.labels(host_info=host_ip).set(bytes_recv / 1024)
        logger.debug(f"{bytes_sent / 1024:.2f} KB/s sent | {bytes_recv / 1024:.2f} KB/s received")
        
        logger.debug("")
        logger.debug("************** process monitoring **************")
        for pid in pids:
            process = find_process(pid)
            if process:
                try:
                    process_name = process.name()
                    process_cpu_usage = process.cpu_percent(interval=1) / psutil.cpu_count()
                    process_memory_usage = process.memory_info().rss / (1024 * 1024)  # Convert bytes to MB
                    process_memory_usage_percentage = process_memory_usage / total_memory * 100

                    # Update Prometheus Gauges with process metrics
                    process_cpu_usage_gauge.labels(pid=pid).set(process_cpu_usage)
                    process_memory_usage_gauge.labels(pid=pid).set(process_memory_usage)
                    process_memory_percentage_usage_gauge.labels(pid=pid).set(process_memory_usage_percentage)

                    logger.debug("")
                    logger.debug(f"{process_name + ' (pid=' + str(pid) + ')':<30} Usage:") 
                    logger.debug(f"Memory Usage: {process_memory_usage:.2f} MB ({process_memory_usage_percentage:.2f}%)  | CPU Usage: {process_cpu_usage:.2f}%")
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.debug("")
                    logger.warning(f"Process with PID {pid} not found or access denied.")


        time.sleep(1)  # Delay to avoid excessive CPU usage
