"""
Small anatomy tests for ch04/01_main-chapter-code/gpt.py.

These tests are intentionally lightweight. They do not train the model.
They only verify that the core GPT anatomy works:

- token IDs enter as [batch, tokens]
- logits exit as [batch, tokens, vocab_size]
- simple autoregressive generation appends tokens
- the causal attention module preserves [batch, tokens, emb_dim]

Run locally from the repository root with: super bien

    python -m pytest tests/test_ch04_gpt_anatomy.py.
"""

from pathlib import Path
import importlib.util

import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
GPT_FILE = REPO_ROOT / "ch04" / "01_main-chapter-code" / "gpt.py"


def load_gpt_module():
    spec = importlib.util.spec_from_file_location("ch04_gpt", GPT_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tiny_gpt_config():
    return {
        "vocab_size": 32,
        "context_length": 8,
        "emb_dim": 16,
        "n_heads": 4,
        "n_layers": 2,
        "drop_rate": 0.0,
        "qkv_bias": False,
    }


def test_gpt_model_forward_logits_shape():
    gpt = load_gpt_module()
    torch.manual_seed(123)

    cfg = tiny_gpt_config()
    model = gpt.GPTModel(cfg)
    model.eval()

    input_ids = torch.randint(0, cfg["vocab_size"], (2, 5))
    logits = model(input_ids)

    assert logits.shape == (2, 5, cfg["vocab_size"])
    assert torch.isfinite(logits).all()


def test_generate_text_simple_appends_tokens():
    gpt = load_gpt_module()
    torch.manual_seed(123)

    cfg = tiny_gpt_config()
    model = gpt.GPTModel(cfg)
    model.eval()

    start_ids = torch.tensor([[1, 2, 3]])
    out = gpt.generate_text_simple(
        model=model,
        idx=start_ids,
        max_new_tokens=4,
        context_size=cfg["context_length"],
    )

    assert out.shape == (1, 7)
    assert torch.equal(out[:, :3], start_ids)
    assert out.max().item() < cfg["vocab_size"]
    assert out.min().item() >= 0


def test_multi_head_attention_preserves_shape():
    gpt = load_gpt_module()
    torch.manual_seed(123)

    att = gpt.MultiHeadAttention(
        d_in=16,
        d_out=16,
        context_length=8,
        dropout=0.0,
        num_heads=4,
        qkv_bias=False,
    )
    att.eval()

    x = torch.randn(2, 5, 16)
    y = att(x)

    assert y.shape == x.shape
    assert torch.isfinite(y).all()
