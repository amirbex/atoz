import sharp from "sharp";
import fs from "node:fs";
import path from "node:path";
const dir=path.resolve(process.argv[2]||"../content-output/week-01/motion-lab/frames");
for(const name of fs.readdirSync(dir).filter(x=>x.endsWith(".svg")).sort()){
 const src=path.join(dir,name);
 await sharp(src,{density:96}).resize(540,960,{fit:"contain",background:"#0A1931"}).png({compressionLevel:8}).toFile(src.replace(/\.svg$/i,".png"));
}
console.log(`Rendered ${fs.readdirSync(dir).filter(x=>x.endsWith(".svg")).length} motion keyframes.`);
