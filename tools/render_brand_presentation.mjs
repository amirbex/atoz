import sharp from "sharp";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const dir=path.join(root,"brand/presentation/slides");
for(const name of fs.readdirSync(dir).filter(n=>n.endsWith(".svg")).sort()){
 const source=path.join(dir,name);
 await sharp(source,{density:144}).resize({width:1920,height:1080,fit:"fill"}).png({compressionLevel:9}).toFile(source.replace(/\.svg$/i,".png"));
}
console.log("Rendered 10 1920×1080 presentation slides.");
