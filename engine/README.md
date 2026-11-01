# Islamic Reels engine

Tested Python modules used by the `islamic-reels-doc-style` skill. Copy them into a working folder:

```bash
cp ~/media-files/engine/*.py .                       # modules
cp ~/media-files/engine/templates/{script,reel,sound}.py .   # narrated reel template
```

| File | What it is |
|---|---|
| `ir_doc.py` | House documentary engine: palette, fonts, paper props, highlight/marker/stamp, whip and flash transitions, renderer |
| `ir_motion.py` | NullMotion moves (GSAP eases, mask rise, blur reveal, card stacks, morph, hub, bars, timeline, list, chat, end card, LIFT/ZOOM/PUSH_UP) |
| `ir_viral.py` | Moves from the reference reels: lead + big keyword, karaoke fill, bar word, icon-in-word, letter build, swell, arc sweep, marker loop, ghost word, ribbon, light sweep, floating icons, glow, tilted plane, purple hill, chess stage with pawn-to-king, dark outro |
| `ir_urdu.py` | Narration timeline cues (ON/OFF/WT), Nastaliq text, synced captions, illustrated plate + camera, quote cards, reel runner and CLI |
| `narrate.py` | Urdu voice (Kokoro, Devanagari input) chunk by chunk with measured timing -> timeline.json |
| `align.py` | Word times snapped to energy dips |
| `asr_check.py` | Whisper (Urdu) read-back of every clip; `try` mode for pronunciation variants |
| `ir_audio.py` | Synthesised sound design on cue times + final mix with the user's track |
| `templates/` | Narrated template (script, reel, sound) and the quick-card templates |

No people are drawn. Accuracy rules live in the skill.
