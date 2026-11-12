# Forged: the house animation style (dark-lime theme)

Default look for every Islamic Reel from Nov 2026. A cinematic night world drawn in code (parallax ridges, sky moods,
the pass and the wall, fire, copper, swarm dots, lake, at-Tur, balance, birds, rain, sprouts, pomegranate, globe),
"forged" text (a lime molten edge sweeps through the letters and they cool to white; Arabic sweeps right to left),
ember-burn transitions, word-by-word Urdu captions at the bottom, the full-lime dua scene with dark ink, dark outro.

Colours: near-black #0B090A with olive glow + halftone dots, LIME #CEF41E accent, white text, CORAL #F05844 for negatives.
Fonts: Cinzel + Cormorant Garamond (npm @fontsource/cinzel, @fontsource/cormorant-garamond into ~/fonts), Amiri, Noto Nastaliq Urdu.

Use:
```bash
cp ~/media-files/engine/*.py . && cp ~/media-files/engine/forged/forged_*.py .
# write scenes.py (see example_scenes_yajuj_majuj.py: base(), wall_world(), forge(), ar_word(), gloss(), label(), fin())
cat forged_look.py forged_world.py scenes.py > reel.py
python3 reel.py info | preview t1 t2 ... | range a b part.mp4
```
Canvas drawing must stay RGB (blending put/paste); never ImageDraw on an RGBA canvas with partial alpha.
