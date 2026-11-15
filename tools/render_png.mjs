/**
 * Render the generated logo library: 2048px logo PNGs, a 2400px guideline,
 * app icons and standard favicon sizes. Run from tools/: npm run render-png.
 */
import sharp from "sharp";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const LOGO_DIR = path.join(ROOT, "logo");
const LOGO_WIDTH = 2048;
const ICON_DIR = path.join(LOGO_DIR, "icons");
const ICON_SVG = path.join(ICON_DIR, "svg", "app-icon.svg");

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(file) : [file];
  });
}

function pngPathFor(svgPath) {
  const rel = path.relative(LOGO_DIR, svgPath).split(path.sep);
  const svgAt = rel.indexOf("svg");
  if (svgAt >= 0) rel[svgAt] = "png";
  else rel[0] = "png";
  return path.join(LOGO_DIR, ...rel).replace(/\.svg$/i, ".png");
}

async function render(svgPath, pngPath, width) {
  fs.mkdirSync(path.dirname(pngPath), { recursive: true });
  const buffer = await sharp(svgPath, { density: 144 }).resize({ width }).png().toBuffer();
  fs.writeFileSync(pngPath, buffer);
  console.log(`  ${path.relative(ROOT, pngPath)} (${Math.round(buffer.length / 1024)} KB)`);
  return buffer;
}

function makeIco(entries) {
  const header = Buffer.alloc(6 + entries.length * 16);
  header.writeUInt16LE(0, 0); header.writeUInt16LE(1, 2); header.writeUInt16LE(entries.length, 4);
  let offset = header.length;
  const chunks = [header];
  entries.forEach(({ size, data }, i) => {
    const p = 6 + i * 16;
    header.writeUInt8(size === 256 ? 0 : size, p);
    header.writeUInt8(size === 256 ? 0 : size, p + 1);
    header.writeUInt8(0, p + 2); header.writeUInt8(0, p + 3);
    header.writeUInt16LE(1, p + 4); header.writeUInt16LE(32, p + 6);
    header.writeUInt32LE(data.length, p + 8); header.writeUInt32LE(offset, p + 12);
    chunks.push(data); offset += data.length;
  });
  return Buffer.concat(chunks);
}

fs.mkdirSync(LOGO_DIR, { recursive: true });
const svgs = walk(LOGO_DIR).filter((file) => file.endsWith(".svg"));
for (const svg of svgs) {
  if (svg.includes(`${path.sep}icons${path.sep}`)) continue;
  const width = svg.includes(`${path.sep}guidelines${path.sep}`) ? 2400 : LOGO_WIDTH;
  await render(svg, pngPathFor(svg), width);
}

const sizes = [16, 32, 48, 180, 192, 512];
const icoParts = [];
for (const size of sizes) {
  const buffer = await sharp(ICON_SVG, { density: 144 }).resize(size, size, { fit: "contain" }).png().toBuffer();
  const filename = size === 180 ? "apple-touch-icon.png" : `favicon-${size}.png`;
  const out = path.join(ICON_DIR, "png", filename);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, buffer);
  if (size <= 48) icoParts.push({ size, data: buffer });
  console.log(`  ${path.relative(ROOT, out)} (${Math.round(buffer.length / 1024)} KB)`);
}
const appIcon = await render(ICON_SVG, path.join(ICON_DIR, "png", "app-icon.png"), 1024);
fs.writeFileSync(path.join(ICON_DIR, "png", "favicon.ico"), makeIco(icoParts));
console.log(`  ${path.relative(ROOT, path.join(ICON_DIR, "png", "favicon.ico"))}`);
console.log("Done.");
