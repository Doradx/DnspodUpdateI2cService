# -*- coding: utf-8 -*-
# @FileName: main.py
# @Time    : 2020/9/25 11:11
# @Author  : Dorad, cug.xia@gmail.com
# @Blog    ：https://blog.cuger.cn

import psutil
import socket
import time
from datetime import datetime
import requests

login_token = "183166,xxxxxxxxxxxxxxxxx"
domain = "cuger.cn"  # such as: xxx.cn
record_id = 'd4s9a4d6'  # find at dnspod api according to your record: https://support.dnspod.cn/api/5f562ae4e75cf42d25bf689e/
sleep_time = 30  # the time interval to query local ip, seconds


def get_local_ip():
    if_list = []
    try:
        addrs = psutil.net_if_addrs()
        for _, net_card_info in addrs.items():
            for each_ip in net_card_info:
                # print(each_ip.address,each_ip.family,each_ip)
                if each_ip.family == socket.AF_INET:  # linux socket.AF_INET=2
                    if_list.append(each_ip.address)
    except:
        pass
    for ip in if_list:
        if ip != '127.0.0.1':
            return ip
    return if_list[0]


def update_dns(ip):
    url = "https://dnsapi.cn/Record.Modify"
    payload = {
        'login_token': login_token,
        'format': 'json',
        'lang': 'cn',
        'error_on_empty': 'no',
        'domain': domain,
        'sub_domain': 'rasp',
        'record_id': record_id,
        'record_type': 'A',
        'record_line': '默认',
        'value': ip,
        'mx': '20'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'dnspod-python/0.01 (im@chuangbo.li; DNSPod.CN API v2.8)'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    res = response.json()
    if (res['status']['code'] == '1'):
        return res
    return False


def update_dns_service():
    current_ip = ''
    while True:
        new_ip = get_local_ip()
        if (current_ip != new_ip and new_ip != '127.0.0.1'):
            # 需要更新 ip
            print('%s, New Net Addr: %s' % (datetime.now(), new_ip))
            # 设置 ip
            current_ip = new_ip
            print(update_dns(new_ip))
        # sleep
        time.sleep(sleep_time)

def update_screen_service():
    import os
    import sys
    from luma.core.render import canvas
    from luma.core import cmdline, error
    from PIL import ImageFont

    try:
        import psutil
    except ImportError:
        print("The psutil library was not found. Run 'sudo -H pip install psutil' to install it.")
        sys.exit()

    def get_device(actual_args=None):
        """
        Create device from command-line arguments and return it.
        """
        if actual_args is None:
            actual_args = sys.argv[1:]
        parser = cmdline.create_parser(description='luma.examples arguments')
        args = parser.parse_args(actual_args)

        if args.config:
            # load config from file
            config = cmdline.load_config(args.config)
            args = parser.parse_args(config + actual_args)

        print(display_settings(args))

        # create device
        try:
            device = cmdline.create_device(args)
        except error.Error as e:
            parser.error(e)

        return device

    def display_settings(args):
        """
        Display a short summary of the settings.

        :rtype: str
        """
        iface = ''
        display_types = cmdline.get_display_types()
        if args.display not in display_types['emulator']:
            iface = 'Interface: {}\n'.format(args.interface)

        lib_name = cmdline.get_library_for_display_type(args.display)
        if lib_name is not None:
            lib_version = cmdline.get_library_version(lib_name)
        else:
            lib_name = lib_version = 'unknown'

        import luma.core
        version = 'luma.{} {} (luma.core {})'.format(
            lib_name, lib_version, luma.core.__version__)

        return 'Version: {}\nDisplay: {}\n{}Dimensions: {} x {}\n{}'.format(
            version, args.display, iface, args.width, args.height, '-' * 60)

    def bytes2human(n):
        """
        >>> bytes2human(10000)
        '9K'
        >>> bytes2human(100001221)
        '95M'
        """
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = int(float(n) / prefix[s])
                return '%s%s' % (value, s)
        return "%sB" % n


    def cpu_usage():
        # load average, uptime
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        av1, av2, av3 = os.getloadavg()
        return "Ld:%.1f %.1f %.1f Up: %s" \
            % (av1, av2, av3, str(uptime).split('.')[0])


    def mem_usage():
        usage = psutil.virtual_memory()
        return "Mem: %s %.0f%%" \
            % (bytes2human(usage.used), 100 - usage.percent)


    def disk_usage(dir):
        usage = psutil.disk_usage(dir)
        return "SD:  %s %.0f%%" \
            % (bytes2human(usage.used), usage.percent)


    def network(iface):
        stat = psutil.net_io_counters(pernic=True)[iface]
        return "%s: Tx%s, Rx%s" % \
            (iface, bytes2human(stat.bytes_sent), bytes2human(stat.bytes_recv))

    def cpu_temp():
        temperatures = psutil.sensors_temperatures()
        return "T: %2.1f℃" % temperatures['cpu_thermal'][0].current

    def stats(device):
        # use custom font
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    'fonts', 'Times New Roman 400.ttf'))
        font2 = ImageFont.truetype(font_path, 10)

        with canvas(device) as draw:
            draw.text((0, 0), cpu_usage(), font=font2, fill="white")
            if device.height >= 32:
                draw.text((0, 14), mem_usage(), font=font2, fill="white")

            if device.height >= 64:
                draw.text((0, 26), disk_usage('/'), font=font2, fill="white")
                draw.text((80, 26), cpu_temp(), font=font2,fill="white")
                try:
                    draw.text((0, 38), network('wlan0'), font=font2, fill="white")
                    draw.text((0, 50), 'IP: %s'%get_local_ip(),font=font2, fill="white")
                except KeyError:
                    # no wifi enabled/available
                    pass

    device = get_device()
    while True:
        stats(device)
        time.sleep(1)


import threading

if __name__ == '__main__':
    update_dns_thread=threading.Thread(target=update_dns_service)
    update_screen_thread=threading.Thread(target=update_screen_service)
    update_dns_thread.start()
    update_screen_thread.start()
    update_dns_thread.join()
    update_screen_thread.join()
