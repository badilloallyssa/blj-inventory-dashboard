/**
 * generate_layout.js
 * Renders a BLJ-style infographic to a 300 DPI PNG.
 * Usage: node tools/generate_layout.js
 * Output: .tmp/pause_and_pivot_layout.png
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const OUTPUT = path.join(__dirname, '../.tmp/pause_and_pivot_layout.png');

// ─────────────────────────────────────────────────────────────────────────────
// ILLUSTRATION SVG (inline, center of loop)
// ─────────────────────────────────────────────────────────────────────────────
const illustrationSVG = `
<svg width="280" height="560" viewBox="0 0 280 560" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="grainy" x="-10%" y="-10%" width="120%" height="120%">
      <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" result="noise" seed="2"/>
      <feColorMatrix type="saturate" values="0" in="noise" result="grayNoise"/>
      <feBlend in="SourceGraphic" in2="grayNoise" mode="multiply" result="blend"/>
      <feComposite in="blend" in2="SourceGraphic" operator="in"/>
    </filter>
    <radialGradient id="bgWash" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#C5E8E8" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#E8F5F5" stop-opacity="0.1"/>
    </radialGradient>
  </defs>

  <!-- Background watercolor wash -->
  <ellipse cx="140" cy="280" rx="125" ry="260" fill="url(#bgWash)"/>
  <ellipse cx="140" cy="280" rx="125" ry="260" fill="url(#bgWash)" filter="url(#grainy)" opacity="0.4"/>

  <!-- ── CHILD (left, Black boy, defiant crossed arms) ── -->
  <!-- Ground shadow -->
  <ellipse cx="80" cy="500" rx="32" ry="6" fill="#7BBFBF" opacity="0.18"/>

  <!-- Legs -->
  <path d="M72,410 L65,495" stroke="#5B7FA6" stroke-width="14" stroke-linecap="round" fill="none"/>
  <path d="M88,410 L95,495" stroke="#5B7FA6" stroke-width="14" stroke-linecap="round" fill="none"/>
  <!-- Shoes -->
  <ellipse cx="62" cy="496" rx="15" ry="7" fill="#2A1A0A" opacity="0.9"/>
  <ellipse cx="98" cy="496" rx="15" ry="7" fill="#2A1A0A" opacity="0.9"/>

  <!-- Torso (teal shirt) -->
  <rect x="60" y="330" width="40" height="85" rx="10" fill="#5CB8B2"/>
  <rect x="60" y="330" width="40" height="85" rx="10" fill="#5CB8B2" filter="url(#grainy)" opacity="0.5"/>
  <!-- Shirt outline -->
  <rect x="60" y="330" width="40" height="85" rx="10" fill="none" stroke="#3A9490" stroke-width="1.5"/>

  <!-- Crossed arms -->
  <!-- Left arm -->
  <path d="M60,355 Q45,368 50,385 Q56,392 72,385" stroke="#8B5C3A" stroke-width="9" stroke-linecap="round" fill="none"/>
  <!-- Right arm crossing over -->
  <path d="M100,355 Q115,365 108,382 Q100,390 80,382" stroke="#8B5C3A" stroke-width="9" stroke-linecap="round" fill="none"/>

  <!-- Neck -->
  <rect x="73" y="315" width="14" height="18" rx="5" fill="#8B5C3A"/>

  <!-- Head -->
  <circle cx="80" cy="295" r="30" fill="#8B5C3A"/>
  <circle cx="80" cy="295" r="30" fill="#8B5C3A" filter="url(#grainy)" opacity="0.3"/>

  <!-- Natural hair (afro) -->
  <circle cx="80" cy="272" r="26" fill="#2A1008"/>
  <circle cx="60" cy="280" r="14" fill="#2A1008"/>
  <circle cx="100" cy="280" r="14" fill="#2A1008"/>
  <circle cx="74" cy="268" r="10" fill="#2A1008"/>
  <circle cx="86" cy="268" r="10" fill="#2A1008"/>

  <!-- Eyes (frowning/defiant) -->
  <circle cx="72" cy="296" r="3.5" fill="#1A0A00"/>
  <circle cx="88" cy="296" r="3.5" fill="#1A0A00"/>
  <!-- Eyebrow furrowed -->
  <path d="M68,288 Q72,285 76,287" stroke="#1A0A00" stroke-width="2" stroke-linecap="round" fill="none"/>
  <path d="M84,287 Q88,285 92,288" stroke="#1A0A00" stroke-width="2" stroke-linecap="round" fill="none"/>
  <!-- Frown -->
  <path d="M73,310 Q80,306 87,310" stroke="#1A0A00" stroke-width="2" stroke-linecap="round" fill="none"/>


  <!-- ── PARENT (right, light-skinned woman, calm open hands) ── -->
  <!-- Ground shadow -->
  <ellipse cx="200" cy="500" rx="32" ry="6" fill="#7BBFBF" opacity="0.18"/>

  <!-- Legs -->
  <path d="M190,405 L183,495" stroke="#9A7AC0" stroke-width="16" stroke-linecap="round" fill="none"/>
  <path d="M210,405 L217,495" stroke="#9A7AC0" stroke-width="16" stroke-linecap="round" fill="none"/>
  <!-- Shoes -->
  <ellipse cx="180" cy="496" rx="16" ry="7" fill="#4A3020" opacity="0.85"/>
  <ellipse cx="220" cy="496" rx="16" ry="7" fill="#4A3020" opacity="0.85"/>

  <!-- Torso (rose/salmon top) -->
  <rect x="176" y="310" width="48" height="100" rx="12" fill="#E8A0A0"/>
  <rect x="176" y="310" width="48" height="100" rx="12" fill="#E8A0A0" filter="url(#grainy)" opacity="0.4"/>
  <rect x="176" y="310" width="48" height="100" rx="12" fill="none" stroke="#C07070" stroke-width="1.5"/>

  <!-- Left arm — extended open, palm up (stepping back) -->
  <path d="M176,340 Q148,350 136,370 Q134,380 138,385" stroke="#FDDBB4" stroke-width="11" stroke-linecap="round" fill="none"/>
  <!-- Palm/hand -->
  <ellipse cx="136" cy="386" rx="9" ry="7" fill="#FDDBB4" stroke="#D4A870" stroke-width="1"/>

  <!-- Right arm — slightly back/to side -->
  <path d="M224,340 Q244,352 250,370" stroke="#FDDBB4" stroke-width="11" stroke-linecap="round" fill="none"/>
  <ellipse cx="252" cy="372" rx="8" ry="7" fill="#FDDBB4" stroke="#D4A870" stroke-width="1"/>

  <!-- Neck -->
  <rect x="193" y="296" width="14" height="16" rx="5" fill="#FDDBB4"/>

  <!-- Head -->
  <circle cx="200" cy="270" r="34" fill="#FDDBB4"/>
  <circle cx="200" cy="270" r="34" fill="#FDDBB4" filter="url(#grainy)" opacity="0.25"/>

  <!-- Hair (warm brown, bun) -->
  <path d="M170,260 Q175,228 200,222 Q225,228 230,260 Q220,218 200,215 Q180,218 170,260" fill="#7B4F2A"/>
  <circle cx="200" cy="222" r="14" fill="#7B4F2A"/>
  <!-- Bun highlight -->
  <circle cx="196" cy="218" r="5" fill="#9B6F4A" opacity="0.5"/>

  <!-- Eyes (gentle, warm) -->
  <ellipse cx="191" cy="270" rx="4" ry="4.5" fill="#3A2010"/>
  <ellipse cx="209" cy="270" rx="4" ry="4.5" fill="#3A2010"/>
  <!-- Eye sparkle -->
  <circle cx="193" cy="268" r="1.5" fill="white"/>
  <circle cx="211" cy="268" r="1.5" fill="white"/>
  <!-- Eyebrow (relaxed) -->
  <path d="M184,260 Q191,256 198,259" stroke="#5A3010" stroke-width="2" stroke-linecap="round" fill="none"/>
  <path d="M202,259 Q209,256 216,260" stroke="#5A3010" stroke-width="2" stroke-linecap="round" fill="none"/>
  <!-- Calm smile -->
  <path d="M191,284 Q200,291 209,284" stroke="#3A2010" stroke-width="2" stroke-linecap="round" fill="none"/>


  <!-- ── DROPPED ROPE between them ── -->
  <!-- Main rope -->
  <path d="M100,370 Q120,430 140,440 Q160,450 170,388"
    fill="none"
    stroke="#B07830"
    stroke-width="5.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    opacity="0.85"/>
  <!-- Rope braid texture overlay -->
  <path d="M100,370 Q120,430 140,440 Q160,450 170,388"
    fill="none"
    stroke="#D4A840"
    stroke-width="2.5"
    stroke-dasharray="7 6"
    stroke-linecap="round"
    opacity="0.6"/>
  <!-- Rope ends (loose) -->
  <circle cx="100" cy="370" r="5" fill="#B07830" opacity="0.7"/>
  <circle cx="170" cy="388" r="5" fill="#B07830" opacity="0.7"/>


  <!-- ── GROUND LINE ── -->
  <line x1="30" y1="502" x2="250" y2="502" stroke="#B8DEDE" stroke-width="1.5" stroke-dasharray="6 4" opacity="0.5"/>


  <!-- ── LABELS ── -->
  <text x="140" y="535" text-anchor="middle"
    font-family="Nunito, sans-serif" font-size="13" font-weight="900"
    fill="#2A7A76" letter-spacing="1.5">PAUSE &amp; PIVOT</text>
  <text x="140" y="551" text-anchor="middle"
    font-family="Nunito, sans-serif" font-size="9" font-weight="600"
    fill="#7BBFBF" letter-spacing="0.5">Drop the rope. Change the game.</text>

</svg>`;

// ─────────────────────────────────────────────────────────────────────────────
// FULL PAGE HTML
// ─────────────────────────────────────────────────────────────────────────────
const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,400;0,600;0,700;0,800;0,900;1,400;1,700&display=swap" rel="stylesheet">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    width: 816px;
    height: 1056px;
    background: #FFFFFF;
    font-family: 'Nunito', sans-serif;
    overflow: hidden;
  }

  .page {
    width: 816px;
    height: 1056px;
    padding: 28px 38px 22px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    position: relative;
    background: #fff;
  }

  /* ── Decorative corner circles ── */
  .deco {
    position: absolute;
    border-radius: 50%;
    background: #C5E8E8;
    opacity: 0.30;
    pointer-events: none;
  }
  .deco-tl  { width: 90px;  height: 90px;  top: -25px;   left: -25px; }
  .deco-tr  { width: 50px;  height: 50px;  top: 60px;    right: -12px; }
  .deco-br  { width: 70px;  height: 70px;  bottom: -18px; right: -18px; }
  .deco-bl  { width: 38px;  height: 38px;  bottom: 60px;  left: -10px; }

  /* ── TITLE ── */
  .title-area {
    text-align: center;
    padding: 0 10px;
    flex-shrink: 0;
  }

  .main-title {
    font-size: 24.5px;
    font-weight: 900;
    color: #2A7A76;
    line-height: 1.22;
    margin-bottom: 7px;
  }

  .main-title .italic-part {
    font-style: italic;
    color: #1D5D5A;
  }

  .subtitle {
    font-size: 10.5px;
    color: #444;
    line-height: 1.62;
    font-weight: 600;
    max-width: 640px;
    margin: 0 auto;
  }

  /* ── SECTION BARS ── */
  .section-bar {
    background: #2A7A76;
    color: #fff;
    text-align: center;
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 7px 20px;
    border-radius: 4px;
    flex-shrink: 0;
  }

  /* ── DOTTED BOX ── */
  .dotted-box {
    border: 2.5px dashed #7BBFBF;
    border-radius: 14px;
    padding: 10px 18px 12px;
    background: #FBFFFE;
    flex-shrink: 0;
  }

  .dotted-header {
    text-align: center;
    font-size: 10.5px;
    font-weight: 900;
    color: #2A7A76;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .bullet-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3px 24px;
  }

  .bullet-item {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 10px;
    color: #333;
    line-height: 1.45;
  }

  .bullet-icon {
    color: #2A7A76;
    font-weight: 900;
    font-size: 12px;
    flex-shrink: 0;
  }

  /* ── LOOP AREA ── */
  .loop-area {
    flex: 1;
    position: relative;
    min-height: 0;
  }

  .loop-bg-svg {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 1;
  }

  .loop-grid {
    position: absolute;
    inset: 0;
    z-index: 2;
    display: grid;
    grid-template-columns: 208px 1fr 208px;
    grid-template-rows: 1fr 1fr;
    gap: 10px;
  }

  /* ── STEP CARDS ── */
  .step-card {
    border: 2.5px dashed #7BBFBF;
    border-radius: 12px;
    padding: 10px 12px;
    background: #F2FAFA;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .step-card-header {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 5px;
    flex-shrink: 0;
  }

  .step-badge {
    background: #2A7A76;
    color: #fff;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    font-size: 14px;
    font-weight: 900;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .step-title {
    font-size: 11px;
    font-weight: 900;
    color: #2A7A76;
    line-height: 1.2;
  }

  .step-rule {
    height: 1.5px;
    background: linear-gradient(to right, #7BBFBF, transparent);
    margin-bottom: 6px;
    border-radius: 2px;
    flex-shrink: 0;
  }

  .step-body {
    font-size: 9.5px;
    color: #333;
    line-height: 1.52;
    flex: 1;
  }

  .step-example {
    background: #FFF8DC;
    border-left: 3px solid #E8C840;
    border-radius: 0 6px 6px 0;
    padding: 4px 8px;
    font-size: 9px;
    color: #444;
    font-style: italic;
    line-height: 1.45;
    margin-top: 6px;
    flex-shrink: 0;
  }

  .step-example strong {
    font-style: normal;
    color: #222;
    font-weight: 800;
  }

  /* ── CENTER ILLUSTRATION ── */
  .center-area {
    grid-column: 2;
    grid-row: 1 / 3;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  /* ── POWER SCRIPTS ── */
  .scripts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    flex-shrink: 0;
  }

  .script-card {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .script-label {
    font-size: 9.5px;
    font-weight: 800;
    color: #2A7A76;
  }

  .script-text {
    background: #FFF8DC;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 9px;
    color: #333;
    font-style: italic;
    line-height: 1.52;
    flex: 1;
    border-left: 3px solid #E8C840;
  }

  /* ── FOOTER ── */
  .footer {
    text-align: center;
    font-size: 8px;
    color: #999;
    flex-shrink: 0;
  }

  .evidence-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #F0F9F9;
    border: 1px solid #B8DEDE;
    border-radius: 20px;
    padding: 2px 14px;
    font-size: 8px;
    color: #666;
    font-weight: 700;
  }
</style>
</head>
<body>
<div class="page">

  <!-- Corner decorations -->
  <div class="deco deco-tl"></div>
  <div class="deco deco-tr"></div>
  <div class="deco deco-br"></div>
  <div class="deco deco-bl"></div>

  <!-- ── TITLE ── -->
  <div class="title-area">
    <div class="main-title">
      The "Pause and Pivot" Plan:<br>
      <span class="italic-part">Ending the Tug-of-War with a Defiant Child</span>
    </div>
    <div class="subtitle">
      This guide provides a structured way to handle "No!" and power struggles without losing your cool or giving in.
      It moves the child from a state of defiance to a state of <strong>collaboration</strong> by addressing their need for autonomy.
    </div>
  </div>

  <!-- ── USE THIS GUIDE IF ── -->
  <div class="dotted-box">
    <div class="dotted-header">✦ Use This Guide If Your Child: ✦</div>
    <div class="bullet-grid">
      <div class="bullet-item">
        <span class="bullet-icon">✓</span>
        <span>Digs their heels in when given a direction.</span>
      </div>
      <div class="bullet-item">
        <span class="bullet-icon">✓</span>
        <span>Responds to every request with "No" or "Make me."</span>
      </div>
      <div class="bullet-item">
        <span class="bullet-icon">✓</span>
        <span>Negotiates or argues to avoid simple tasks.</span>
      </div>
      <div class="bullet-item">
        <span class="bullet-icon">✓</span>
        <span>Ignores you until you start raising your voice.</span>
      </div>
    </div>
  </div>

  <!-- ── SECTION BAR ── -->
  <div class="section-bar">The 4-Step De-Escalation Loop</div>

  <!-- ── LOOP AREA ── -->
  <div class="loop-area">

    <!-- Background dashed loop circle -->
    <svg class="loop-bg-svg" viewBox="0 0 740 100%" preserveAspectRatio="xMidYMid meet"
         xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%;">
      <!-- We use a percentage-based ellipse centered on the grid -->
      <!-- Center col starts at 208+10=218px, width=(740-416-20)=304px, center=218+152=370px -->
      <!-- Rows are equal height, so vertical center is at 50% -->
      <ellipse cx="370" cy="50%" rx="130" ry="44%"
        fill="none"
        stroke="#7BBFBF"
        stroke-width="4"
        stroke-dasharray="14 9"
        opacity="0.45"/>
      <!-- Clockwise arrow heads on ellipse -->
      <!-- Top (pointing right) -->
      <path d="M370,6% L378,12% L362,12%" fill="#7BBFBF" opacity="0.5"/>
      <!-- Right (pointing down) -->
      <path d="M500,50% L492,57% L492,43%" fill="#7BBFBF" opacity="0.5"/>
      <!-- Bottom (pointing left) -->
      <path d="M370,94% L362,88% L378,88%" fill="#7BBFBF" opacity="0.5"/>
      <!-- Left (pointing up) -->
      <path d="M240,50% L248,43% L248,57%" fill="#7BBFBF" opacity="0.5"/>
    </svg>

    <div class="loop-grid">

      <!-- Step 1: Drop the Rope -->
      <div class="step-card">
        <div class="step-card-header">
          <div class="step-badge">1</div>
          <div class="step-title">Drop the Rope</div>
        </div>
        <div class="step-rule"></div>
        <div class="step-body">
          Stop the back-and-forth arguing immediately. You cannot win a power struggle while you are actively pulling on your end of the rope.
          <br><br>
          Take one step back physically to show you aren't a threat.
        </div>
      </div>

      <!-- Center illustration -->
      <div class="center-area">
        ${illustrationSVG}
      </div>

      <!-- Step 2: Offer Two "Yes" Options -->
      <div class="step-card">
        <div class="step-card-header">
          <div class="step-badge">2</div>
          <div class="step-title">Offer Two "Yes" Options</div>
        </div>
        <div class="step-rule"></div>
        <div class="step-body">
          Defiance is often a desperate grab for control. Give it back to them in a way that still gets the job done. Both options must lead to the same goal.
        </div>
        <div class="step-example">
          <strong>Example:</strong> "Do you want to put your shoes on in the kitchen or by the front door?"
        </div>
      </div>

      <!-- Step 3: When/Then Contract -->
      <div class="step-card">
        <div class="step-card-header">
          <div class="step-badge">3</div>
          <div class="step-title">The "When/Then" Contract</div>
        </div>
        <div class="step-rule"></div>
        <div class="step-body">
          Move away from threats ("If you don't...") and move toward logical sequences. This makes the desired activity the "reward" for the necessary task.
        </div>
        <div class="step-example">
          <strong>Example:</strong> "When your toys are in the bin, then we can head to the park."
        </div>
      </div>

      <!-- Step 4: The Silent Wait -->
      <div class="step-card">
        <div class="step-card-header">
          <div class="step-badge">4</div>
          <div class="step-title">The Silent Wait</div>
        </div>
        <div class="step-rule"></div>
        <div class="step-body">
          After giving the choice, walk away or look at your watch. Counting to ten in your head gives their brain time to process the request without the pressure of your "stare," which often triggers more defiance.
        </div>
      </div>

    </div><!-- /loop-grid -->
  </div><!-- /loop-area -->

  <!-- ── POWER SCRIPTS ── -->
  <div class="section-bar">Power Scripts</div>

  <div class="scripts-grid">
    <div class="script-card">
      <div class="script-label">To bypass the "No":</div>
      <div class="script-text">"I'm not going to argue about this. I'll be in the kitchen; let me know if you want to do [Option A] or [Option B]."</div>
    </div>
    <div class="script-card">
      <div class="script-label">To shift to the next task:</div>
      <div class="script-text">"I see you're not ready yet. I'll come back in two minutes to see if you've decided to start."</div>
    </div>
    <div class="script-card">
      <div class="script-label">To acknowledge the frustration:</div>
      <div class="script-text">"It's tough when you have to stop playing to do chores. I get it. Do you want to hop like a frog to the sink or walk like a penguin?"</div>
    </div>
  </div>

  <!-- ── FOOTER ── -->
  <div class="footer">
    <span class="evidence-badge">✓ Therapist-Vetted &amp; Evidence-Based</span>
  </div>

</div>
</body>
</html>`;

// ─────────────────────────────────────────────────────────────────────────────
// RENDER
// ─────────────────────────────────────────────────────────────────────────────
async function main() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
  });

  const page = await browser.newPage();

  // US Letter portrait at 300 DPI
  // CSS pixels at 96 DPI: 816 × 1056
  // Scale factor to reach 300 DPI: 300/96 ≈ 3.125 → output: 2550 × 3300 px
  await page.setViewport({ width: 816, height: 1056, deviceScaleFactor: 3.125 });

  console.log('Rendering HTML...');
  await page.setContent(html, { waitUntil: 'networkidle0', timeout: 30000 });

  // Wait for web fonts to finish loading
  await page.evaluateHandle('document.fonts.ready');

  console.log('Capturing screenshot...');
  await page.screenshot({
    path: OUTPUT,
    clip: { x: 0, y: 0, width: 816, height: 1056 }
  });

  await browser.close();
  console.log(`\n✅ Done! Output saved to:\n   ${OUTPUT}`);
  console.log(`   Size: 2550 × 3300 px (300 DPI, US Letter Portrait)`);
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
