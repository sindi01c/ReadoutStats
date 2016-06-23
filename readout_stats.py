import csv
import os
import re
import numpy as np
import itertools
import statsmodels.robust as rb
import zipfile


from collections import defaultdict

from analysis_engine.node import DerivedParameterNode, MultistateDerivedParameterNode, SectionNode
from analysis_engine.utils import open_node_container


medians = defaultdict(lambda: defaultdict(list))
#medianabsolutedev = defaultdict(lambda: defaultdict(list))

count = 0
for filename in os.listdir('.'):

    match = re.match(r'^(?P<frame_type>.*)\.zip$', filename)
    if not match:
        continue
    frame_name = match.groups()[0]
    print frame_name
    
    try:
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

                for phase in phases.itervalues():
                    arrays = []
                    for section in phase:
                        arrays.append(parameter.array[section.slice.start * parameter.hz:section.slice.stop * parameter.hz])
                    array = np.ma.concatenate(arrays)
                    
                    std = np.ma.std(array)
                    if np.ma.count(std):
                        medians[parameter.name][phase.name].append(float(std))
            if count >= 10:
                break
    except (RuntimeError, TypeError, NameError, zipfile.BadZipfile):
        pass
            

def IQR(values):
    q75, q25 = np.percentile(values, [75, 25])
    if q25 == q75:
        lt = -2*q25
        ut = 2*q75
    else:
        lt = q25-((q75-q25)*2)
        ut = q75+((q75-q25)*2)
    return lt, ut, q25, q75



with open('D:/Documents/GitHub/ReadoutStats/min_change.csv', 'wb') as file_obj:
    writer = csv.writer(file_obj)
    writer.writerow(('parameter', 'phases', 'Average STD_dev', 'Median_std_dev', 'StdDev_of_std_dev', 'MAD_std', 'q25_std','q75_std', 'lt_std','ut_std', 'min_std', 'max_std', 'avg_first_5_min_std'))
    for parameter, phases in sorted(medians.items()):
        for phase, values in sorted(phases.items()):
            values = np.array(values)
            min_values = np.sort(values)
            lt, ut, q25, q75 = IQR(values)
            writer.writerow((parameter, phase, np.mean(values), np.median(values), np.std(values), rb.scale.mad(values), q25, q75, lt, ut, np.ma.min(values), np.ma.max(values), np.mean(min_values[0:5])))