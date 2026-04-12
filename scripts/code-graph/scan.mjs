#!/usr/bin/env node
/**
 * Quét thư mục (mặc định: ../../src) — acorn cho JS, regex cho .css / .html.
 * Đầu ra: ../../static/data/code-graph.json { nodes, edges, meta }
 *
 * Usage: node scan.mjs [--root <path>] [--out <file>]
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import * as acorn from 'acorn';
import { simple as walk } from 'acorn-walk';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../..');

function parseArgs() {
  const args = process.argv.slice(2);
  let root = path.join(REPO_ROOT, 'src');
  let out = path.join(REPO_ROOT, 'static', 'data', 'code-graph.json');
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--root' && args[i + 1]) {
      const raw = args[++i];
      root = path.isAbsolute(raw) ? path.normalize(raw) : path.join(REPO_ROOT, raw);
    } else if (args[i] === '--out' && args[i + 1]) {
      const raw = args[++i];
      out = path.isAbsolute(raw) ? path.normalize(raw) : path.join(REPO_ROOT, raw);
    }
  }
  return { root, out };
}

const TEXT_EXT = new Set(['.js', '.jsx', '.mjs', '.cjs', '.css', '.html']);

function walkFiles(dir, base, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (['node_modules', '.git', 'dist', 'build'].includes(e.name)) continue;
      walkFiles(full, base, acc);
    } else {
      const ext = path.extname(e.name).toLowerCase();
      if (TEXT_EXT.has(ext)) {
        const rel = path.relative(base, full).split(path.sep).join('/');
        acc.push({ full, rel, ext });
      }
    }
  }
  return acc;
}

function tryResolveFile(fromFile, spec) {
  if (!spec || spec.startsWith('data:')) return null;
  if (/^https?:\/\//i.test(spec)) return null;
  let s = spec.trim();
  const dir = path.dirname(fromFile);
  let resolved = path.normalize(path.resolve(dir, s));
  const candidates = [
    resolved,
    resolved + '.js',
    resolved + '.jsx',
    resolved + '.mjs',
    resolved + '.json',
    path.join(resolved, 'index.js'),
    path.join(resolved, 'index.jsx'),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(c) && fs.statSync(c).isFile()) return path.normalize(c);
    } catch {
      /* ignore */
    }
  }
  return null;
}

function extractCssImports(content, fromFile) {
  const out = [];
  const re = /@import\s+(?:url\s*\(\s*)?['"]?([^'")\s;]+)['"]?\s*\)?/gi;
  let m;
  while ((m = re.exec(content)) !== null) {
    const t = tryResolveFile(fromFile, m[1].trim());
    if (t) out.push(t);
  }
  return out;
}

function extractHtmlRefs(content, fromFile) {
  const out = [];
  const scriptRe = /<script[^>]+src\s*=\s*["']([^"']+)["']/gi;
  const linkRe = /<link[^>]+href\s*=\s*["']([^"']+)["']/gi;
  let m;
  while ((m = scriptRe.exec(content)) !== null) {
    const t = tryResolveFile(fromFile, m[1]);
    if (t) out.push(t);
  }
  while ((m = linkRe.exec(content)) !== null) {
    if (/\.css(\?|$)/i.test(m[1])) {
      const t = tryResolveFile(fromFile, m[1]);
      if (t) out.push(t);
    }
  }
  return out;
}

function classifyJsKind(relPath, exportNames, defaultExportName) {
  if (/\.jsx$/i.test(relPath)) return 'component';
  const base = path.basename(relPath, path.extname(relPath));
  if (/component$/i.test(base) || /^[A-Z]/.test(defaultExportName || '')) return 'component';
  const hasPascalDefault = /^[A-Z]/.test(defaultExportName || '');
  if (hasPascalDefault) return 'component';
  if (exportNames.length && exportNames.every((n) => n !== 'default' && /^[a-z_$]/.test(String(n)))) return 'function';
  return 'module';
}

function parseJsFile(fullPath, rel, fileIndexAbsToRel) {
  const content = fs.readFileSync(fullPath, 'utf8');
  const importSpecs = [];
  const exportNames = [];
  let defaultExportName = '';
  const functions = [];

  let ast = null;
  const tryParse = (sourceType) => {
    try {
      return acorn.parse(content, {
        ecmaVersion: 'latest',
        sourceType,
        locations: false,
        allowAwaitOutsideFunction: true,
      });
    } catch {
      return null;
    }
  };
  ast = tryParse('module') || tryParse('script');

  if (ast) {
    walk(ast, {
      ImportDeclaration(node) {
        importSpecs.push(node.source.value);
      },
      ExportNamedDeclaration(node) {
        if (node.declaration) {
          const d = node.declaration;
          if (d.type === 'FunctionDeclaration' && d.id) {
            exportNames.push(d.id.name);
            functions.push(d.id.name);
          } else if (d.type === 'VariableDeclaration') {
            for (const decl of d.declarations) {
              if (decl.id && decl.id.name) exportNames.push(decl.id.name);
            }
          } else if (d.type === 'ClassDeclaration' && d.id) {
            exportNames.push(d.id.name);
            functions.push(`class ${d.id.name}`);
          }
        }
        if (node.specifiers) {
          for (const s of node.specifiers) {
            if (s.exported && s.exported.name) exportNames.push(s.exported.name);
          }
        }
      },
      ExportDefaultDeclaration(node) {
        const d = node.declaration;
        if (d.type === 'FunctionDeclaration' && d.id) {
          defaultExportName = d.id.name;
          functions.push(d.id.name);
          exportNames.push('default');
        } else if (d.type === 'Identifier') {
          defaultExportName = d.name;
          exportNames.push('default');
        } else if (d.type === 'ClassDeclaration' && d.id) {
          defaultExportName = d.id.name;
          functions.push(`class ${d.id.name}`);
          exportNames.push('default');
        } else {
          exportNames.push('default');
        }
      },
      FunctionDeclaration(node) {
        if (node.id && node.id.name) functions.push(node.id.name);
      },
      ClassDeclaration(node) {
        if (node.id && node.id.name) functions.push(`class ${node.id.name}`);
      },
    });
  }

  const resolvedImports = [];
  for (const spec of importSpecs) {
    const abs = tryResolveFile(fullPath, spec);
    if (abs && fileIndexAbsToRel.has(abs)) resolvedImports.push(fileIndexAbsToRel.get(abs));
  }

  const kind = classifyJsKind(rel, exportNames, defaultExportName);
  const ext = path.extname(rel).replace(/^\./, '') || 'js';

  return {
    rel,
    kind,
    extension: ext,
    imports: resolvedImports,
    functions: [...new Set(functions)],
    exports: [...new Set(exportNames)],
  };
}

function main() {
  const { root, out } = parseArgs();
  const rootNorm = path.normalize(path.resolve(root));

  if (!fs.existsSync(rootNorm)) {
    console.warn('Thư mục không tồn tại:', rootNorm);
    const empty = {
      nodes: [],
      edges: [],
      meta: {
        scannedRoot: rootNorm,
        generatedAt: new Date().toISOString(),
        warning: 'root_missing',
      },
    };
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, JSON.stringify(empty, null, 2), 'utf8');
    console.log('Đã ghi JSON rỗng →', out);
    process.exit(0);
  }

  const files = walkFiles(rootNorm, rootNorm);
  const fileIndexAbsToRel = new Map();
  for (const f of files) {
    fileIndexAbsToRel.set(path.normalize(f.full), f.rel);
  }

  const nodes = [];
  const edgeKeys = new Set();
  const edges = [];

  function addEdge(fromRel, toRel) {
    if (!fromRel || !toRel || fromRel === toRel) return;
    const k = `${fromRel}-->${toRel}`;
    if (edgeKeys.has(k)) return;
    edgeKeys.add(k);
    edges.push({
      data: {
        id: `e_${edges.length + 1}`,
        source: fromRel,
        target: toRel,
        label: 'imports',
      },
    });
  }

  for (const f of files) {
    if (f.ext === '.css') {
      const content = fs.readFileSync(f.full, 'utf8');
      const targets = extractCssImports(content, f.full);
      for (const abs of targets) {
        const tid = fileIndexAbsToRel.get(path.normalize(abs));
        if (tid) addEdge(f.rel, tid);
      }
      nodes.push({
        data: {
          id: f.rel,
          label: path.basename(f.rel),
          path: f.rel,
          kind: 'style',
          extension: 'css',
          functions: [],
          exports: [],
        },
      });
    } else if (f.ext === '.html') {
      const content = fs.readFileSync(f.full, 'utf8');
      const targets = extractHtmlRefs(content, f.full);
      for (const abs of targets) {
        const tid = fileIndexAbsToRel.get(path.normalize(abs));
        if (tid) addEdge(f.rel, tid);
      }
      nodes.push({
        data: {
          id: f.rel,
          label: path.basename(f.rel),
          path: f.rel,
          kind: 'template',
          extension: 'html',
          functions: [],
          exports: [],
        },
      });
    } else if (['.js', '.jsx', '.mjs', '.cjs'].includes(f.ext)) {
      const info = parseJsFile(f.full, f.rel, fileIndexAbsToRel);
      for (const tid of info.imports) addEdge(info.rel, tid);
      nodes.push({
        data: {
          id: info.rel,
          label: path.basename(info.rel),
          path: info.rel,
          kind: info.kind,
          extension: info.extension,
          functions: info.functions,
          exports: info.exports,
        },
      });
    }
  }

  const payload = {
    nodes,
    edges,
    meta: {
      scannedRoot: rootNorm,
      generatedAt: new Date().toISOString(),
      fileCount: files.length,
    },
  };

  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(payload, null, 2), 'utf8');
  console.log(`OK: ${nodes.length} nodes, ${edges.length} edges → ${out}`);
}

main();
