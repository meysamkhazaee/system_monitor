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
process_memory_usage_gauge = Gauge('process_memory_usage_', 'Memory Usage of a specific process in MB', ['process_name'])
process_memory_percentage_usage_gauge = Gauge('process_memory_percentage_usage_', 'Memory Usage Percentage of a specific process', ['process_name'])
net_io_sent_guage = Gauge('net_io_sent', 'KiloBytes sent over network')
net_io_recv_guage = Gauge('net_io_recv', 'KiloBytes received over network')

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

def get_system_cpu_usage():
    all_core = psutil.cpu_percent(interval=1, percpu=True)  # Total CPU usage in percentage

    cpu_usage_percent = 0
    for ele in all_core:
        cpu_usage_percent += ele
        
    return cpu_usage_percent/len(all_core)

def get_system_usage():
    memory_usage_percent = psutil.virtual_memory().percent  # Memory usage in percentage    
    return memory_usage_percent, get_system_cpu_usage()

if __name__ == '__main__':
    
    if len(sys.argv) != 3:
        process_name = input("Enter process name (or press Enter for 'PAPERServer'): ") or 'PAPERServer'
        port = int(input("Enter port (or press Enter for 9990): ") or 9990)

    else:
        process_name = sys.argv[1]
        port = int(sys.argv[2])

    start_http_server(port)

    # Get total system memory volume and CPU core count
    total_memory, total_cores = get_system_info()
    system_memory_volume_gauge.set(total_memory)
    system_cpu_cores_gauge.set(total_cores)

    # Get the network interface objects
    net_if_addrs = psutil.net_if_addrs()
    net_ifaces = [k for k, v in net_if_addrs.items() if v]

    # Initialize the network I/O stats dictionary
    net_io_stats = {iface: {'bytes_sent': 0, 'bytes_recv': 0} for iface in net_ifaces}
    
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
                process_cpu_usage = process.info['cpu_percent'] / psutil.cpu_count()
                process_memory_usage = process.info['memory_info'].rss / (1024 * 1024)  # Convert bytes to MB
                process_memory_usage_percentage = process_memory_usage/total_memory * 100
                process_cpu_usage_gauge.labels(process_name=process_name).set(process_cpu_usage)
                process_memory_usage_gauge.labels(process_name=process_name).set(process_memory_usage)
                process_memory_percentage_usage_gauge.labels(process_name=process_name).set(process_memory_usage_percentage)
                print("\n============================================================================================")
                print(f"{'System Specification:':<30} Memory: {total_memory:.2f} MB {'':<12}   | System CPU Cores: {total_cores}")
                print(f"{'System Usage:':<30} Memory Usage: {memory_usage:.2f}%  {'':<12} | CPU Usage: {cpu_usage:.2f}%")
                print(f"{process_name + ':(pid = '+ pid +')':<30} Memory Usage: {process_memory_usage:.2f} MB ({process_memory_usage_percentage:.2f}%) {'':<3}  | CPU Usage: {process_cpu_usage:.2f}%")
                print("Network(i/o):")
                
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

                    if iface == "enp2s0":
                        net_io_sent_guage.set(bytes_sent_kb)
                        net_io_recv_guage.set(bytes_recv_kb)

                    # Print the network I/O stats
                    print(f"\t{iface}: {bytes_sent_kb:.2f} {'KB/s sent':<} | {bytes_recv_kb:<.2f} KB/s received")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"Process {process_name} not found or access denied.")
        else:
            print(f"Process {process_name} not found.")

        time.sleep(1)