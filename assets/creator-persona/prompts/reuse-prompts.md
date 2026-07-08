# Future Street Philosopher Reuse Prompts

Use the original concept sheet and `docs/character-spec.md` as the first reference whenever the model can inspect images. If image inspection is unavailable, use the text prompt below.

## Base Identity Prompt

```text
Create the SAME original creator persona: an East Asian male-presenting intellectual in his late 30s to mid 40s, calm slightly tired eyes, slightly messy medium-short black hair, round thin glasses, oversized black workwear coat, loose black trousers, simple white inner shirt, deep oxblood/crimson scarf or inner lining. He feels like a future street philosopher: an ordinary social observer with a frontier-level technical brain, artistic but credible, quiet but sharp. Sophisticated Chinese editorial illustration, modern literary magazine style, painterly ink texture plus flat poster shapes, strong black silhouette, warm ivory/gray mood, restrained red accent.
```

## Transparent Pose Prompt

```text
Use case: background-extraction
Asset type: reusable transparent character cutout for WeChat article covers
Primary request: Create the SAME Future Street Philosopher character in this pose: <POSE>.

Subject identity: East Asian male-presenting intellectual, late 30s to mid 40s, calm tired eyes, slightly messy medium-short black hair, round thin glasses, oversized black workwear coat, loose black trousers, simple white inner shirt, deep oxblood/crimson scarf or inner lining, art-school texture, quiet but sharp social observer and frontier thinker.

Style/medium: sophisticated editorial illustration, modern Chinese literary magazine, painterly ink texture plus flat poster shapes.

Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for background removal. The background must be one uniform color with no shadows, gradients, texture, floor plane, reflections, or lighting variation.

Constraints: no text, no watermark, no logo, no phone, no laptop, no screen, no chart, no money, no topic-specific props. Do not use #00ff00 anywhere in the character. Keep the subject fully separated from the background with crisp edges. No cast shadow or contact shadow.
```

After generation, remove the green background with:

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input <source-keyed.png> \
  --out <transparent.png> \
  --auto-key border \
  --soft-matte \
  --transparent-threshold 12 \
  --opaque-threshold 220 \
  --despill
```

## Useful Future Poses

- Looking through a blank document.
- Half-turn with one hand in pocket.
- Crouched near an invisible object.
- Standing under abstract light.
- Back view walking away.
- Sitting on a low block with one knee raised.
- Side profile adjusting glasses.
- Holding a blank folder.
