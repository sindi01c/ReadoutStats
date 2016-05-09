import os
import re
import numpy as np
import pprint

from analysis_engine.node import SectionNode
from analysis_engine.utils import open_node_container


#parameters = {
    #name: [
        #phase, 'average', 0.8,
    #]
    ## discrete: 
    #name: [
        #phase, state, 80,
    #]
#}

#averages = {
    #parameter_name: {        
        #'Approach': [0.4, 0.7, 0.8],
    #},
    ## discrete
    #parameter_name: {
        #'Approach': {
            #'Warning': [],
            #'Unknown': [],
            #'-': [],
        #}
    #}
#}

for filename in os.listdir('.'):
    match = re.match(r'^(?P<frame_type>.*)\.zip$', filename)
    if not match:
        continue
    frame_name = match.groups()[0]
    print frame_name
    
    for flight_pk, nodes, attrs in open_node_container(filename):
        print flight_pk, attrs
        
        phases = {}
        parameters = {}
        for node_name, node in nodes.iteritems():
            if isinstance(node, SectionNode):
                phases[node_name] = node
            else:
                parameters[node_name] = node
        
        speedbrake = parameters.get('Speedbrake')
        print speedbrake, speedbrake.frequency
        if not speedbrake:
            continue
        airborne = phases.get('Descending')
        if not airborne:
            continue
        arrays = []
        for air in airborne:
            arrays.append(speedbrake.array[air.slice])
        print np.ma.concatenate(arrays)
        break