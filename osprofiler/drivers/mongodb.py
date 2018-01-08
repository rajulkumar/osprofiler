# Copyright 2016 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import oslo_messaging as messaging
from oslo_config import cfg
from osprofiler.drivers import base
from osprofiler import exc

conf=cfg.CONF

class MongoDB(base.Driver):
    def __init__(self, connection_str, db_name="osprofiler", project=None,
                 service=None, host=None, **kwargs):
        """MongoDB driver for OSProfiler."""

        super(MongoDB, self).__init__(connection_str, project=project,
                                      service=service, host=host)
        #try:
        #    from pymongo import MongoClient
        #except ImportError:
        #    raise exc.CommandError(
        #        "To use this command, you should install "
        #        "'pymongo' manually. Use command:\n "
        #        "'pip install pymongo'.")

        #client = MongoClient(self.connection_str, connect=False)
        #self.db = client[db_name]

	url="rabbit://guest:guest@192.168.100.13:5672"
	transport=messaging.get_transport(conf,url)

	target = messaging.Target(topic='osprofiler',server='127.0.0.1')
	self.rpcclient= messaging.RPCClient(transport,target)

    @classmethod
    def get_name(cls):
        return "mongodb"
    
    def db_conn(self):
        try:
            from pymongo import MongoClient
        except ImportError:
            raise exc.CommandError(
                "To use this command, you should install "
                "'pymongo' manually. Use command:\n "
                "'pip install pymongo'.")

        client = MongoClient(self.connection_str, connect=False)
        self.db = client['osprofiler']

    def db_notify(self, info):
        """Send notifications to MongoDB.

        :param info:  Contains information about trace element.
                      In payload dict there are always 3 ids:
                      "base_id" - uuid that is common for all notifications
                                  related to one trace. Used to simplify
                                  retrieving of all trace elements from
                                  MongoDB.
                      "parent_id" - uuid of parent element in trace
                      "trace_id" - uuid of current element in trace

                      With parent_id and trace_id it's quite simple to build
                      tree of trace elements, which simplify analyze of trace.

        """
        self.db_conn()
        data = info.copy()
        data["project"] = self.project
        data["service"] = self.service
        self.db.profiler.insert_one(data)
    
    def notify(self,info):
        self.rpcclient.cast({},'processTrace',trace=info)

    def list_traces(self, query, fields=[]):
        """Returns array of all base_id fields that match the given criteria

        :param query: dict that specifies the query criteria
        :param fields: iterable of strings that specifies the output fields
        """
        self.db_conn()
        ids = self.db.profiler.find(query).distinct("base_id")
        out_format = {"base_id": 1, "timestamp": 1, "_id": 0}
        out_format.update({i: 1 for i in fields})
        return [self.db.profiler.find(
                {"base_id": i}, out_format).sort("timestamp")[0] for i in ids]

    def get_report(self, base_id):
        """Retrieves and parses notification from MongoDB.

        :param base_id: Base id of trace elements.
        """
        self.db_conn()
        for n in self.db.profiler.find({"base_id": base_id}, {"_id": 0}):
            trace_id = n["trace_id"]
            parent_id = n["parent_id"]
            name = n["name"]
            project = n["project"]
            service = n["service"]
            host = n["info"]["host"]
            timestamp = n["timestamp"]

            self._append_results(trace_id, parent_id, name, project, service,
                                 host, timestamp, n)

        return self._parse_results()
