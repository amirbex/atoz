import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

const root = path.resolve(process.argv[2] || 'پیش‌انتشار/ماه-اول/هفته-اول');
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
  if(relative.includes(`${path.sep}slides${path.sep}`) || relative.includes(`${path.sep}reel-source${path.sep}`)){
    const png=svg.replace(/\.svg$/i,'.png');
    await sharp(svg,{density:96}).resize({width:540,height:960,fit:'contain',background:'#ffffff'}).png().toFile(png);
  } else {
    const png=svg.replace(/\.svg$/i,'.png');
    await sharp(svg,{density:96}).png().toFile(png);
  }
  count++;
}
console.log(`Rendered ${count} SVG files to PNG.`);
