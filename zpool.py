import re
import subprocess

console_output = """b'  pool: Containers'
b' state: ONLINE'
b'  scan: none requested'
b'config:'
b''
b'\tNAME        STATE     READ WRITE CKSUM'
b'\tContainers  ONLINE       0     0     0'
b'\t  sde       ONLINE       0     0     0'
b'\t  sdf       ONLINE       0     0     0'
b''
b'errors: No known data errors'
b''
b'  pool: Storage'
b' state: ONLINE'
b'  scan: none requested'
b'config:'
b''
b'\tNAME        STATE     READ WRITE CKSUM'
b'\tStorage     ONLINE       0     0     0'
b'\t  sdb       ONLINE       0     0     0'
b'\t  sdc       ONLINE       0     0     0'
b'\t  sdd       ONLINE       0     0     0'
b''
b'errors: No known data errors'"""

def get_zpool_list():
    """
    
    :return: Returns a list of names of all pools that are currently active on the system.
    :rtype: list
    """
    test = subprocess.Popen(["zpool", "list", "-Ho", "name"], stdout=subprocess.PIPE)
    result = test.communicate()[0]
    result = result.decode('utf-8')
    zpool_list = []
    for line in result.splitlines():
        m = re.search(r'\w+', line)
        if m:
            zpool_list.append(m.group(0))
    return zpool_list


def zstatus():
    """
    Gathers and returns the information from 'zpool status' command.
    :return: 
    """
    pools = re.findall(r"pool: (\w+)", console_output)
    pool_list = []
    for pool in pools:
        pool_list.append({"name":str(pool), "drive_list":[]})
    pool_index = 0
    for line in console_output.splitlines():
        if "sd" in line:
            drive = re.findall(r"(sd[b-z])\W+(\w+)\W+([0-9])+\W+([0-9])+\W+([0-9])+", line)
            print(drive)
            pool_list[pool_index]["drive_list"].append({"path": drive[0][0],
                                                        "state": drive[0][1],
                                                        "read": drive[0][2],
                                                        "write": drive[0][3],
                                                        "checksum": drive[0][4]})
        elif "state" in line:
            state = re.findall(r"state: (\w+)", str(line))
        elif "errors:" in line:
            pool_index += 1
    return pool_list


def zlist(pool=None, *args):
    """
    Gathers and returns the information from 'zpool list' command.
    :param pool: Pool name to get information about. If left blank, information about all pools returned.
    :type pool: str
    :param args: Attributes to return. If left blank, default information returned
    :return: Returns a list of dictionary objects, one for each pool
    :rtype: list
    """

    # --------- Arg List ---------
    valid_args = ["allocated", "capacity", "dedupratio", "expandsize", "fragmentation", "free", "freeing", "guid",
                  "health", "leaked", "size", "altroot", "ashift", "autoexpand", "autoreplace", "bootfs", "cachefile",
                  "comment", "dedupditto", "failmode", "listsnapshots", "readonly", "version", "name"]
    view_options = ""
    if args:
        # Adding arg to output for custom view
        view_options = "-o "
        # checking each arg passed into the method against valid options
        for arg in args:
            # if it is in the valid list, add it to the output. Otherwise, disregard it.
            if arg in valid_args:
                view_options += (str(arg) + ",")
        # take out the trailing comma at the end.
        view_options = view_options[:len(view_options)-1]
    # --------- Pool Name ---------
    # If pool arg is not supplied, insert blank string instead of None
    if not pool:
        pool = ""
    # Check to see if pool provided is a valid pool
    elif pool not in get_zpool_list():
        raise NameError
    # If pool not caught by either condition, it is a valid pool and will be used in zpool list command
    try:
        # Execute command
        command = subprocess.Popen(["zpool", "list", view_options, pool], stdout=subprocess.PIPE)
        result = command.communicate()[0]

        # Parse results to array of arrays with the following form:
        # result_array = [[title1, title2, title3...], [result1, result2, result3...]...]
        result_array = []
        for line in result.splitlines():
            list_results = re.findall(r"([A-Za-z0-9\.%\-]+) +", line)
            result_array.append(list_results)

        # taking results and creating dictionary with the following data structure:
        # list_info = {
        #   "Pool": {
        #     "title1": "result1",
        #     "title2": "result2"
        #   },
        #   "Pool2": {
        #     "title1": "result1",
        #     "title2": "result2"
        #   } ...
        # }
        list_info = {}
        if pool is not "": # if a specific pool has been selected
            list_info[pool] = {}
            for i in range(0, len(result_array[0])):
                list_info[pool][result_array[0][i]] = result_array[1][i]
        else: # if no pool was selected
            pool_list = get_zpool_list()
            for poolname in pool_list:
                list_info[poolname] = {}
                for title in result_array[0]:
                    pass







        for option in view_options:
            if pool == "":
                for selected in get_zpool_list():
                    pass
    except Exception as e:
        print(e)
















