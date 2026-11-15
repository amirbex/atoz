import sharp from "sharp";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const targets = [];
function addTree(directory, predicate, widthFor) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) addTree(file, predicate, widthFor);
    else if (file.endsWith(".svg") && predicate(file)) targets.push([file, widthFor(file)]);
  }
}
addTree(path.join(ROOT, "logo/primary"), () => true, (file) => file.includes("square") ? 1800 : 2048);
addTree(path.join(ROOT, "logo/subbrands"), (file) => file.includes("/logos/") || file.includes("/icons/"), () => 1600);
addTree(path.join(ROOT, "logo/icons"), () => true, () => 1024);
addTree(path.join(ROOT, "logo/brand-book/slides"), () => true, () => 1600);
addTree(path.join(ROOT, "content-templates"), () => true, (file) => file.includes("reel-") ? 1080 : 1350);
for (const [source, width] of targets) {
  const destination = source.replace(/\.svg$/i, ".png");
  await sharp(source, { density: 144 }).resize({ width }).png({ compressionLevel: 9 }).toFile(destination);
}
console.log(`Rendered ${targets.length} responsive raster previews from SVG source files.`);
