#!/usr/etc/evn python
# coding=utf8
import ssl
import urllib2
import json
import re
import sys
import time
import os
# 请求header
headers = {
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
'Accept-Encoding': 'gzip, deflate, br',
'Accept-Language': 'zh-CN,en-US;q=0.7,en;q=0.3',
'Cache-Control': 'max-age=0',
'Connection': 'keep-alive',
'DNT': '1',
'Host': 'kyfw.12306.cn',
'Upgrade-Insecure-Requests': '1',
'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
}
# 解决证书问题
# ssl._create_default_https_context = ssl._create_unverified_context
# 代理功能
# proxy_handler=urllib2.ProxyHandler({'http':'http://dev-proxy.oa.com:8080', 'https':'http://dev-proxy.oa.com:8080'})
# opener=urllib2.build_opener(proxy_handler)
# urllib2.install_opener(opener)
# 转换车票信息
def convert_row(str, sname):
    cq = str.split('|')
    cw = {}
    cw['secretHBStr'] = cq[36]
    cw['secretStr'] = cq[0]
    cw['buttonTextInfo'] = cq[1]
    cu = {}
    cu['train_no'] = cq[2]
    cu['station_train_code'] = cq[3]
    cu['start_station_telecode'] = cq[4]
    cu['end_station_telecode'] = cq[5]
    cu['from_station_telecode'] = cq[6]
    cu['to_station_telecode'] = cq[7]
    cu['start_time'] = cq[8]
    cu['arrive_time'] = cq[9]
    cu['lishi'] = cq[10]
    cu['canWebBuy'] = cq[11]
    cu['yp_info'] = cq[12]
    cu['start_train_date'] = cq[13]
    cu['train_seat_feature'] = cq[14]
    cu['location_code'] = cq[15]
    cu['from_station_no'] = cq[16]
    cu['to_station_no'] = cq[17]
    cu['is_support_card'] = cq[18]
    cu['controlled_train_flag'] = cq[19]
    cu['gg_num'] = cq[20]
    cu['gr_num'] = cq[21]
    cu['qt_num'] = cq[22]
    cu['rw_num'] = cq[23]
    cu['rz_num'] = cq[24]
    cu['tz_num'] = cq[25]
    cu['wz_num'] = cq[26]
    cu['yb_num'] = cq[27]
    cu['yw_num'] = cq[28]
    cu['yz_num'] = cq[29]
    cu['ze_num'] = cq[30]
    cu['zy_num'] = cq[31]
    cu['swz_num'] = cq[32]
    cu['srrb_num'] = cq[33]
    cu['yp_ex'] = cq[34]
    cu['seat_types'] = cq[35]
    cu['exchange_train_flag'] = cq[36]
    cu['from_station_name'] = sname[cq[6]]
    cu['to_station_name'] = sname[cq[7]]
    cw['queryLeftNewDTO'] = cu
    return cw;
class TicketsChecker(object):
    # 车票字段含义，注释掉的不会在结果里
    _attrs = [
        (u'start_train_date', u'开车时间'),
        (u'from_station_name', u'起'),
        (u'to_station_name', u'止'),
        # (u'start_station_name', u'始发'),
        # (u'end_station_name', u'终点'),
        (u'station_train_code', u'车次'),
        (u'start_time', u'发车时间'),
        # (u'arrive_time', u'到达时间'),
        # (u'day_difference', u''),
        (u'lishi', u'历时'),  # %H:%M
        # (u'lishiValue', u'历时'), #分钟
        (u'swz_num', u'商务座'),
        (u'tz_num', u'特等座'),
        (u'zy_num', u'一等座'),
        (u'ze_num', u'二等座'),
        # (u'gr_num', u'高级软卧'),
        (u'rw_num', u'软卧'),
        (u'yw_num', u'硬卧'),
        # (u'rz_num', u'软座'),
        # (u'yz_num', u'硬座'),
        # (u'wz_num', u'无座'),
        # (u'qt_num', '其他')
    ]
    # 站点名称和代码映射关系临时文件
    _station_file = 'station.tmp'
    def __init__(self, src, dest, date, is_adult=True):
        print'__init__'
        self.stations = ''
        self._fetch_stations()
        self.src = TicketsChecker._translate_station(self.stations, src)
        self.dest = TicketsChecker._translate_station(self.stations, dest)
        self.date = date
        self.is_adult = is_adult
        self.trains = []
    def _handle_trains(self):
        print '_handle_trains'
        data = TicketsChecker._query_trains(self.src, self.dest, self.date, is_adult=self.is_adult)
        self.trains = map(lambda i: [i.get(k) for k in [j[0] for j in TicketsChecker._attrs]], data)
    @staticmethod
    def _query_trains(src, dest, date, **cfg):
        print '_query_trains'
        data = [
            ('leftTicketDTO.train_date', date),
            ('leftTicketDTO.from_station', src),
            ('leftTicketDTO.to_station', dest)
        ]
        if 'is_adult' in cfg:
            data.append(('purpose_codes', 'ADULT' if cfg['is_adult'] else '0X00'))
        url = 'https://kyfw.12306.cn/otn/leftTicket/queryZ?%s' % (
            '&'.join('%s=%s' % (k, v) for k, v in data))
        retry_times = 5
        while retry_times > 0:
            try:
                req = req=urllib2.Request(url, headers=headers)
                conn = urllib2.urlopen(req, timeout=5)
                text = conn.read()
                # print text.decode('utf8')
                result = json.loads(text)
                data = result.get('data',{})
                sname = data.get('map',{})
                trains = map(lambda t: convert_row(t, sname), data.get('result',[]))
                return [i.get('queryLeftNewDTO') for i in trains]
            except Exception as e:
                print 'retry %d:' % (6 - retry_times), e
            retry_times -= 1
        raise Exception('error get tickets!')
    # 获取站点名称和站点代码
    def _fetch_stations(self):
        print '_fetch_stations'
        if os.path.exists(TicketsChecker._station_file):
            with open(TicketsChecker._station_file) as f:
                self.stations = f.read().decode('utf8')
        if not self.stations:
            req=urllib2.Request('https://kyfw.12306.cn/otn/resources/js/framework/station_name.js', headers=headers)
            conn = urllib2.urlopen(req)
            self.stations = conn.read().decode('utf8')
            with open(TicketsChecker._station_file, 'w') as f:
                f.write(self.stations.encode('utf8'))
        s = self.stations.split('\'')[1].split('@')[1:]
        def tmp_fun(t):
            a = t.split('|')
            return (a[1], a[2])
        ss = map(tmp_fun ,s)
        self.stations = {}
        for k, v in ss:
            self.stations[k] = v
        # print self.stations
    # 转换站点名称为站点代码
    @staticmethod
    def _translate_station(stations, station):
        print '_translate_station'
        s = stations.get(station)
        if not s:
            print 'error translating station'
            sys.exit(1)
        return s
# 发送短信通知
def send_sms(tel, msg):
    print tel,msg
    # cmd = '/usr/local/support/bin/send_sms.pl "'+tel+'" "'+msg+'"'
    # os.system(cmd)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print 'usage:', sys.argv[0], 'from  to  date'
        sys.exit(1)
    from_ = sys.argv[1].decode('utf8')
    to_ = sys.argv[2].decode('utf8')
    date = sys.argv[3]
    if not re.match('\d{4}-\d{2}-\d{2}', date):
        print 'date should in yyyy-mm-dd format.'
        sys.exit(1)
    print 'run: ', from_.encode('utf8'), to_.encode('utf8'), date
    t = TicketsChecker(from_, to_, date)
    interval = 10
    while True:
        try:
            t._handle_trains()
            table = t.trains
            for train in table:
                if any(map(lambda n: n == u'有' or n.isdigit(), train[-6:])):
                    print train
            # train[-6:]检查所有类型的车票，应和_attrs中车票种类的数量一致
            if any([any(map(lambda n: n == u'有' or n.isdigit(), train[-6:])) for train in table]):
                break
        except:
            pass
        print 'try another time after %d sec...' % interval
        time.sleep(interval)
    # 查询到有车票的车次，短信提醒
    send_sms('152xxxxxxxx', 'haha')