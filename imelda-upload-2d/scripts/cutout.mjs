// Background removal for new portraits. Usage (from a folder where @imgly/background-removal-node is installed):
//   node path/to/scripts/cutout.mjs input.jpg=name [more.jpg=name2]
// Writes name.png next to where you run it. Move it into source-photos/cutouts/.
import { removeBackground } from '@imgly/background-removal-node';
import { readFileSync, writeFileSync } from 'node:fs';
for (const job of process.argv.slice(2)) {
  const [src, name] = job.split('=');
  const blob = await removeBackground(new Blob([readFileSync(src)], { type: src.endsWith('.png') ? 'image/png' : 'image/jpeg' }), { model: 'medium', output: { format: 'image/png', quality: 1 } });
  writeFileSync(`${name}.png`, Buffer.from(await blob.arrayBuffer()));
  console.log('wrote', `${name}.png`);
}
