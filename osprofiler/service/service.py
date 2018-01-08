#!/usr/bin/env python


from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service
import oslo_messaging as messaging
from osprofiler.drivers import mongodb
import pdb

conf=cfg.CONF
LOG = logging.getLogger(__name__)

#_conf_opt=[ cfg.StrOpt('log-dir',default='/var/log/',help='log path'), cfg.StrOpt('log-file',default='osp.log',help='osp log file name')]


class Manager():
    target = messaging.Target(topic='osprofiler', server='127.0.0.1')
    
    def processTrace(self,ctx,trace):
        LOG.debug("got message:::")
        LOG.debug(trace)
        #f=open("trace.txt","a")
        #f.write(trace)
	#f.write("\n")
        #f.close()
        mongodb.MongoDB('mongodb://127.0.0.1:27017').db_notify(trace)
        LOG.debug('trace processed')



class RequestSerializer(messaging.NoOpSerializer):
    def __init__(self,base=None):
        self._base=base

class Service(service.Service):
    def __init__(self,topic,host,manager=None):
        super(Service, self).__init__()
        self.rpcserver=None
        self.manager=Manager()
        self.topic=topic
        self.host=host


    def reset(self):
        """Reset a service in case it received a SIGHUP."""
        super(Service, self).reset()
    def start(self):
        """Start a service."""
        LOG.debug("Creating RPC server for service %s", self.topic)

        #ctxt = context.get_admin_context()
        endpoints = [self.manager]
        #endpoints.extend(self.manager.additional_endpoints)
        #obj_version_cap = objects.Service.get_minimum_obj_version(ctxt)
        #LOG.debug("Pinning object versions for RPC server serializer to %s",
        #          obj_version_cap)
        #serializer = objects_base.CinderObjectSerializer(obj_version_cap)
        #url="rabbit://rabbitmq:password@127.0.0.1:5672"
        url="rabbit://guest:guest@192.168.100.13:5672/"
        transport=messaging.get_transport(conf,url)

        target = messaging.Target(topic=self.topic, server=self.host)
        serializer=RequestSerializer()
        pdb.set_trace()
        self.rpcserver = messaging.get_rpc_server(transport,
                                    target,
                                    endpoints,
                                    executor='eventlet')
        self.rpcserver.start()
        LOG.debug("OSP RPC server running")


    def stop(self, graceful=False):
        """Stop a service."""
        if self.rpcserver:
            self.rpcserver.wait()
        super(Service,self).stop(graceful=True);

    def wait(self):
        """Wait for a service to shut down."""
        super(Service, self).wait()



def main():
    pdb.set_trace()
    #conf.register_opts(_conf_opt)
    conf.log_file='osp.log'
    conf.log_dir='/var/log/'
    conf.debug=True
    logging.register_options(conf)
    logging.setup(conf,'osp')
    launcher = service.ProcessLauncher(conf)
    launcher.launch_service(Service(topic='osprofiler',host='127.0.0.1'))
    LOG.info("launching service")
    launcher.wait()


if __name__== "__main__":
    main()
