import psutil
from prometheus_client import start_http_server, Gauge
import time
import argparse
import socket
from logger import logger

def parse_args():
    parser = argparse.ArgumentParser(description='expose system and process memory and cpu usage using Prometheus')
    parser.add_argument('process_name', nargs="?", help='Name of the process to monitor')
    parser.add_argument('port', type=int, nargs="?", default=9990, help='Port number to push metrics for Prometheus server (default: 9990)')
    return parser.parse_args()

# Define Prometheus Gauges for monitor system and process CPU and Memory usage
system_memory_volume_gauge = Gauge('system_memory_volume_mb', 'Total system memory volume in MB', ['host_info'])
system_cpu_cores_gauge = Gauge('system_cpu_cores', 'Total number of CPU cores', ['host_info'])
system_memory_usage_gauge = Gauge('system_memory_usage_percent', 'Percentage of memory used in the system', ['host_info'])
system_cpu_usage_gauge = Gauge('system_cpu_usage_percent', 'Percentage of CPU used in the system', ['host_info'])
process_cpu_usage_gauge = Gauge('process_cpu_usage', 'CPU Usage of a specific process', ['process_name'])
process_memory_usage_gauge = Gauge('process_memory_usage', 'Memory Usage of a specific process in MB', ['process_name'])
process_memory_percentage_usage_gauge = Gauge('process_memory_percentage_usage', 'Memory Usage Percentage of a specific process', ['process_name'])
net_io_sent_gauge = Gauge('net_io_sent', 'KiloBytes sent over network', ['network_interface'])
net_io_recv_gauge = Gauge('net_io_recv', 'KiloBytes received over network', ['network_interface'])

def find_process_by_name(name):

    if name == None:
        return None
    
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

def get_system_cpu_usage():
    all_core = psutil.cpu_percent(interval=1, percpu=True)  # Total CPU usage in percentage
    cpu_usage_percent = sum(all_core) / len(all_core)
    return cpu_usage_percent

def get_system_usage():
    memory_usage_percent = psutil.virtual_memory().percent  # Memory usage in percentage    
    return memory_usage_percent, get_system_cpu_usage()

if __name__ == '__main__':

    # Default values
    default_expose_port = 9990

    # Setup argparse
    parser = argparse.ArgumentParser(description='expose system and process memory and cpu usage using Prometheus')
    parser.add_argument('process_name', type=str, nargs="?", default=None, help='Name of the process to monitor')
    parser.add_argument('port', type=int, nargs="?", default=None, help='Port number to push prometheus metrics')

    args = parser.parse_args()

    # Get inputs from command line or prompt user if not provided
    process_name = args.process_name or input(f"Enter process name (or press Enter to ignore process monitoring): ") or None
    port = args.port or input(f"Enter server IP (default: {default_expose_port}): ") or default_expose_port

    args = parse_args()

    start_http_server(int(port))

    try:
        host_ip = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        host_ip = None

    total_memory, total_cores = get_system_info()
    system_memory_volume_gauge.labels(host_info=host_ip).set(total_memory)
    system_cpu_cores_gauge.labels(host_info=host_ip).set(total_cores)

    net_if_addrs = psutil.net_if_addrs()
    net_ifaces = [k for k, v in net_if_addrs.items() if v]

    net_io_stats = {iface: {'bytes_sent': 0, 'bytes_recv': 0} for iface in net_ifaces}

    while True:
        memory_usage, cpu_usage = get_system_usage()
        system_memory_usage_gauge.labels(host_info=host_ip).set(memory_usage)
        system_cpu_usage_gauge.labels(host_info=host_ip).set(cpu_usage)

        process = find_process_by_name(process_name)

        logger.info("\n============================================================================================")
        logger.info(f"{'System Specification:':<30} Memory: {total_memory:.2f} MB {'':<12}   | System CPU Cores: {total_cores}")
        logger.info(f"{'System Usage:':<30} Memory Usage: {memory_usage:.2f}%  {'':<12} | CPU Usage: {cpu_usage:.2f}%")

        if process:
            try:
                process_name = process.info['name']
                pid = str(process.info['pid'])
                process_cpu_usage = process.info['cpu_percent'] / psutil.cpu_count()
                process_memory_usage = process.info['memory_info'].rss / (1024 * 1024)  # Convert bytes to MB
                process_memory_usage_percentage = process_memory_usage/total_memory * 100
                process_cpu_usage_gauge.labels(process_name=process_name).set(process_cpu_usage)
                process_memory_usage_gauge.labels(process_name=process_name).set(process_memory_usage)
                process_memory_percentage_usage_gauge.labels(process_name=process_name).set(process_memory_usage_percentage)
                logger.info(f"{process_name + ' (pid=' + pid + ')':<30} Memory Usage: {process_memory_usage:.2f} MB ({process_memory_usage_percentage:.2f}%)  | CPU Usage: {process_cpu_usage:.2f}%")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                logger.info(f"Process {process_name} not found or access denied.")
        
        
        logger.info("Network(i/o):")
        
        # Loop through each network interface
        for iface in net_ifaces:
            # Get the network interface statistics
            io_stats = psutil.net_io_counters(pernic=True)[iface]

            # Calculate the I/O rates
            bytes_sent = io_stats.bytes_sent - net_io_stats[iface]['bytes_sent']
            bytes_recv = io_stats.bytes_recv - net_io_stats[iface]['bytes_recv']

            # Update the stats dictionary
            net_io_stats[iface]['bytes_sent'] = io_stats.bytes_sent
            net_io_stats[iface]['bytes_recv'] = io_stats.bytes_recv

            # Calculate the I/O rates in KB/s
            bytes_sent_kb = bytes_sent / 1024
            bytes_recv_kb = bytes_recv / 1024

            net_io_sent_gauge.labels(network_interface=iface).set(bytes_sent_kb)
            net_io_recv_gauge.labels(network_interface=iface).set(bytes_recv_kb)

            # Print the network I/O stats
            logger.info(f"\t{iface}: {bytes_sent_kb:.2f} {'KB/s sent':<} | {bytes_recv_kb:<.2f} KB/s received")