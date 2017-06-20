from flask import Flask, render_template, send_file, jsonify, request
from random import randrange
import psutil

app = Flask(__name__)


def _reduce(data):
    if isinstance(data, str):
        data = float(data)
    levels = ["B", "KB", "MB", "GB", "TB", "PB"]
    levelcount = 0
    while data > 1024:
        data /= 1024
        levelcount += 1
    return str(format(data, ".2f")) + " " + str(levels[levelcount])


def _get_swap_memory():
    return {"data": psutil.swap_memory(),
            "labels": ["Total", "Used", "Free", "Percent", "s-in", "s-out"]}


def _get_virtual_memory():
    data = []
    results = psutil.virtual_memory()
    for result in results:
        data.append(_reduce(result))

    return {"data": results,
            "pp-data": data,
            "labels": ["Total", "Available", "Percent", "Used", "Free", "Active",
                       "Inactive", "Buffered", "Cached", "Shared"]}


def _get_cpu_stat():
    return {"labels": ['CTX Switches', 'Interrupts', 'Soft Interrupts', 'Sys Calls'],
            "data": psutil.cpu_stats()}


def _get_cpu_percent(percpu=False):
    if percpu:
        labels = []
        data = psutil.cpu_percent(percpu=True)
        for i in range(len(data)):
            labels.append("core_{}".format(str(i).zfill(2)))
        return {"labels": labels, "data": data}
    return psutil.cpu_percent()


def _get_cpu_timepercent():
    if psutil.LINUX:
        labels = ["User", "Nice", "System", "Idle", "IO Wait", "IRQ", "Soft IRQ", "Steal", "Guest", "Guest Nice"]
    else:
        labels = ["User", "System", "Idle", "Nice", "IRQ"]
    return {"labels": labels,
            "data": psutil.cpu_times_percent(percpu=False)}


def _get_disk_io():
    # psutil.disk_usage()
    # psutil.disk_partitions()
    return {"data": psutil.disk_io_counters(perdisk=True),
            "labels": ["reads", "writes", "rbytes", "wbytes", "rtime", "wtime", "reads_merged", "writes_merged",
                       "busy_time"]}


def _get_disk_partitions(all=False):
    return {"data": psutil.disk_partitions(all=all),
            "labels": ["device", "mountpoint", "fstype", "opts"]}


def _get_disk_usage(all=False):
    data = []
    for disk in psutil.disk_partitions(all=all):
        usage = list(psutil.disk_usage(path=disk[1]))
        for i in range(3):
            usage[i] = _reduce(usage[i])
        usage.append(disk[1])
        usage.append(disk[2])
        data.append(usage)
    return {"data": data, "labels": ["Total", "Used", "Free", "Percent", "Mountpoint", "FS Type"]}


def _get_network_io():
    return {"data": psutil.net_io_counters(pernic=True),
            "labels": ["Bytes Sent", "Bytes Received", "Packets Sent", "Packets Received", "Error In", "Error Out",
                       "Dropped In", "Dropped Out"]}


def _get_network_status():
    return {"data": psutil.net_if_stats(), "labels": ["Is Up", "Duplex", "Speed", "MTU"]}


def _get_network_addresses():
    return {"data": psutil.net_if_addrs(), "labels": ["Family", "Address", "Netmask", "Broadcast", "PTP"]}


def _get_network_connections():
    return {"data": psutil.net_connections(),
            "labels": ["fd", "Family", "Type", "laddr", "raddr", "Status", "Bound PID"]}


@app.route('/')
def main():
    system_info = {
        "cpu": _get_cpu_percent(),
        "ram": _get_virtual_memory()
    }

    return render_template('main.html', page='home', system=system_info)


@app.route('/health')
def server_health():
    cpu_info = {"status": _get_cpu_stat(),
                "utilization": _get_cpu_percent(True),
                "timepercent": _get_cpu_timepercent()}
    ram_info = {"swap": _get_swap_memory(),
                "virtual": _get_virtual_memory()}
    storage_info = {"partitions": _get_disk_partitions(),
                    "io": _get_disk_io(),
                    "usage": _get_disk_usage()}
    net_info = {"io": _get_network_io(),
                "stat": _get_network_status(),
                "addr": _get_network_addresses(),
                "conn": _get_network_connections()}
    return render_template('health.html', page='health',
                           cpu=cpu_info, ram=ram_info, storage=storage_info, net=net_info)


@app.route('/storage')
def server_storage():
    return render_template('storage.html', page='storage')


@app.route('/mock')
def design_mockup():
    # --------------- MOCK DATA ---------------
    hwTemp = [['CPU01', randrange(35, 90)],
              ['CPU02', randrange(35, 90)],
              ['Motherboard', randrange(40, 70)],
              ['RAM', randrange(30, 80)]]
    driveTemp = []
    for i in range(1, randrange(2, 5)):
        for j in range(1, randrange(3, 7)):
            driveTemp.append(['E0{0} D0{1}'.format(i, j), randrange(30, 85)])
    # ------------- end mock data -------------
    return render_template('main-mock.html', page='home', hwTemp=hwTemp, driveTemp=driveTemp)


@app.route('/img/<filename>')
def images(filename):
    return send_file('./img/' + str(filename), mimetype='image/png')


@app.route('/font/<filename>')
def fonts(filename):
    return send_file('./font/' + str(filename))


@app.route('/api/status')
@app.route('/api/status/')
def system_monitor():
    results = {}
    results['cpu'] = {
        "utilization": _get_cpu_percent(),
        "stats": _get_cpu_stat(),
        "timepercent": _get_cpu_timepercent()
    }
    results['network'] = {
        "addresses": psutil.net_if_addrs(),
        "stats": psutil.net_if_stats(),
        "io": psutil.net_io_counters(pernic=True)
    }
    results['memory'] = {
        "virtual": psutil.virtual_memory(),
        "swap": psutil.swap_memory()
    }
    disk_info = []
    for partition_info in psutil.disk_partitions():
        part_dict = {
            partition_info[1]: psutil.disk_usage(partition_info[1])
        }
        disk_info.append(part_dict)
    results['disk'] = {
        "summary": psutil.disk_partitions(),
        "utilization": disk_info
    }
    if psutil.LINUX:
        results['sensors'] = {
            "temp": psutil.sensors_temperatures()
        }
    return jsonify(results)


@app.route('/api/status/<part>')
def section_monitor(part=None):
    if "cpu" in part:
        # Providing information on the status of the CPU
        if part == "cpu_stat":
            return jsonify(_get_cpu_stat())
        if part == "cpu_percent":
            return jsonify(_get_cpu_percent(True))
        if part == "cpu_time_percent":
            return jsonify(_get_cpu_timepercent())
    if "disk" in part:
        # Providing information on the status of the Disks
        if part == "disk_partitions":
            return jsonify(_get_disk_partitions())
        if part == "disk_usage":
            return jsonify(_get_disk_usage())
        if part == "disk_io":
            return jsonify(_get_disk_io())
    if "net" in part:
        if part == "net_io":
            return jsonify(_get_network_io())
        if part == "net_stat":
            return jsonify(_get_network_status())
        if part == "net_addr":
            return jsonify(_get_network_addresses())
        if part == "net_conn":
            return jsonify(_get_network_connections())
    if "memory" in part:
        if part == "virtual_memory":
            return jsonify(_get_virtual_memory())
        if part == "swap_memory":
            return jsonify(_get_swap_memory())
    return render_template("error404.html", url=request.url)


@app.route('/api/help')
def api_help():
    return render_template('api_help.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error404.html", url=request.url)


if __name__ == '__main__':
    app.run(host='10.101.24.36', port='80')
