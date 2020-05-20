#! /usr/bin/python

# This script processes and parses the errors produced by the normalizing of the HCP-line data.
# It requires as input the directory in which the logs were written, and it outputs two files:
# (1) a JSON file that lists each subject/rater/hemi that should be excluded, and,
# (2) a JSON file that gives details about each error that it recognized.
# The script should throw an error if it encounters an error in the logs that it does not
# understand.

import sys, six, warnings, os

def die(*args):
    if len(args) > 1:
        sys.stderr.write(args[0] % tuple(args[1:]))
        sys.stderr.write('\n')
        sys.stderr.flush()
    elif len(args) > 0:
        sys.stderr.write(args[0])
        sys.stderr.write('\n')
        sys.stderr.flush()
    sys.exit(1)

try: import numpy as np
except: die('Could not import numpy library')
try: import pimms
except: die('Could not import pimms library')
try: import neuropythy as ny
except: die('Could not import neuropythy library')
try: import matplotlib, matplotlib.pyplot as plt
except: die('Could not import matplotlib library')

if len(sys.argv) < 1: die('SYNTAX: process_logs.py <directory>')
log_path = sys.argv[1]

errs = []
errnotes = ny.util.AutoDict()

for flnm in os.listdir(log_path):
    if not flnm.startswith('stderr_'): continue
    flid = int(flnm.split('_')[-1][:-4])
    flnm = os.path.join(log_path, flnm)
    st = os.stat(flnm)
    if st.st_size == 0: continue
    # read in and collect...
    with open(flnm, 'r') as fl: lns = fl.readlines()
    sid = None
    for ln in lns:
        if ': UserWarning: ' not in ln: continue
        ln = ln.strip()
        msg = ln.split(': UserWarning: ')[1:]
        if len(msg) != 1: raise ValueError('Cannot understand error from file %s: %s' % (flnm, ln))
        msg = msg[0]
        if msg.startswith('Closing'): continue # not actually an error
        (anat,h,tag,meta,bh) = (None,None,None,None,None)
        if msg.startswith('No ') and ' intersection for ' in msg:
            ss = msg.split('intersection for ')[-1].split(' / ')
            (anat,sid,h) = (ss[0], int(ss[1]), ss[2])
            tag = 'missing intersection'
            meta = msg.split(' ')
            meta = [meta[1], meta[3]]
        elif 'inverted sector label: (' in msg:
            (anat,sid,h,meta) = eval(msg.split('inverted sector label: ')[-1])
            tag = 'topological'
        elif 'inverted area label: (' in msg:
            (anat,sid,h,meta) = eval(msg.split('inverted area label: ')[-1])
            tag='topological'
        elif msg.startswith('eccen curves'):
            (anat,sid,h) = msg.split(' intersect for ')[-1].split(' / ')
            sid = int(sid)
            tag = 'illegal intersection'
            meta = msg.split(' ')
            meta = [meta[2], meta[4]]
        elif msg.startswith('Bad ordering of '):
            (anat,sid,h,meta) = msg.split(' lines for ')[-1].split(' / ')
            msg = msg.split(' for ')[-1]
            sid = int(sid)
            tag = 'topological'
        elif msg.startswith('Subject hemi has empty label: '):
            # this label is basically an addendum to previous errors
            if sid is None: raise ValueError('bad label as first error: %s' % flnm)
            continue
        elif msg.startswith('Save failure for labels: '):
            # this label is basically an addendum to previous errors
            if sid is None:
                msg = msg.split(': ')[-1].split(' / ')
                (anat,sid,h,bh) = (msg[0], msg[1], 'lh', True)
                sid = int(sid)
                tag = 'unknown'
            else: continue
        elif msg.startswith('Could not separate ventral/dorsal '):
            msg = msg.split(' ')
            (anat,sid,h) = msg[-1].split('/')
            sid = int(sid)
            meta = msg[4]
            tag = 'topological'
        elif msg.startswith('cmag calc: subject hemi has empty label: '):
            msg = msg.split(': ')[-1].strip()
            (anat,sid,h,lbl) = msg.split('/')
            sid = int(sid)
            meta = lbl
            tag = 'topological'
        elif 'fixing non-zero BC to conform:' in msg:
            # These don't matter; they are typically fine.
            continue
        elif 'failed to render fsaverage path' in msg:
            # this is a non-issue because the fsaverage paths are included for completion but
            # not because they are actually needed for anything.
            continue
        elif 'failed to render ' in msg:
            (anat,sid,h,meta) = msg.split(':')[0].split(' path ')[-1].split('/')
            sid = int(sid)
            tag = 'mesh'
        elif 'Incomplete set of lines for' in msg:
            (anat, sid, h) = msg.split(' lines for ')[-1].split(' / ')
            sid = int(sid)
            tag = 'anatomist'
        else: raise ValueError('Unrecognized warning in file %s: %s' % (flnm,ln))
        if anat != 'mean': errs.append((anat,sid,h))
        dat = errnotes[sid]
        if anat not in dat[h]: dat[h][anat] = []
        lst = dat[h][anat]
        entry = {'tag': tag, 'message': msg}
        if meta is not None: entry['metadata'] = meta
        lst.append(entry)
        if bh:
            h = ('lh' if h == 'rh' else 'rh')
            if anat not in dat[h]: dat[h][anat] = []
            lst = dat[h][anat]
            lst.append(entry)
errs = list(map(list, sorted(set(errs))))
# save the json exclusions file
ny.save(os.path.join(log_path, 'exclusions.json'), errs, 'JSON')
# and the json errors file
errnotes = {str(k):v for (k,v) in six.iteritems(errnotes)}
ny.save(os.path.join(log_path, 'errors.json'), errnotes, 'JSON')

sys.exit(0)


