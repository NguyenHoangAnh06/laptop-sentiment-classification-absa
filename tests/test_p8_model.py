"""BERT nhỏ trên CPU cho forward/backward/reload, không phải kết quả model thật."""
import json

import pytest
import torch
from transformers import BertConfig,BertForTokenClassification

from src.absa.extraction import AspectDataset,AspectExtractor,collate_ate,evaluate_ate
from src.absa.extraction_data import encode_sentence,load_p8_config,load_tokenizer
from src.config import PROJECT_ROOT
from scripts.train_p8 import save_model


def fixture_records():
    tokenizer=load_tokenizer(PROJECT_ROOT/'artifacts/preprocessing/p4_20261009_final/bert/tokenizer.json')
    rows=[]
    for i,text,aspects in [(0,'battery good',[{'term':'battery','start':0,'end':7,'polarity':'conflict'}]),
                           (1,'All is fine.',[])]:
        row={'sentence_id':str(i),'split':'train','text':text,'aspects':aspects}
        encoded,_=encode_sentence(row,tokenizer,split='train',max_length=128,source_file='fixture.xml')
        rows.append(encoded)
    return rows


def tiny_model():
    return BertForTokenClassification(BertConfig(vocab_size=30522,hidden_size=24,num_hidden_layers=1,
        num_attention_heads=2,intermediate_size=32,max_position_embeddings=256,num_labels=3,
        id2label={0:'O',1:'B-ASP',2:'I-ASP'},label2id={'O':0,'B-ASP':1,'I-ASP':2}))


def test_token_classifier_batch_forward_backward_and_loss_masking():
    torch.set_num_threads(2)
    records=fixture_records(); ds=AspectDataset(records,'train')
    batch=collate_ate([ds[0],ds[1]])
    assert set(batch)=={'input_ids','attention_mask','token_type_ids','labels'}
    assert (batch['labels'][batch['attention_mask']==0]==-100).all()
    model=tiny_model(); output=model(**batch)
    assert output.logits.shape==(*batch['input_ids'].shape,3)
    assert torch.isfinite(output.loss)
    output.loss.backward()
    assert model.classifier.weight.grad.abs().sum()>0


def test_checkpoint_reload_cpu_inference_empty_and_unsupported_language(tmp_path):
    torch.set_num_threads(2)
    model=tiny_model()
    # Fixture luôn dự đoán O để có expected extraction xác định.
    with torch.no_grad(): model.classifier.weight.zero_(); model.classifier.bias.copy_(torch.tensor([5.,0.,0.]))
    cfg=load_p8_config()
    save_model(model,tmp_path,cfg,PROJECT_ROOT/cfg['tokenizer'])
    extractor=AspectExtractor(tmp_path,device='cpu')
    assert extractor.extract_aspects('battery good')==[]
    assert extractor.extract_aspects('')==[]
    with pytest.raises(ValueError): extractor.extract_aspects('pin tốt',language='vi')
    with pytest.raises(ValueError): extractor.extract_aspects('battery '*200)
    records=fixture_records()
    before,p1=evaluate_ate(model,records,torch.device('cpu'),batch_size=2)
    after,p2=evaluate_ate(extractor.model,records,torch.device('cpu'),batch_size=1)
    assert before==after and p1==p2
    assert before['false_negative']==1
    p=tmp_path/'extraction_metadata.json'; metadata=json.loads(p.read_text(encoding='utf-8'))
    metadata['labels']=['negative','neutral','positive'];p.write_text(json.dumps(metadata),encoding='utf-8')
    with pytest.raises(ValueError): AspectExtractor(tmp_path,device='cpu')


def test_dataset_rejects_bad_bio_and_mixed_split():
    records=fixture_records(); records[0]['split']='test'
    with pytest.raises(ValueError): AspectDataset(records,'train')
    records=fixture_records(); records[0]['labels'][1]=2
    with pytest.raises(ValueError): AspectDataset(records,'train')


@pytest.mark.parametrize('resume',[False,True])
def test_completed_experiment_cannot_reopen_official_test(resume):
    from scripts.train_p8 import run
    from src.evaluation.error_diagnosis import file_hash
    paths=[PROJECT_ROOT/'reports/p8_20261026/selection_lock.json',
           PROJECT_ROOT/'data/interim/p8_20261026/test_predictions.jsonl']
    before=[file_hash(p) for p in paths]
    with pytest.raises(ValueError,match='Không mở lại experiment'):
        run(resume=resume)
    assert before==[file_hash(p) for p in paths]
