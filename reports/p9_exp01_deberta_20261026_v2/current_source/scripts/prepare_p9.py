"""Chuẩn bị gold-aspect ASC từ SemEval/P8 frozen, không sửa hoặc tải nguồn."""
import json
from src.absa.sentiment_data import prepare_p9

if __name__=='__main__':
    m=prepare_p9()
    print(json.dumps({'status':m['status'],'splits':m['splits'],'weights':m['balanced_weights_train_only']}))
