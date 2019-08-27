from flask_login import current_user
from .. import mongo
from datetime import datetime

def ip(ip_list):
    if ip_list.count(', ') == 1:
        ip1, ip3 = ip_list.split(', ')
        ip2 = 'None'
    elif ip_list.count(',') == 1:
        ip1, ip3 = ip_list.split(',')
        ip2 = 'None'
    elif ip_list.count(',') > 1:
        ip1, ip2, ip3 = ip_list.split(',')
    elif ip_list.count(', ') > 1:
        ip1, ip2, ip3 = ip_list.split(', ')
    else:
        raise ValueError(ip_list)
    return [ip1, ip2, ip3]

def user_log(url, ip_list):
    iplist = ip(ip_list)
    index_log = mongo.db.index_log
    index_log.insert({
        'user_id': current_user.id,
        'url': url,
        'ip_client': iplist[0],
        'ip_proxy': iplist[1],
        'ip_cloudflare': iplist[2],
        'timestamp': datetime.utcnow()
    })