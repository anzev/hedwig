import numpy as np
from scipy import stats


def binarize(matrix, attributes, bins=4):
    ''' Use a simple binning method for continous attributes '''
    target_att = attributes[-1]

    # Compute bins for each attribute
    new_attributes = []
    binarized_data = [[] for _ in range(len(matrix))]
    for i, att in enumerate(attributes):
        _, edges, membership = stats.binned_statistic(matrix[:,i], matrix[:,i], bins=bins)

        binned_attributes = []
        if att == target_att:
            # For the target attribute, use the bins as target values
            binned_attributes.append(att)
            target_values = []
            for i, _ in enumerate(edges):
                lower, upper = str(edges[i]), str(edges[(i + 1) % len(edges)])
                target_values.append('{}<={}<{}'.format(lower,att,upper))

            for j, bin_idx in enumerate(membership):
                binarized_data[j].append(target_values[bin_idx-1])
        else:
            for i in range(1, len(edges)):
                lower, upper = str(edges[i - 1]), str(edges[i])
                binned_attributes.append('{}<={}<{}'.format(lower,att,upper))

            for i, _ in enumerate(binned_attributes):
                for j, bin_idx in enumerate(membership):
                    binarized_data[j].append('0' if bin_idx-1 != i else '1')

        new_attributes = new_attributes + binned_attributes

    return binarized_data, new_attributes


def to_matrix(data, target_att):
    ''' Converts the input json data to a numpy array and a list of attributes '''
    attributes = filter(lambda key: key!=target_att, data[0].keys()) + [target_att]
    data_list = []
    for e in data:
       data_list.append([e[att] for att in attributes])

    return np.array(data_list), attributes


def dump_to_csv(data, attributes, out_file):
    ''' Output to csv for hedwig '''
    with open(out_file, 'w') as f:
        f.write('{}\n'.format(';'.join(['id'] + attributes)))

        for id, example in enumerate(data):
            f.write('{}\n'.format(';'.join([str(id)] + example)))
