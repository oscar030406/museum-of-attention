// 把第三方库和字体放进站内，网站运行时不请求任何外部域名。
// 用法：cd vendor-build && npm ci && npm run build
import { build } from "esbuild";
import { copyFileSync, mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const site = join(here, "..", "site", "assets");
const nm = join(here, "node_modules");
const pkg = JSON.parse(readFileSync(join(here, "package.json"), "utf8"));

// 1. 3D 图谱：3d-force-graph、three、泛光通道和输出通道（负责色彩空间转换）打成一个文件，three 只有一份
mkdirSync(join(site, "vendor"), { recursive: true });
await build({
  stdin: {
    contents: `
      import ForceGraph3D from "3d-force-graph";
      import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
      import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
      import { Vector2 } from "three";
      window.MuseumGraph3D = { ForceGraph3D, UnrealBloomPass, OutputPass, Vector2 };`,
    resolveDir: here,
    loader: "js",
  },
  bundle: true,
  minify: true,
  format: "iife",
  target: "es2020",
  legalComments: "eof",
  outfile: join(site, "vendor", "graph3d.min.js"),
});

await build({
  stdin: {
    contents: 'export { default } from "openseadragon";',
    resolveDir: here,
  },
  bundle: true,
  minify: true,
  format: "esm",
  target: "es2020",
  legalComments: "eof",
  outfile: join(site, "vendor", "openseadragon.min.js"),
});
copyFileSync(join(nm, "openseadragon", "LICENSE.txt"), join(site, "vendor", "LICENSE-OpenSeadragon.txt"));

// 2. 字体：Archivo 可变字体（字重和字宽两个轴）与 IBM Plex Mono，连同许可证
const fonts = join(site, "fonts");
mkdirSync(fonts, { recursive: true });
const files = [
  ["@fontsource-variable/archivo/files/archivo-latin-standard-normal.woff2", "archivo-latin.woff2"],
  ["@fontsource-variable/archivo/files/archivo-latin-ext-standard-normal.woff2", "archivo-latin-ext.woff2"],
  ["@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2", "ibm-plex-mono-400.woff2"],
  ["@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-500-normal.woff2", "ibm-plex-mono-500.woff2"],
  ["@fontsource-variable/archivo/LICENSE", "LICENSE-Archivo.txt"],
  ["@fontsource/ibm-plex-mono/LICENSE", "LICENSE-IBM-Plex-Mono.txt"],
];
for (const [src, dst] of files) copyFileSync(join(nm, src), join(fonts, dst));

const latin = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD";
const latinExt = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF";
writeFileSync(join(fonts, "fonts.css"), `/* 由 vendor-build/build.mjs 生成，不要手改 */
@font-face { font-family: "Archivo"; font-style: normal; font-display: swap; font-weight: 100 900; font-stretch: 62% 125%;
  src: url(archivo-latin-ext.woff2) format("woff2-variations"); unicode-range: ${latinExt}; }
@font-face { font-family: "Archivo"; font-style: normal; font-display: swap; font-weight: 100 900; font-stretch: 62% 125%;
  src: url(archivo-latin.woff2) format("woff2-variations"); unicode-range: ${latin}; }
@font-face { font-family: "IBM Plex Mono"; font-style: normal; font-display: swap; font-weight: 400;
  src: url(ibm-plex-mono-400.woff2) format("woff2"); unicode-range: ${latin}; }
@font-face { font-family: "IBM Plex Mono"; font-style: normal; font-display: swap; font-weight: 500;
  src: url(ibm-plex-mono-500.woff2) format("woff2"); unicode-range: ${latin}; }
`);

writeFileSync(join(site, "vendor", "VERSIONS.txt"),
  Object.entries(pkg.dependencies).map(([k, v]) => `${k} ${v}`).join("\n") + "\n");
console.log("vendor ok:", Object.entries(pkg.dependencies).map(([k, v]) => `${k}@${v}`).join(", "));
