# LLM Anatomy Roadmap

This file is a personal learning map for reading this repository as an anatomy laboratory for large language models.

## Goal

Understand a ChatGPT-like language model from the inside, step by step, without treating it as a black box.

## Reading path

1. Tokenization
   - How raw text becomes token IDs.
   - What information is preserved, compressed, or lost.

2. Embeddings
   - How token IDs become vectors.
   - Why a token must enter a geometric space before the model can operate on it.

3. Positional information
   - How the model receives order.
   - Why sequence position matters for language.

4. Self-attention
   - How tokens look at previous tokens.
   - How query, key, and value projections create relational structure.

5. Multi-head attention
   - Why several attention heads can track different relations at the same time.

6. Feed-forward network
   - How each token representation is transformed internally.

7. Residual connections and layer normalization
   - How information remains stable across many layers.

8. Transformer block
   - How attention, feed-forward layers, residual paths, and normalization form the basic organ of the model.

9. GPT model
   - How many Transformer blocks compose a full language model.

10. Loss and training
    - How next-token prediction becomes a mathematical pressure on the weights.

11. Generation
    - How logits become probabilities and how the model samples the next token.

## Personal method

For each chapter or script, create a small anatomical note:

- What enters?
- What shape does it have?
- What transformation happens?
- What exits?
- Which weights are involved?
- What would break if this part were removed?

## First local command after cloning

```bash
git pull origin main
```

Then start reading from the earliest chapters and keep notes in small files or notebooks.
