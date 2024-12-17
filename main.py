import psutil
from prometheus_client import start_http_server, Gauge
import time
import argparse
import socket
from logger import logger

def parse_args():
    parser = argparse.ArgumentParser(description='Expose system and process memory, CPU, and disk usage using Prometheus')
    parser.add_argument('--pids', type=int, nargs="*", help='PIDs of the processes to monitor')
    parser.add_argument('--port', type=int, nargs="?", help='Port number to push metrics for Prometheus server (default: 9990)')
    return parser.parse_args()

# Define Prometheus Gauges for monitoring system CPU, Memory, Network, and Disk usage
system_memory_volume_gauge = Gauge('system_memory_volume_mb', 'Total system memory volume in MB', ['host_info'])
system_cpu_cores_gauge = Gauge('system_cpu_cores', 'Total number of CPU cores', ['host_info'])
system_memory_usage_gauge = Gauge('system_memory_usage_percent', 'Percentage of memory used in the system', ['host_info'])
system_cpu_usage_gauge = Gauge('system_cpu_usage_percent', 'Percentage of CPU used in the system', ['host_info'])
net_io_sent_gauge = Gauge('net_io_sent', 'KiloBytes sent over network', ['host_info'])
net_io_recv_gauge = Gauge('net_io_recv', 'KiloBytes received over network', ['host_info'])
system_disk_read_gauge = Gauge('system_disk_read_mb', 'Total Disk read by the system in KB', ['host_info'])
system_disk_write_gauge = Gauge('system_disk_write_mb', 'Total Disk write by the system in KB', ['host_info'])

# Define Prometheus Gauges for monitoring process CPU, Memory, Network, and Disk I/O usage
process_cpu_usage_gauge = Gauge('process_cpu_usage', 'CPU Usage of a specific process', ['pid'])
process_memory_usage_gauge = Gauge('process_memory_usage', 'Memory Usage of a specific process in MB', ['pid'])
process_memory_percentage_usage_gauge = Gauge('process_memory_percentage_usage', 'Memory Usage Percentage of a specific process', ['pid'])
process_disk_read_gauge = Gauge('process_disk_read_kb', 'Disk read by a specific process in KB', ['pid'])
process_disk_write_gauge = Gauge('process_disk_write_kb', 'Disk write by a specific process in KB', ['pid'])

def find_process(pid):
    if pid == -1:
        logger.warning("No input process. The process monitoring is disabled.")
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

    default_port = 9990

    parser = argparse.ArgumentParser(description='Expose system and process memory, CPU, and disk usage using Prometheus')
    parser.add_argument('--pids', type=int, nargs="*", help='PIDs of the processes to monitor(Multiple PIDs should be separate by space)', default=None)
    parser.add_argument('--port', type=int, nargs="?", help='Port number to push metrics for Prometheus server', default=None)

    args = parser.parse_args()

    pids_list = args.pids or input("Enter processes PIDs (press Enter to ignore processes monitoring, Multiple PIDs should be separate by space): ").split()
    for element in pids_list:
        idx = pids_list.index(element)
        if element.isdigit():
            pids_list[idx] = int(element)

    port = args.port or input(f"Enter Prometheus client port (default: {default_port}): ") or str(default_port)
    try:
        port = int(port)
    except ValueError:
        logger.error(f"Invalid port number. Using default port: {default_port}")
        port = default_port

    start_http_server(port)

    try:
        host_ip = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        host_ip = None

    total_memory, total_cores = get_system_info()
    system_memory_volume_gauge.labels(host_info=host_ip).set(total_memory)
    system_cpu_cores_gauge.labels(host_info=host_ip).set(total_cores)

    prev_net_io = psutil.net_io_counters(pernic=True)
    prev_disk_io = psutil.disk_io_counters()

    while True:
        memory_usage, cpu_usage = get_system_usage()
        system_memory_usage_gauge.labels(host_info=host_ip).set(memory_usage)
        system_cpu_usage_gauge.labels(host_info=host_ip).set(cpu_usage)

        current_disk_io = psutil.disk_io_counters()
        disk_read_rate = (current_disk_io.read_bytes - prev_disk_io.read_bytes) / (1024 * 1024)
        disk_write_rate = (current_disk_io.write_bytes - prev_disk_io.write_bytes) / (1024 * 1024)

        system_disk_read_gauge.labels(host_info=host_ip).set(disk_read_rate)
        system_disk_write_gauge.labels(host_info=host_ip).set(disk_write_rate)
        
        net_io = psutil.net_io_counters(pernic=True)

        total_sent_kb = 0
        total_recv_kb = 0
        for iface, io_counters in net_io.items():
            prev_io_counters = prev_net_io[iface]

            total_sent_kb += ((io_counters.bytes_sent - prev_io_counters.bytes_sent) / 1024) 
            total_recv_kb += ((io_counters.bytes_recv - prev_io_counters.bytes_recv) / 1024)

        prev_net_io = net_io

        net_io_sent_gauge.labels(host_info=host_ip).set(total_sent_kb)
        net_io_recv_gauge.labels(host_info=host_ip).set(total_recv_kb)

        logger.debug(f"============================ System Monitoring ============================")
        logger.debug(f"")
        logger.debug(f"System Specification:")
        logger.debug(f"Memory: {total_memory:.2f} MB | CPU Cores: {total_cores}")
        logger.debug(f"System Resource Usage: ")
        logger.debug(f"Memory: {memory_usage:.2f}% | CPU: {cpu_usage:.2f}%")
        logger.debug(f"Disk: {disk_read_rate:.2f} MB Read | {disk_write_rate:.2f} MB Write")
        logger.debug(f"Network (I/O): {total_sent_kb:.2f} KB/s sent | {total_recv_kb / 1024:.2f} KB/s received")

        logger.debug(f"")
        logger.debug("************** Process Monitoring **************")
        logger.debug(f"")
        for pid in pids_list:
            process = find_process(pid)
            if process:
                try:
                    process_name = process.name()
                    process_cpu_usage = process.cpu_percent(interval=1) / psutil.cpu_count()
                    process_memory_usage = process.memory_info().rss / (1024 * 1024)  # Convert bytes to MB
                    process_memory_usage_percentage = process_memory_usage / total_memory * 100

                    # Process Disk I/O
                    io_counters = process.io_counters()
                    process_disk_read = io_counters.read_bytes / (1024 * 1024)  
                    process_disk_write = io_counters.write_bytes / (1024 * 1024)

                    # Update Prometheus Gauges with process metrics
                    process_cpu_usage_gauge.labels(pid=pid).set(process_cpu_usage)
                    process_memory_usage_gauge.labels(pid=pid).set(process_memory_usage)
                    process_memory_percentage_usage_gauge.labels(pid=pid).set(process_memory_usage_percentage)
                    process_disk_read_gauge.labels(pid=pid).set(process_disk_read)
                    process_disk_write_gauge.labels(pid=pid).set(process_disk_write)

                    logger.debug(f"Process = {process_name} with PID={pid} Resource Usage:")
                    logger.debug(f"Memory: {process_memory_usage:.2f} MB ({process_memory_usage_percentage:.2f}%) | CPU: {process_cpu_usage:.2f}%")
                    logger.debug(f"Disk: {process_disk_read:.2f} MB read | {process_disk_write:.2f} MB write")
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.warning(f"Process with PID {pid} not found or access denied.")
        
        time.sleep(1)
