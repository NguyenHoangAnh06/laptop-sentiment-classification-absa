"""Smoke mô hình thật trên fixture tổng hợp; không phải kết quả review thực."""

import numpy as np
import pytest
import torch

from src.sentiment.modern import balanced_weights, make_tabm, tabm_predict


def test_xgboost_fit_predict_reload(tmp_path):
    from xgboost import XGBClassifier
    x = np.random.default_rng(42).normal(size=(24, 8)).astype('float32')
    y = np.tile(np.arange(3), 8)
    model = XGBClassifier(n_estimators=2, max_depth=2, n_jobs=1, random_state=42)
    model.fit(x, y, sample_weight=balanced_weights(y)[y])
    predicted = model.predict(x)
    model.save_model(tmp_path / 'model.ubj')
    loaded = XGBClassifier()
    loaded.load_model(tmp_path / 'model.ubj')
    assert np.array_equal(predicted, loaded.predict(x))
    assert set(predicted) <= {0, 1, 2}


def test_tabm_backward_reload(tmp_path):
    torch.manual_seed(42)
    torch.set_num_threads(1)
    cfg = {'n_blocks': 1, 'd_block': 16, 'k': 4, 'dropout': 0.1}
    model = make_tabm(8, cfg, 'cpu')
    x = np.random.default_rng(42).normal(size=(6, 8)).astype('float32')
    y = torch.tensor([0, 1, 2, 0, 1, 2])
    output = model(torch.tensor(x))
    loss = torch.nn.functional.cross_entropy(output.flatten(0, 1), y.repeat_interleave(4))
    loss.backward()
    assert any(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    before = tabm_predict(model, x, device='cpu')
    torch.save(model.state_dict(), tmp_path / 'model.pt')
    loaded = make_tabm(8, cfg, 'cpu')
    loaded.load_state_dict(torch.load(tmp_path / 'model.pt', weights_only=True))
    assert np.array_equal(before, tabm_predict(loaded, x, device='cpu'))


@pytest.mark.parametrize('locked', [False, True])
def test_retry_cannot_reopen_selected_test(tmp_path, monkeypatch, locked):
    """Chặn retry thí nghiệm PASS hoặc đã khóa, kể cả sau lỗi ghi kết quả."""
    import json
    import scripts.train_modern as runner
    (tmp_path / 'configs').mkdir()
    (tmp_path / 'configs/modern_tabular.yaml').write_text('{}', encoding='utf-8')
    (tmp_path / 'reports').mkdir()
    (tmp_path / 'reports/p4_semantic_independent_validation.json').write_text('{}', encoding='utf-8')
    report = tmp_path / 'reports/E03_tabpfn_v3_embedding'
    report.mkdir()
    original = json.dumps({'status': 'FAILED' if locked else 'PASS'})
    (report / 'result.json').write_text(original, encoding='utf-8')
    if locked:
        (report / 'selection_lock.json').write_text('{}', encoding='utf-8')
    monkeypatch.setattr(runner, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(runner, 'load_semantic_config', lambda: {'reports': 'reports', 'experiments': 'artifacts'})
    with pytest.raises(ValueError, match='Chỉ retry'):
        runner.run('E03_tabpfn_v3_embedding', attempt='retry01')
    assert (report / 'result.json').read_text(encoding='utf-8') == original
    assert not (report / 'attempts').exists()


def test_attempt_pointer_rejects_path_traversal(tmp_path):
    from scripts.train_modern import latest_report
    (tmp_path / 'latest_attempt.json').write_text('{"attempt":"../outside"}', encoding='utf-8')
    with pytest.raises(ValueError):
        latest_report(tmp_path)
