"""BERT nhỏ/fixtures kiểm ASC forward/reload và ABSA wrapper, không phải benchmark thật."""
import copy

import pytest
import torch
from transformers import BertConfig,BertForSequenceClassification

from src.absa.sentiment import AspectSentimentClassifier,AspectSentimentDataset,evaluate_asc
from src.absa.sentiment_data import asc_tokenizer,build_asc_samples,load_p9_config
from src.config import PROJECT_ROOT
from src.inference.absa import AspectAnalyzer
from src.sentiment.bert import collate_tokens
from scripts.train_p9 import save_asc_model
from scripts.evaluate_p9_end_to_end import build_end_to_end_inputs


def records():
    text='battery good keyboard bad'
    row={'uid':'train:fixture','sentence_id':'fixture','original_split':'train','split':'train','text':text,'source_file':'fixture.xml',
         'aspects':[{'term':'battery','start':0,'end':7,'polarity':'positive'},
                    {'term':'keyboard','start':13,'end':21,'polarity':'negative'}]}
    t=asc_tokenizer(PROJECT_ROOT/'artifacts/preprocessing/p4_20261009_final/bert/tokenizer.json')
    return build_asc_samples([row],t,128)[0],t,row


def tiny_model():
    return BertForSequenceClassification(BertConfig(vocab_size=30522,hidden_size=24,num_hidden_layers=1,
        num_attention_heads=2,intermediate_size=32,num_labels=3,id2label={0:'negative',1:'neutral',2:'positive'},
        label2id={'negative':0,'neutral':1,'positive':2}))


def test_asc_forward_backward_no_metadata_and_reload_cpu(tmp_path):
    torch.set_num_threads(2)
    rows,t,_=records(); ds=AspectSentimentDataset(rows,'train');batch=collate_tokens([ds[0],ds[1]])
    assert set(batch)=={'input_ids','attention_mask','token_type_ids','labels'}
    model=tiny_model(); output=model(**batch);assert output.logits.shape==(2,3) and torch.isfinite(output.loss)
    output.loss.backward();assert model.classifier.weight.grad.abs().sum()>0
    with torch.no_grad(): model.classifier.weight.zero_();model.classifier.bias.copy_(torch.tensor([0.,0.,5.]))
    cfg=load_p9_config(); tpath=tmp_path/'source_tokenizer.json';t.save(str(tpath))
    save_asc_model(model,tmp_path/'model',cfg,tpath)
    classifier=AspectSentimentClassifier(tmp_path/'model',device='cpu')
    a,p1=evaluate_asc(model,rows,torch.device('cpu'),batch_size=2)
    b,p2=evaluate_asc(classifier.model,rows,torch.device('cpu'),batch_size=1)
    assert a==b and p1==p2
    assert classifier.classify_aspect_sentiment('battery good','battery')['sentiment']=='positive'
    assert classifier.classify_aspect_sentiment('battery good','battery')['confidence'] is None
    with pytest.raises(ValueError): classifier.classify_aspect_sentiment('pin tốt','pin',language='vi')


def test_dataset_rejects_invalid_labels_and_wrong_marker_order():
    rows,_,_=records();rows[0]['label_id']=3
    with pytest.raises(ValueError): AspectSentimentDataset(rows,'train')
    rows,_,_=records();a=rows[0]['input_ids'].index(1);b=rows[0]['input_ids'].index(2)
    rows[0]['input_ids'][a],rows[0]['input_ids'][b]=2,1
    with pytest.raises(ValueError): AspectSentimentDataset(rows,'train')


def test_end_to_end_input_uses_predicted_spans_not_gold():
    _,t,row=records()
    row['extraction_aspects']=[{'term':'battery','start':0,'end':7}]
    pred=[{'uid':row['uid'],'text':row['text'],'predicted_aspects':[{'term':'good','start':8,'end':12}]}]
    inputs,mapping=build_end_to_end_inputs([row],pred,t,128)
    assert len(inputs)==1 and inputs[0]['label_id'] is None
    assert '[unused0]good[unused1]' in inputs[0]['marked_text']
    assert mapping[0][1]['term']=='good'


def test_wrapper_opposite_aspects_and_empty_result():
    class Extractor:
        def extract_aspects(self,text,language='en'):
            return [] if text=='empty' else [{'term':'battery','start':0,'end':7},{'term':'keyboard','start':13,'end':21}]
    class Classifier:
        def classify_many(self,text,aspects,language='en'):
            return [{'aspect':a['term'],'sentiment':p,'confidence':None} for a,p in zip(aspects,['positive','negative'])]
    analyzer=AspectAnalyzer(Extractor(),Classifier())
    result=analyzer.analyze_aspects('battery good keyboard bad')
    assert [r['sentiment'] for r in result]==['positive','negative']
    assert all(r['aspect_score'] is None and r['sentiment_score'] is None for r in result)
    assert analyzer.analyze_aspects('empty')==[]


@pytest.mark.parametrize('resume',[False,True])
def test_completed_asc_cannot_reopen_test(resume):
    from scripts.train_p9 import run
    from src.evaluation.error_diagnosis import file_hash
    paths=[PROJECT_ROOT/'reports/p9_20261026/selection_lock.json',PROJECT_ROOT/'data/interim/p9_20261026/test_predictions.jsonl']
    before=[file_hash(p) for p in paths]
    with pytest.raises(ValueError,match='Không mở lại ASC'): run(resume=resume)
    assert before==[file_hash(p) for p in paths]


def test_completed_end_to_end_cannot_reopen_inference():
    from scripts.evaluate_p9_end_to_end import evaluate_end_to_end
    from src.evaluation.error_diagnosis import file_hash
    path=PROJECT_ROOT/'data/interim/p9_20261026/test_end_to_end_predictions.jsonl'; before=file_hash(path)
    with pytest.raises(ValueError,match='Không mở lại end-to-end'): evaluate_end_to_end()
    assert file_hash(path)==before


def test_deberta_occurrence_markers_forward_reload_cpu(tmp_path):
    """Fixture DeBERTa nhỏ; tokenizer cache local, không tải mạng hoặc train benchmark."""
    from transformers import AutoTokenizer,DebertaV2Config,DebertaV2ForSequenceClassification
    from src.absa.sentiment_backbone import encode_record
    from scripts.p9_exp01 import NAMESPACE
    tokenizer=AutoTokenizer.from_pretrained(PROJECT_ROOT/f'data/processed/{NAMESPACE}',local_files_only=True)
    text='battery good but battery bad'
    rows=[]
    for index,(start,label) in enumerate([(0,2),(17,0)]):
        rows.append(encode_record({'text':text,'aspect':'battery','start':start,'end':start+7,
                                  'split':'train','example_id':str(index),'label_id':label},tokenizer))
    assert rows[0]['input_ids']!=rows[1]['input_ids']
    assert rows[0]['input_ids'][0]==tokenizer.cls_token_id
    assert rows[0]['input_ids'][-1]==tokenizer.sep_token_id
    broken_tokenizer=copy.deepcopy(tokenizer)
    broken_tokenizer.backend_tokenizer.post_processor=None
    with pytest.raises(ValueError,match='length/marker'): encode_record(rows[0],broken_tokenizer)
    with pytest.raises(ValueError,match='length/marker'): encode_record(rows[0],tokenizer,4)
    broken={**rows[0],'marked_text':'battery'}
    with pytest.raises(ValueError,match='Representation'): encode_record(broken,tokenizer)
    ds=AspectSentimentDataset(rows,'train')
    model=DebertaV2ForSequenceClassification(DebertaV2Config(vocab_size=len(tokenizer),hidden_size=12,
        num_hidden_layers=1,num_attention_heads=2,intermediate_size=16,num_labels=3,
        id2label={0:'negative',1:'neutral',2:'positive'},label2id={'negative':0,'neutral':1,'positive':2}))
    batch=collate_tokens([ds[0],ds[1]]); output=model(**batch)
    assert output.logits.shape==(2,3) and torch.isfinite(output.loss)
    output.loss.backward(); assert model.classifier.weight.grad is not None
    with torch.no_grad(): model.classifier.weight.zero_(); model.classifier.bias.copy_(torch.tensor([0.,0.,5.]))
    cfg=load_p9_config(PROJECT_ROOT/'configs/p9_exp01_deberta.yaml')
    save_asc_model(model,tmp_path/'deberta',cfg,PROJECT_ROOT/f'data/processed/{NAMESPACE}/tokenizer.json')
    classifier=AspectSentimentClassifier(tmp_path/'deberta',device='cpu')
    assert classifier.tokenizer(text)['input_ids']==tokenizer(text)['input_ids']
    prediction=classifier.classify_aspect_sentiment(text,'battery',17,24)
    assert prediction=={'aspect':'battery','sentiment':'positive','confidence':None}
    assert classifier.classify_many(text,[])==[]
