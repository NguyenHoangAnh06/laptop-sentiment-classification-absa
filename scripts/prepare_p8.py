"""Chuẩn bị SemEval laptop/BIO P8 từ nguồn P1 local, không tải dữ liệu."""
import json

from src.absa.extraction_data import prepare_p8

if __name__=='__main__':
    manifest=prepare_p8()
    print(json.dumps({'status':manifest['status'],
                      'splits':{s:{k:v[k] for k in ['sentences','aspect_entities','max_sequence_length']} for s,v in manifest['splits'].items()},
                      'alignment':manifest['alignment'],'leakage':manifest['leakage']}))
