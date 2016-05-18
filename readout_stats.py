import csv
import os
import re
import numpy as np
import pprint

from collections import defaultdict

from analysis_engine.node import DerivedParameterNode, MultistateDerivedParameterNode, SectionNode
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




#averages = defaultdict(lambda: defaultdict(list))
#averages = defaultdict(lambda: defaultdict(list))
flights = defaultdict(lambda: defaultdict(dict))


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
            elif type(node) == DerivedParameterNode and node.array.dtype.kind !='S':
                parameters[node_name] = node
            else:
                # TODO: MultistateDerivedParameterNode
                pass
        
        for parameter in parameters.itervalues():
        
            for phase in phases.itervalues():
                arrays = []
                for section in phase:
                    arrays.append(parameter.array[section.slice.start * parameter.hz:section.slice.stop * parameter.hz])
                array = np.ma.concatenate(arrays)
                
                if not np.ma.count(array):
                    continue
                
                flights[flight_pk][parameter.name][phase.name] = np.ma.mean(array)
    #break
                #averages[parameter.name][phase.name].append(np.ma.mean(array))
                #writer.writerow((parameter.name, phase.name, np.ma.mean(array)))
                
                #for raw_value, state_name in parameter.array.values_mapping.iteritems():
                    #state_averages[parameter.name][phase.name][state_name].append(np.ma.mean(array))
    

def write_csv():
    with open('D:\\ReadoutStats\\csv_flight_data\\output.csv', 'wb') as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(('flight_pk', 'parameter', 'phases', 'value'))
        for flight_pk, parameter_phases in flights.iteritems():
            for parameter, phases in parameter_phases.iteritems():
                for phase, value in phases.iteritems():
                    writer.writerow((flight_pk, parameter, phase, value))

while True:
    try:
        write_csv()
    except:
        pass
    else:
        break


        #speedbrake = parameters.get('Speedbrake')
        #if not speedbrake:
            #continue
        #airborne = phases.get('Descending')
        #if not airborne:
            #continue
        #arrays = []
        #for air in airborne:
            #arrays.append(speedbrake.array[air.slice])
        #print np.ma.concatenate(arrays)

