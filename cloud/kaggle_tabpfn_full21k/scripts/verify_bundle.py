"""Xác minh gói trước mọi thao tác mô hình."""
import argparse
from common import ROOT, verify
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=str,default=str(ROOT))
    a=p.parse_args()
    data,_=verify(a.data_root)
    print('PASS: hashes/alignment/labels/IDs/finite/secret scan', {s:x[0].shape for s,x in data.items()})
