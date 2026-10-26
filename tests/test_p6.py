"""BERT ngẫu nhiên nhỏ và đồ đạc token tổng hợp; không bao giờ đưa ra bằng chứng đánh giá so sánh."""

import json
import shutil

import numpy as np
import pandas as pd
import pytest
import torch
import yaml
from torch.utils.data import DataLoader
from transformers import BertConfig, BertForSequenceClassification
from tokenizers import Tokenizer, models, normalizers, pre_tokenizers, processors

from scripts.train_p5 import write_json
from scripts.train_p6 import run, save_checkpoint
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.models.registry import load_sentiment, UnsupportedLanguageError
from src.preprocessing.bert import BertPreprocessor
from src.sentiment.bert import (FEATURES, LABEL_TO_ID, BertArtifact, LengthBatchSampler,
    P4BertDataset, class_weights, collate_tokens, evaluate, improved, resolve_device,
    seed_everything, training_loss)


def records(split='train'):
    return [dict(review_id=f'{split}{i}', split=split, label_id=i % 3,
                 input_ids=[101] + [10 + i] * (i + 1) + [102],
                 attention_mask=[1] * (i + 3), token_type_ids=[0] * (i + 3), rating=5)
            for i in range(9)]


def tiny_model(vocab_size=128):
    return BertForSequenceClassification(BertConfig(vocab_size=vocab_size, hidden_size=16,
        num_hidden_layers=1, num_attention_heads=2, intermediate_size=32, num_labels=3,
        label2id=LABEL_TO_ID, id2label=dict(enumerate(LABEL_TO_ID))))


@pytest.fixture
def tokenizer_path(tmp_path):
    vocabulary = {f'unused{i}': i for i in range(128)}
    for index, token in {0: '[PAD]', 100: '[UNK]', 101: '[CLS]', 102: '[SEP]', 103: '[MASK]',
                         104: 'not', 105: 'good', 106: 'bad', 107: 'broken', 108: 'average',
                         109: 'fine', 110: 'excellent', 111: 'love', 112: 'works', 113: 'well'}.items():
        del vocabulary[f'unused{index}']
        vocabulary[token] = index
    tokenizer = Tokenizer(models.WordPiece(vocab=vocabulary, unk_token='[UNK]'))
    tokenizer.normalizer = normalizers.BertNormalizer(lowercase=True)
    tokenizer.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
    tokenizer.post_processor = processors.TemplateProcessing(single='[CLS] $A [SEP]',
        special_tokens=[('[CLS]', 101), ('[SEP]', 102)])
    path = tmp_path / 'fixture_tokenizer.json'
    tokenizer.save(str(path))
    return path


def test_adapter_collator_shapes_fields_and_padding():
    dataset = P4BertDataset(records(), split='train', max_length=32, vocab_size=128)
    assert dataset.review_ids == [f'train{i}' for i in range(9)]
    batch = collate_tokens([dataset[0], dataset[3]])
    assert set(batch) == set(FEATURES) | {'labels'}
    assert batch['input_ids'].shape == (2, 6)
    assert all(v.dtype == torch.long for v in batch.values())
    assert batch['attention_mask'][0].tolist() == [1, 1, 1, 0, 0, 0]
    assert batch['input_ids'][0, 3:].tolist() == [0, 0, 0]
    dataset[0]['input_ids'].append(20)
    assert len(dataset[0]['input_ids']) == 3


@pytest.mark.parametrize('field,value', [('split', 'test'), ('label_id', 3), ('input_ids', [101, 128, 102]),
    ('attention_mask', [0, 0, 0]), ('token_type_ids', [1, 1, 1]), ('input_ids', [100, 10, 102])])
def test_adapter_rejects_corrupt_tokens_labels_or_split(field, value):
    rows = records()
    rows[0][field] = value
    with pytest.raises(ValueError):
        P4BertDataset(rows, split='train', max_length=32, vocab_size=128)


def test_train_only_balanced_weights_and_sampler_conservation():
    rows = records() + [{**row, 'review_id': f'extra{i}'} for i, row in enumerate(records()[::3])]
    train = P4BertDataset(rows, split='train', max_length=32, vocab_size=128)
    weights = class_weights(train, 'balanced').numpy()
    np.testing.assert_allclose(weights, [2/3, 4/3, 4/3])
    assert class_weights(train, 'unweighted') is None
    sampler = LengthBatchSampler(train, 2, 42)
    order = list(sampler)
    assert sorted(i for batch in order for i in batch) == list(range(len(train)))
    assert order == list(sampler)
    sampler.epoch = 1
    assert order != list(sampler)
    heldout = P4BertDataset(records('test'), split='test', max_length=32, vocab_size=128)
    with pytest.raises(ValueError): class_weights(heldout, 'balanced')
    with pytest.raises(ValueError): LengthBatchSampler(heldout, 2, 42)


def test_forward_backprop_evaluation_and_selection():
    torch.set_num_threads(1)
    seed_everything(42)
    dataset = P4BertDataset(records(), split='train', max_length=32, vocab_size=128)
    model = tiny_model()
    batch = collate_tokens([dataset[0], dataset[1], dataset[2]])
    labels = batch.pop('labels')
    output = model(**batch).logits
    assert output.shape == (3, 3)
    loss = training_loss(output, labels, torch.tensor([2., 1., .5]))
    assert torch.isfinite(loss)
    loss.backward()
    assert model.bert.embeddings.word_embeddings.weight.grad.abs().sum() > 0
    loader = DataLoader(dataset, batch_size=3, collate_fn=collate_tokens)
    one, pred, truth = evaluate(model, loader, torch.device('cpu'))
    two, again, _ = evaluate(model, loader, torch.device('cpu'))
    assert one == two and np.array_equal(pred, again)
    assert len(truth) == 9 and one['confusion_matrix_order'] == list(LABEL_TO_ID)
    assert improved({'macro_f1': .6}, {'macro_f1': .5})
    assert not improved({'macro_f1': .6}, {'macro_f1': .6})


def test_device_fallback_and_language_registry(monkeypatch):
    monkeypatch.setattr(torch.cuda, 'is_available', lambda: False)
    assert resolve_device('auto').type == 'cpu'
    with pytest.raises(ValueError): resolve_device('cuda')
    with pytest.raises(UnsupportedLanguageError): load_sentiment('unused', family='bert', language='vi')


def test_checkpoint_roundtrip_text_inference_and_tamper(tmp_path, tokenizer_path):
    model = tiny_model().eval()
    directory = tmp_path / 'best'
    save_checkpoint(model, directory, tokenizer_path, {'max_length': 512})
    artifact = BertArtifact(directory, 'cpu')
    frame = pd.DataFrame({'text': ['NOT good!', 'Works well.'], 'language': ['en', 'en'], 'rating': [5, 1]})
    predictions = artifact.predict(frame, 1)
    assert len(predictions) == 2 and predictions == artifact.predict(frame, 2)
    assert predictions[0]['confidence'] is None and predictions[0]['aspects'] == []
    pre = BertPreprocessor(tokenizer_path, 512)
    token_batch = collate_tokens(pre.encode(frame))
    with torch.inference_mode():
        np.testing.assert_array_equal(artifact.predict_ids(frame), model(**token_batch).logits.argmax(-1).numpy())
    with pytest.raises(ValueError): artifact.predict(pd.DataFrame({'text': ['']}))
    with pytest.raises(ValueError): artifact.predict(pd.DataFrame({'text': ['test'], 'language': ['vi']}))
    with (directory / 'model.safetensors').open('ab') as handle: handle.write(b'changed')
    with pytest.raises(ValueError, match='Changed'): BertArtifact(directory, 'cpu')


def test_full_tiny_training_locks_before_test_and_preserves_inputs(tmp_path, monkeypatch, tokenizer_path):
    """Hai thiết bị mô hình nhỏ thực tế lượt khớp mô hình, tất cả các mẫu; không tải xuống đã huấn luyện trước."""
    import scripts.train_p6 as runner
    root = tmp_path
    for path in ('configs', 'reports/p4', 'reports/p5/fixturep5', 'artifacts/pre/bert', 'data/splits',
                 'data/features', 'artifacts/models/fixturep5', 'source'):
        (root / path).mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((PROJECT_ROOT / 'configs/p6.yaml').read_text())
    cfg.update(output_suffix='fixturep6', p4_manifest='reports/p4/manifest.json',
               p5_manifest='reports/p5/fixturep5/manifest.json', device='cpu', mixed_precision='none',
               gradient_checkpointing=False, epochs=2, batch_size=2, eval_batch_size=3,
               gradient_accumulation=2, latency_batch_size=3, latency_repeats=1, threads=1)
    (root / 'configs/p6.yaml').write_text(yaml.safe_dump(cfg), encoding='utf-8')
    original_tokenizer = tokenizer_path
    shutil.copyfile(original_tokenizer, root / 'artifacts/pre/bert/tokenizer.json')
    model = tiny_model()
    model.config.save_pretrained(root / 'artifacts/pre/bert')
    model.save_pretrained(root / 'source', safe_serialization=True)
    write_json(root / 'artifacts/pre/preprocessing.json', {'bert': {'max_length_policy': {'max_length': 512},
               'repo': cfg['checkpoint'], 'revision': cfg['revision']}})
    pre = BertPreprocessor(original_tokenizer, 512)
    frames = {}
    for split in ('train', 'validation', 'test'):
        frames[split] = pd.DataFrame([dict(review_id=f'{split}{i}', label_id=i%3, split=split,
            parent_asin=f'{split}p{i}', asin=f'{split}a{i}', split_group_id=f'{split}g{i}',
            text=f'{split} unique{i} ' + ['bad broken', 'average fine', 'excellent love'][i%3],
            language='en', sentiment=list(LABEL_TO_ID)[i%3], label_provenance='rating-derived proxy',
            clean_text_sha256=f'{split}h{i}', rating=[1, 3, 5][i%3]) for i in range(6)])
        frame = frames[split]
        frame.to_parquet(root / f'data/splits/{split}.parquet', index=False)
        rows = [{**tok, 'review_id': row.review_id, 'label_id': row.label_id, 'split': split}
                for tok, row in zip(pre.encode(frame), frame.itertuples())]
        pd.DataFrame(rows).to_parquet(root / f'data/features/{split}_bert.parquet', index=False)
    source_file = root / 'data/source.parquet'
    pd.concat(frames.values()).to_parquet(source_file)
    write_json(root / 'reports/p4/input_preservation.json', {})
    write_json(root / cfg['p4_manifest'], {'output_sha256': {}, 'implementation_sha256': {},
        'source': 'data/source.parquet', 'source_sha256': sha256_file(source_file),
        'paths': {'preprocessing': 'artifacts/pre', 'splits': 'data/splits', 'features': 'data/features', 'report': 'reports/p4'}})
    write_json(root / cfg['p5_manifest'], {'status': 'DONE', 'input_sha256': {}, 'output_sha256': {}, 'implementation_sha256': {}})
    pd.DataFrame([{'model': 'logistic_regression', 'selected_by_validation': True,
                   'validation_macro_f1': .2, 'macro_f1': .2}]).to_csv(root / 'reports/p5/fixturep5/benchmark.csv', index=False)
    pd.DataFrame({'review_id': frames['test'].review_id, 'label_id': frames['test'].label_id,
                  'logistic_regression': [2]*6}).to_parquet(root / 'artifacts/models/fixturep5/test_predictions.parquet', index=False)
    for path in ('scripts/train_p6.py', 'src/sentiment/bert.py', 'src/models/registry.py', 'requirements.txt'):
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / path, destination)
    monkeypatch.setattr(runner, 'hf_hub_download', lambda *a, **k: root / 'source/model.safetensors')
    real_evaluate, test_calls = runner.evaluate, []
    def guarded_evaluate(model, loader, device, **kwargs):
        if loader.dataset.split == 'test':
            assert (root / 'reports/p6/fixturep6/selection_lock.json').exists()
            test_calls.append(True)
        return real_evaluate(model, loader, device, **kwargs)
    monkeypatch.setattr(runner, 'evaluate', guarded_evaluate)
    result = run(root / 'configs/p6.yaml', root)
    assert result['status'] == 'DONE' and test_calls == [True]
    history = json.loads((root / 'reports/p6/fixturep6/training_history.json').read_text())
    assert {r['mode'] for r in history} == {'unweighted', 'balanced'}
    assert all(r['train_rows'] == 6 for r in history)
    assert all(r['optimizer_updates'] == 2 for r in history)  # bao gồm nhóm một vi hạt cuối cùng
    from scripts.validate_p6 import validate
    audit = validate(root / 'reports/p6/fixturep6', root)
    assert audit['status'] == 'PASS' and audit['test_predictions_rerun'] is False
    with pytest.raises(FileExistsError): run(root / 'configs/p6.yaml', root)
