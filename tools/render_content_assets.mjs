import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

const root = path.resolve(process.argv[2] || 'content-output/week-01');
function walk(dir) {
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap((e) => {
    const p = path.join(dir,e.name);
    return e.isDirectory() ? walk(p) : [p];
  });
}
const files=walk(root).filter((p)=>p.endsWith('.svg'));
let count=0;
for(const svg of files){
  const relative=path.relative(root,svg);
  const image=sharp(svg,{density:96});
  if(relative.includes(`${path.sep}slides${path.sep}`)){
    // Carousel artwork is designed as 4:5 at 1080×1350; never squeeze it into a 9:16 reel canvas.
    await image.resize({width:1080,height:1350,fit:'contain',background:'#ffffff'}).png({compressionLevel:8}).toFile(svg.replace(/\.svg$/i,'.png'));
  } else if(relative.includes(`${path.sep}reel-source${path.sep}`)){
    // Reel storyboard frames are 9:16; render at a lightweight preview size without distortion.
    await image.resize({width:540,height:960,fit:'contain',background:'#ffffff'}).png({compressionLevel:8}).toFile(svg.replace(/\.svg$/i,'.png'));
  } else {
    // Standalone post/story vectors keep their source dimensions and aspect ratio.
    await image.png({compressionLevel:8}).toFile(svg.replace(/\.svg$/i,'.png'));
  }
  count++;
}
console.log(`Rendered ${count} SVG files to aspect-correct PNGs.`);
