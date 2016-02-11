'''
Wrapper for Hedwig to work within the HBP medical platform.

Example:
$ python hbp_wrapper.py test_data.json tsnr

@author: anze.vavpetic@ijs.si
'''

import json
import sys
import tempfile
from subprocess import call

import preprocess


if __name__ == '__main__':
    in_file = sys.argv[1]
    target_att = sys.argv[2]
    out_file = sys.argv[3] if len(sys.argv) > 3 else 'out.csv'
    rules_out_file = '{}.json'.format(out_file.split('.')[0])

    with open(in_file) as f:
        data = json.load(f)

    matrix, attributes = preprocess.to_matrix(data, target_att)
    binarized_data, new_attributes = preprocess.binarize(matrix, attributes)
    preprocess.dump_to_csv(binarized_data, new_attributes, out_file)

    # Call hedwig with sensible defaults
    empty_bk = tempfile.mkdtemp()
    call([
        'python', '-m', 'hedwig',
        empty_bk,
        out_file,
        '-f', 'csv',
        '-l',
        '-o', rules_out_file,
        '-a', 'none',
        '--nocache'
    ])
