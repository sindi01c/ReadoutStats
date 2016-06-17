import csv
import os
import re
import numpy as np
import statsmodels.robust as rb
import pandas as pd
import itertools
#import seaborn as sns
import zipfile


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




medians = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
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
                elif type(node) in (DerivedParameterNode, MultistateDerivedParameterNode) and node.array.dtype.kind !='S':
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

                    if hasattr(parameter, 'values_mapping'):
                        for raw_value, state_name in parameter.values_mapping.iteritems():
                            medians[parameter.name][phase.name][state_name][flight_pk] = np.ma.sum(array == raw_value) / float(len(array))
                        else:
                            pass
                            #medians[parameter.name][phase.name][''] = np.ma.mean(array)                    
                    
                    #median = np.ma.mean(np.ma.sum(array == raw_value) / float(len(array)))
                    #if np.ma.count(median):
                        #medians[parameter.name][phase.name][state_name].append(float(median))
            #if count >= 10:
                #break        
    except (RuntimeError, TypeError, NameError, zipfile.BadZipfile):
        pass
            

#def IQR(values):
    #q75, q25 = np.percentile(values, [75, 25])
    #if q25 == q75:
        #lt = -2*q25
        #ut = 2*q75
    #else:
        #lt = q25-((q75-q25)*2)
        #ut = q75+((q75-q25)*2)
    #return lt, ut, q25, q75
    

   

with open('D:\\ReadoutStats\\multistates_stats2.csv', 'wb') as file_obj:
    writer = csv.writer(file_obj)
    writer.writerow((
        'parameter', 'phases', 'state', 'av_percentage', 'median', 'std_dev', 'min', 'max', 'lt','ut'))
    for parameter, phases in sorted(medians.items()):
        for phase, states in sorted(phases.items()):
            for state_name, value in states.iteritems():
                values = value.values()
                av = np.mean(values) 
                sd = np.std(values)
                max_m = np.max(values)
                min_m = np.min(values)
                lt = np.clip(av - (2 * sd), 0, 1)
                ut = np.clip(av + (2 * sd), 0, 1)                
                delta = ut - lt
                if delta > 0.8:
                    lt = np.clip(av - (sd / 2), 0, 1)
                    ut = np.clip(av + (sd / 2), 0, 1)
                else:
                    pass

                if lt < 0.2 and ut < 0.9:
                    lt = 0
                elif ut > 0.8 and lt > 0.1:
                    ut = 1 
                else:
                    pass

                if lt <= 0.2 and ut <= 0.2:
                    lt = 0
                    ut = 0.2
                elif lt >= 0.8 and ut >= 0.8:
                    lt = 0.8
                    ut = 1
                else:
                    pass
                   
                if lt == 0 and ut == 1:
                    if av <= 0.5:
                        lt = 0
                        ut = 0.6
                    else:
                        lt = 0.4
                        ut = 1
                else:
                    pass                
                writer.writerow((parameter, phase, state_name, av, np.median(values), sd, min_m, max_m, lt, ut))
'''
The logic is that we compute lower threshold -lt- and upper threshold -ut- as the average across all flights +/- two times the SD and we clip everything to 0 and 1.
If the gap between lt and ut is too big > 0.8, we'll use only 0.5 sd in the thresholds computations
If the lt < 0.2 and ut is < 0.9 we force it to 0. This is becasue we don't want to end up with a set of threhsolds of lt = 0 and ut =1
Similarly, if the ut > 0.8 and lt > 0.1 we force it to 1.
If the thresholds are in the 0 - 0.2 or 0.8 - 1 we clip it or 20% allowance to pass.
When lt = 0  ad ut = 1 (this happens because of large SD) it means we don't fail that param/state at all, so we look at the average and set the 
allowance to 60% having 20% of overlap
'''                