/**
 * generate_illustration.js
 * Uses Gemini (NanoBanana) to generate a child + parent illustration.
 * Usage: node tools/generate_illustration.js
 * Output: .tmp/illustration.png
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const { GoogleGenAI } = require('@google/genai');
const fs = require('fs');
const path = require('path');

const OUTPUT = path.join(__dirname, '../.tmp/illustration.png');

const PROMPT = `
An illustration of a young Black boy (around 9 years old) and a warm, light-skinned mother holding hands and smiling gently at each other.
The boy has natural curly hair and wears a teal shirt. The mother has warm brown hair in a loose bun and wears a soft rose-colored top.
They are standing side by side, the mother slightly taller, both looking calm and connected.
Style: soft children's educational book illustration — delicate graphite pencil linework with light, transparent watercolor washes in muted teal, soft peach, and warm beige tones.
Clean white background. No text. Warm, hopeful, and gentle mood. Full figures visible from head to feet.
`.trim();

async function main() {
  if (!process.env.GEMINI_API_KEY) {
    console.error('❌ GEMINI_API_KEY not found in .env');
    process.exit(1);
  }

  const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

  console.log('Generating illustration with NanoBanana (Gemini)...');

  const response = await ai.models.generateContent({
    model: 'gemini-2.5-flash-image',
    contents: PROMPT,
  });

  let saved = false;
  for (const part of response.candidates[0].content.parts) {
    if (part.inlineData) {
      const buffer = Buffer.from(part.inlineData.data, 'base64');
      fs.writeFileSync(OUTPUT, buffer);
      console.log(`✅ Illustration saved to: ${OUTPUT}`);
      saved = true;
      break;
    }
    if (part.text) {
      console.log('Model response text:', part.text);
    }
  }

  if (!saved) {
    console.error('❌ No image data returned in response.');
    process.exit(1);
  }
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
