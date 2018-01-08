#!/usr/bin/env python

import oslo_messaging as messaging
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service

LOG = logging.getLogger(__name__)
conf=cfg.CONF


def get_client():
    url="rabbit://guest:guest@192.168.100.13:5672"
    transport=messaging.get_transport(conf,url)

    target = messaging.Target(topic='osprofiler',server='127.0.0.1')
    return messaging.RPCClient(transport,target)


def main():
    import pdb
    #pdb.set_trace()
    client=get_client()
    res=client.cast({},'processTrace',trace='trace text')
    print "res:::"
    print res


if __name__ == '__main__':
    main()

