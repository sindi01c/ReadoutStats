import csv
import os
import re
import numpy as np
import itertools
import statsmodels.robust as rb
import zipfile
from data_validation.correlation_setup import get_aligned_param
from data_validation.correlation import correlate_linear


from collections import defaultdict

from analysis_engine.node import DerivedParameterNode, MultistateDerivedParameterNode, SectionNode
from analysis_engine.utils import open_node_container


medians = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
#medianabsolutedev = defaultdict(lambda: defaultdict(list))

count = 0
for filename in os.listdir('.'):

    match = re.match(r'^(?P<frame_type>.*)\.zip$', filename)
    if not match:
        continue
    frame_name = match.groups()[0]
    print frame_name
    
    #try:
    for flight_pk, nodes, attrs in open_node_container(filename):
        count += 1
        print flight_pk, attrs, count
        
        phases = {}
        test_parameters = {}        
        ref_parameters = {}
        for node_name, node in nodes.iteritems():
            if isinstance(node, SectionNode):
                phases[node_name] = node
            elif type(node) == DerivedParameterNode and node.array.dtype.kind !='S':
                test_parameters[node_name] = node
                ref_parameters[node_name] = node
            else:
                # TODO: MultistateDerivedParameterNode
                pass
        
        for test_parameter in test_parameters.itervalues():
            for phase in phases.itervalues():
                test_arrays = []
                for section in phase:
                    test_arrays.append(test_parameter.array[section.slice.start * test_parameter.hz:section.slice.stop * test_parameter.hz])
                t_arrays = np.ma.concatenate(test_arrays)
                if np.ma.count(t_arrays):
                    medians[flight_pk][test_parameter.name][phase.name].append(t_arrays)
                
        for ref_parameter in ref_parameters.itervalues():
            for phase in phases.itervalues():
                ref_arrays = []
                for section in phase:
                    ref_arrays.append(ref_parameter.array[section.slice.start * ref_parameter.hz:section.slice.stop * ref_parameter.hz])
                r_arrays = np.ma.concatenate(ref_arrays)
                if np.ma.count(r_arrays):
                    medians[flight_pk][ref_parameter.name][phase.name].append(r_arrays)
                
        if count >= 10:
            break
    #except (RuntimeError, TypeError, NameError, zipfile.BadZipfile):
        #pass
            

with open('D:/Documents/GitHub/ReadoutStats/correlation.csv', 'wb') as file_obj:
    writer = csv.writer(file_obj)
    writer.writerow(('test_parameter', 'ref_parameter', 'phases', 'Pearsone_Corr'))
    for parameter, phases in sorted(medians.items()):
        for phase, values in sorted(phases.items()):
            #values = np.array(values)
            co = correlate_linear(r_arrays, t_arrays)
            writer.writerow((test_parameter, ref_parameter, phase, co)) #np.mean(values), np.median(values), np.std(values)