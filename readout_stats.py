import csv
import os
import re
import numpy as np
import statsmodels.robust as rb
import pandas as pd
import itertools
import seaborn as sns


from collections import defaultdict

from analysis_engine.node import DerivedParameterNode, MultistateDerivedParameterNode, SectionNode
from analysis_engine.utils import open_node_container


#DERIVED_EXCLUSIONS = {
    #'1900D': ['Speedbrake'],
#}

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




medians = defaultdict(lambda: defaultdict(list))
#medianabsolutedev = defaultdict(lambda: defaultdict(list))

count = 0
for filename in os.listdir('.'):
    match = re.match(r'^(?P<frame_type>.*)\.zip$', filename)
    if not match:
        continue
    frame_name = match.groups()[0]
    print frame_name
    
    for flight_pk, nodes, attrs in open_node_container(filename):
        count += 1
        print flight_pk, attrs, count
        
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
            #if parameter in DERIVED_EXCLUSIONS[frame_name]:
                #continue
            for phase in phases.itervalues():
                arrays = []
                for section in phase:
                    arrays.append(parameter.array[section.slice.start * parameter.hz:section.slice.stop * parameter.hz])
                array = np.ma.concatenate(arrays)
                
                median = np.ma.median(array)
                if np.ma.count(median):
                    medians[parameter.name][phase.name].append(float(median))
                #medianabsolutedev[parameter.name][phase.name] = statsmodels.robust.scale.mad(array)
                #writer.writerow((parameter.name, phase.name, np.ma.mean(array)))
                                
                #for raw_value, state_name in parameter.array.values_mapping.iteritems():
                    #state_averages[parameter.name][phase.name][state_name].append(np.ma.mean(array))
        #if count >= 10:
            #break

def IQR(values):
    q75, q25 = np.percentile(values, [75, 25])
    if q25 == q75:
        lt = -2*q25
        ut = 2*q75
    else:
        lt = q25-((q75-q25)*2)
        ut = q75+((q75-q25)*2)
    return lt, ut, q25, q75

   

with open('D:\\ReadoutStats\\1. fleet__csv_flight_data\\A319-320-321.csv', 'wb') as file_obj:
    writer = csv.writer(file_obj)
    writer.writerow(('parameter', 'phases', 'Average', 'Median', 'StdDev', 'MAD', 'q25','q75', 'lt','ut', 'min', 'max'))
    for parameter, phases in sorted(medians.items()):
        for phase, values in sorted(phases.items()):
            values = np.array(values)
            lt, ut, q25, q75 = IQR(values)
            writer.writerow((parameter, phase, np.mean(values), np.median(values), np.std(values), rb.scale.mad(values), q25, q75, lt, ut, np.ma.min(values), np.ma.max(values)))