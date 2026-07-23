import streamlit as st
import streamlit.components.v1 as components

from card_render import _format_highlighted, _render_word_ipa_row
from config import PROJECT_ROOT, load_config
from deck_selector import select_deck

_COMPONENT_HEIGHT = 560

# Natural speaking pace baseline for the 1.0x speed setting: ~150 words per
# minute is a commonly cited average conversational rate.
_WORDS_PER_SECOND_BASELINE = 2.5

_STYLE = """
<style>
  * { box-sizing: border-box; }
  body { margin: 0; }
  .shadow-wrap {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 720px;
    margin: 0 auto;
  }
  .shadow-viewport {
    position: relative;
    height: 380px;
    overflow: hidden;
    border-radius: 16px;
    background: linear-gradient(135deg, #232526 0%, #414345 100%);
    color: #ffffff;
    padding: 0 28px;
    mask-image: linear-gradient(to bottom, transparent 0, black 48px, black calc(100% - 48px), transparent 100%);
    -webkit-mask-image: linear-gradient(to bottom, transparent 0, black 48px, black calc(100% - 48px), transparent 100%);
  }
  .shadow-content {
    position: absolute;
    top: 32px;
    left: 28px;
    right: 28px;
  }
  .shadow-line {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    column-gap: 16px;
    row-gap: 10px;
    padding: 18px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .shadow-line.shadow-plain {
    display: block;
    text-align: center;
    font-size: 1.3rem;
    line-height: 1.6;
  }
  .shadow-line .word-unit {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .shadow-line .word-unit-word {
    font-size: 1.3rem;
    font-weight: 500;
  }
  .shadow-line .word-unit-ipa {
    font-size: 0.8rem;
    opacity: 0.6;
  }
  .shadow-line .word-unit-word strong {
    font-weight: 700;
  }
  .shadow-controls {
    margin-top: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  .shadow-controls button {
    padding: 10px 22px;
    border-radius: 999px;
    border: none;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
  }
  #shadow-start-btn {
    background: #4facfe;
    color: white;
  }
  #shadow-reset-btn {
    background: #e9ecef;
    color: #333;
  }
  .shadow-speed-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    min-width: 220px;
  }
  .shadow-speed-wrap input[type="range"] {
    flex: 1;
  }
  #shadow-speed-label {
    font-weight: 600;
    min-width: 44px;
    text-align: right;
  }
</style>
"""

_SCRIPT_TEMPLATE = """
<script>
(function() {{
  const viewport = document.getElementById('shadow-viewport');
  const content = document.getElementById('shadow-content');
  const speedSlider = document.getElementById('shadow-speed');
  const speedLabel = document.getElementById('shadow-speed-label');
  const startBtn = document.getElementById('shadow-start-btn');
  const resetBtn = document.getElementById('shadow-reset-btn');

  const WORDS_PER_SECOND_BASELINE = {words_per_second};

  let position = 0;
  let rafId = null;
  let lastTimestamp = null;
  let playing = false;

  function totalWordUnits() {{
    return content.querySelectorAll('.word-unit').length
      || content.querySelectorAll('.shadow-line').length
      || 1;
  }}

  function maxPosition() {{
    return Math.max(0, content.scrollHeight - viewport.clientHeight);
  }}

  function pixelsPerSecond() {{
    const basePxPerWord = content.scrollHeight / totalWordUnits();
    return basePxPerWord * WORDS_PER_SECOND_BASELINE * parseFloat(speedSlider.value);
  }}

  function applyPosition() {{
    content.style.transform = 'translateY(-' + position + 'px)';
  }}

  function tick(timestamp) {{
    if (!playing) return;
    if (lastTimestamp === null) {{ lastTimestamp = timestamp; }}
    const dt = (timestamp - lastTimestamp) / 1000;
    lastTimestamp = timestamp;

    position += pixelsPerSecond() * dt;
    const max = maxPosition();
    if (position >= max) {{
      position = max;
      applyPosition();
      stopPlaying();
      return;
    }}
    applyPosition();
    rafId = requestAnimationFrame(tick);
  }}

  function startPlaying() {{
    if (position >= maxPosition() - 1) {{
      position = 0;
    }}
    playing = true;
    lastTimestamp = null;
    startBtn.textContent = 'Pause';
    rafId = requestAnimationFrame(tick);
  }}

  function stopPlaying() {{
    playing = false;
    if (rafId) {{ cancelAnimationFrame(rafId); }}
    rafId = null;
    startBtn.textContent = (position <= 0) ? 'Start' : 'Resume';
  }}

  startBtn.addEventListener('click', function() {{
    if (playing) {{ stopPlaying(); }} else {{ startPlaying(); }}
  }});

  resetBtn.addEventListener('click', function() {{
    stopPlaying();
    position = 0;
    applyPosition();
    startBtn.textContent = 'Start';
  }});

  // Reading the slider value fresh every animation frame (in
  // pixelsPerSecond above) means speed changes apply immediately on the
  // next frame — no restart of the animation is needed.
  speedSlider.addEventListener('input', function() {{
    speedLabel.textContent = parseFloat(speedSlider.value).toFixed(1) + 'x';
  }});

  applyPosition();
}})();
</script>
"""


def _build_shadowing_html(cards) -> str:
    lines = []
    for card in cards:
        if card.word_ipa_pairs:
            lines.append(f'<div class="shadow-line">{_render_word_ipa_row(tuple(card.word_ipa_pairs))}</div>')
        else:
            lines.append(f'<div class="shadow-line shadow-plain">{_format_highlighted(card.english_text)}</div>')
    return "".join(lines)


config = load_config()
decks_dir = PROJECT_ROOT / config.get("decks_dir", "decks")

st.title("Shadowing")
st.caption(
    "Read or speak along as the text scrolls upward at a steady pace, like a "
    "teleprompter — this technique is called shadowing."
)

deck, _ = select_deck(decks_dir, show_shuffle=False, key_prefix="shadowing")

if not deck.cards:
    st.info("This deck has no cards to shadow.")
    st.stop()

content_html = _build_shadowing_html(deck.cards)
script_html = _SCRIPT_TEMPLATE.format(words_per_second=_WORDS_PER_SECOND_BASELINE)

component_html = f"""
{_STYLE}
<div class="shadow-wrap">
  <div class="shadow-viewport" id="shadow-viewport">
    <div class="shadow-content" id="shadow-content">{content_html}</div>
  </div>
  <div class="shadow-controls">
    <button id="shadow-start-btn" type="button">Start</button>
    <button id="shadow-reset-btn" type="button">Reset</button>
    <div class="shadow-speed-wrap">
      <span>Speed</span>
      <input type="range" id="shadow-speed" min="0.5" max="2.0" step="0.1" value="1.0">
      <span id="shadow-speed-label">1.0x</span>
    </div>
  </div>
</div>
{script_html}
"""

components.html(component_html, height=_COMPONENT_HEIGHT, scrolling=False)