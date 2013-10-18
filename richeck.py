#!/usr/bin/env python

import os
import sys
import boto
from boto import ec2
from collections import Counter

def get_region(obj):
    for r in obj.regions():
        if r.name == os.getenv('EC2_REGION'):
            return r

ec2conn = boto.connect_ec2(region=get_region(ec2))

running_instances = Counter()

for res in ec2conn.get_all_instances():
    for i in res.instances:
        if i.state == 'running' and not i.spot_instance_request_id:
            if i.vpc_id:
                vpc = "vpc"
            else:
                vpc = "classic"
            running_instances["%s_%s %s" % (i.placement,vpc,i.instance_type)] += 1

reserved_instances = Counter()
for ri in ec2conn.get_all_reserved_instances():
    if ri.state == 'active':
        if 'VPC' in ri.description:
            vpc = "vpc"
        else:
            vpc = "classic"
        reserved_instances["%s_%s %s" % (ri.availability_zone,vpc,ri.instance_type)] += ri.instance_count

for zone in set(reserved_instances).difference(set(running_instances)):
    print "Warning: You have reserved instances in %s but no instances in this zone!" % zone

for zone in running_instances:
    if running_instances[zone] > reserved_instances[zone]:
        print "Warning: You have %i more running instances than reserved instances in %s" % ((running_instances[zone] - reserved_instances[zone]), zone)
    elif running_instances[zone] < reserved_instances[zone]:
        print "Warning: You have %i unused reserved instances in %s" % ((running_instances[zone] - reserved_instances[zone]), zone)

