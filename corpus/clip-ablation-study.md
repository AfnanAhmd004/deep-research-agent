# clip-ablation-study

A **CLIP-style vision–language model** trained from scratch with a symmetric contrastive (InfoNCE) loss, used as a testbed for **model ablations** and **data ablations**. Evaluation is attribute-level zero-shot classification and **compositional generalisation** to colour–shape pairs never seen in training.

## Why a procedural dataset

Images are coloured shapes (4 colours × 3 shapes × 4 positions) with jitter, varying size and noise. Every image's true attributes are known, so the evaluation can say exactly *what* the model learned (colour vs shape vs spatial position), rather than reporting one aggregate score. Two colour–shape pairs (`green triangle`, `blue circle`) are **excluded from training** to test whether the model composes concepts it learned separately.

## Model

- **Image tower**: 3-layer CNN. **Text tower**: 2-layer Transformer with mean pooling over non-padding tokens.
- L2-normalised embeddings in a shared space, a learnable logit scale (temperature) clipped at 100, and a symmetric cross-entropy over the in-batch similarity matrix.

## Results

```bash
pip install -e ".[dev]"
python examples/run_ablations.py     # ~8 min on CPU
pytest
```

Each row changes one factor from the baseline. Columns: zero-shot accuracy per attribute, **joint** accuracy (the correct caption out of all 48), and **compositional** accuracy on held-out colour–shape pairs.

```
config                              colour   shape     pos  joint  compositional
baseline (learned τ, d=64)            100%    100%    100%   100%            59%
fixed τ = 1.0                         100%     44%    100%    44%            60%
fixed τ = 0.07                        100%    100%    100%   100%            55%
embedding d=8                         100%    100%    100%   100%            76%
data: 25% of samples                  100%    100%    100%   100%            50%
data: captions w/o position            96%     91%     22%    18%            87%
data: 30% wrong colours                92%    100%    100%    92%            55%
aug: h-flip, captions unchanged       100%    100%     80%    80%            62%
```

### Findings

1. **Temperature matters most among the model choices.** A fixed τ=1.0 produces logits too flat to separate shapes, and shape accuracy collapses to 44%. A learned τ matches the hand-tuned 0.07.
2. **Captions define what is learnable.** Without position words, position accuracy drops to chance (22%), and the model *does* compose colour and shape better (87%): capacity shifts to what the text supervises.
3. **Label noise passes straight through.** 30% wrong colours in captions cost about 8 points of colour accuracy.
4. **Augmentations must respect the text.** Horizontal flipping without swapping "left"/"right" in captions teaches contradictory labels and cuts position accuracy to 80%.
5. **Compositional generalisation is the hard part.** All configurations score 100% on seen combinations but 50–87% on unseen ones. A smaller embedding (d=8) generalised better here, a hint that bottlenecks encourage factorised representations.

Each number comes from a single seed on a small synthetic task. Treat differences of a few points as noise, and use multiple seeds before drawing conclusions on real data.

## License

MIT
