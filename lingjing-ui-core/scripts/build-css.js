const fs = require('fs');
const path = require('path');

const baseDir = path.resolve(__dirname, '../components/src/styles');
const distDir = path.resolve(__dirname, '../components/dist');

const scenarios = [
  { entry: '05-entry/index-b-system.css', out: 'lingjing-core-b-system.css' },
  { entry: '05-entry/index-ue5-overlay.css', out: 'lingjing-core-ue5-overlay.css' },
  { entry: '05-entry/index-website.css', out: 'lingjing-core-website.css' },
  { entry: '05-entry/index-presentation.css', out: 'lingjing-core-presentation.css' }
];


scenarios.forEach(scenario => {
  const entryPath = path.join(baseDir, scenario.entry);
  if (!fs.existsSync(entryPath)) {
      console.error(`Entry not found: ${entryPath}`);
      return;
  }

  const content = fs.readFileSync(entryPath, 'utf8');
  // Match @import '../01-foundation/variables.css'; style imports
  const importRegex = /@import\s+['"]\.\.\/(.*?)['"];/g;
  let match;
  let output = `/**
 * Lingjing Core - Dist Build
 * Generated at ${new Date().toLocaleString()}
 * Based on ${scenario.entry}
 */\n\n`;

  while ((match = importRegex.exec(content)) !== null) {
    const relativePath = match[1];
    const absolutePath = path.resolve(baseDir, relativePath);
    const fileName = path.basename(relativePath);

    if (fs.existsSync(absolutePath)) {
      const fileContent = fs.readFileSync(absolutePath, 'utf8');
      output += `/* === ${fileName} === */\n${fileContent}\n\n`;
    } else {
      console.warn(`File not found: ${absolutePath}`);
    }
  }

  if (!fs.existsSync(distDir)) {
      fs.mkdirSync(distDir, { recursive: true });
  }
  fs.writeFileSync(path.join(distDir, scenario.out), output);
  console.log(`Successfully generated ${scenario.out}`);
});
