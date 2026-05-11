import * as esbuild from "esbuild";
import { copyFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = resolve(__dirname, "..", "source", "_static", "hero");

const watch = process.argv.includes("--watch");

const buildOpts = {
  entryPoints: [resolve(__dirname, "main.js")],
  bundle: true,
  format: "iife",
  globalName: "LaionFmriHero",
  target: ["es2020"],
  minify: true,
  sourcemap: false,
  outfile: resolve(OUT_DIR, "hero.js"),
  legalComments: "none",
};

async function copyCss() {
  await copyFile(
    resolve(__dirname, "hero.css"),
    resolve(OUT_DIR, "hero.css"),
  );
  console.log("→ copied hero.css");
}

if (watch) {
  const ctx = await esbuild.context(buildOpts);
  await ctx.watch();
  await copyCss();
  console.log("watching hero source for changes...");
} else {
  const result = await esbuild.build(buildOpts);
  await copyCss();
  const bytes = (await import("node:fs/promises"))
    .stat(buildOpts.outfile)
    .then((s) => s.size);
  console.log(`→ built hero.js (${((await bytes) / 1024).toFixed(1)} KB)`);
  if (result.errors.length) process.exit(1);
}
