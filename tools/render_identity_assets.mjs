import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

const roots = process.argv.slice(2).map((x) => path.resolve(x));
if (!roots.length) roots.push(...['brand/brand-book/slides', 'brand/sheets', 'content-templates'].map((x) => path.resolve(x)));
function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap((e) => {
    const p = path.join(dir, e.name);
    return e.isDirectory() ? walk(p) : [p];
  });
}
let total=0;
for (const root of roots) {
  const svgs=walk(root).filter((p)=>p.toLowerCase().endsWith('.svg'));
  for (const svg of svgs) {
    const png=svg.replace(/\.svg$/i,'.png');
    await sharp(svg,{density:96}).png().toFile(png);
    total++;
  }
}
console.log(`Rendered ${total} identity SVG previews to PNG.`);
