#!/usr/bin/env node
/**
 * Quét repo mã nguồn và sinh Knowledge Graph phong phú hơn cho dashboard admin.
 *
 * Đầu ra: ../../static/data/code-graph.json
 * Shape chính vẫn giữ:
 *   { nodes, edges, meta }
 *
 * Nâng cấp:
 * - Hỗ trợ quét Python, JS, HTML, CSS và file config/deploy phổ biến.
 * - Sinh node file + function + class + API route + database.
 * - Gắn metadata để UI có thể hiển thị risk, learning notes, trace flow.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import * as acorn from 'acorn';
import * as acornWalk from 'acorn-walk';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../..');

const JS_EXTS = new Set(['.js', '.jsx', '.mjs', '.cjs']);
const PY_EXTS = new Set(['.py']);
const STYLE_EXTS = new Set(['.css']);
const HTML_EXTS = new Set(['.html']);
const CONFIG_EXTS = new Set(['.json', '.yml', '.yaml', '.toml', '.ini', '.cfg']);
const SPECIAL_FILES = new Set([
  'Procfile',
  'requirements.txt',
  'package-lock.json',
  'package.json',
  'render.yaml',
  'pytest.ini',
  '.env.example',
  '.gitignore',
  '.prettierignore',
  '.prettierrc.json',
  '.db_resolved.json',
]);
const IGNORED_DIRS = new Set([
  '.cursor',
  '.git',
  '.idea',
  '.pytest_cache',
  '.venv',
  '.vscode',
  '__pycache__',
  'backups',
  'build',
  'dist',
  'instance',
  'logs',
  'node_modules',
]);
const RISK_HIGH_KEYWORDS = ['delete', 'remove', 'update', 'edit', 'save', 'backup', 'restore', 'admin'];
const SECURITY_KEYWORDS = ['auth', 'login', 'logout', 'password', 'token', 'session', 'csrf', 'permission', 'secure'];
const DB_WRITE_KEYWORDS = ['insert', 'update', 'delete', 'replace', 'commit', 'executemany', 'save'];
const COMPLEXITY_KEYWORDS = ['tree', 'graph', 'ancestor', 'descendant', 'lineage', 'branch', 'recursive', 'recursion'];
const VIEW_RELEVANT_EDGE_TYPES = new Set([
  'imports',
  'calls',
  'uses',
  'route_to_handler',
  'reads_db',
  'writes_db',
  'renders',
  'configures',
]);

function parseArgs() {
  const args = process.argv.slice(2);
  let root = REPO_ROOT;
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

function normalizeRel(base, fullPath) {
  return path.relative(base, fullPath).split(path.sep).join('/');
}

function isIgnoredDirectory(base, fullPath, dirName) {
  if (IGNORED_DIRS.has(dirName)) return true;
  const rel = normalizeRel(base, fullPath);
  if (!rel) return false;
  if (rel.startsWith('static/images')) return true;
  if (rel.startsWith('scripts/code-graph/node_modules')) return true;
  return false;
}

function shouldIncludeFile(fileName, ext, rel) {
  if (SPECIAL_FILES.has(fileName)) return true;
  if (JS_EXTS.has(ext) || PY_EXTS.has(ext) || STYLE_EXTS.has(ext) || HTML_EXTS.has(ext) || CONFIG_EXTS.has(ext)) {
    return true;
  }
  if (fileName === 'README.txt' && rel.startsWith('static/images/')) return false;
  return false;
}

function walkFiles(dir, base, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (isIgnoredDirectory(base, full, entry.name)) continue;
      walkFiles(full, base, acc);
      continue;
    }
    const ext = path.extname(entry.name).toLowerCase();
    const rel = normalizeRel(base, full);
    if (!shouldIncludeFile(entry.name, ext, rel)) continue;
    acc.push({ full, rel, ext, name: entry.name });
  }
  return acc;
}

function safeRead(fullPath) {
  try {
    return fs.readFileSync(fullPath, 'utf8');
  } catch {
    return '';
  }
}

function uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}

function toLabel(rel) {
  return path.basename(rel);
}

function makeNodeId(fileRel, type, name) {
  return `${fileRel}::${type}::${name}`;
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function languageOf(rel, ext) {
  if (JS_EXTS.has(ext)) return 'js';
  if (PY_EXTS.has(ext)) return 'py';
  if (STYLE_EXTS.has(ext)) return 'css';
  if (HTML_EXTS.has(ext)) return 'html';
  if (ext === '.json') return 'json';
  if (['.yml', '.yaml'].includes(ext)) return 'yaml';
  if (ext === '.toml') return 'toml';
  if (ext === '.ini' || path.basename(rel) === 'Procfile') return 'config';
  return 'other';
}

function isConfigFile(rel, ext) {
  const base = path.basename(rel);
  return SPECIAL_FILES.has(base) || CONFIG_EXTS.has(ext) || base === 'Procfile';
}

function isEntryPointFile(rel) {
  return [
    'app.py',
    'start_server.py',
    'render.yaml',
    'Procfile',
    'templates/index.html',
    'templates/admin/dashboard.html',
    'static/js/index.js',
  ].includes(rel);
}

function classifyFileNodeType(rel, ext) {
  if (STYLE_EXTS.has(ext)) return 'style';
  if (isConfigFile(rel, ext)) return 'config';
  if (HTML_EXTS.has(ext) && rel.includes('/partials/')) return 'component';
  if (JS_EXTS.has(ext) && ext === '.jsx') return 'component';
  return 'file';
}

function buildPythonModuleIndex(files) {
  const index = new Map();
  for (const file of files) {
    if (!PY_EXTS.has(file.ext)) continue;
    let moduleName = file.rel.replace(/\.py$/i, '').replace(/\//g, '.');
    if (moduleName.endsWith('.__init__')) {
      moduleName = moduleName.slice(0, -'.__init__'.length);
    }
    if (moduleName) index.set(moduleName, file.rel);
  }
  return index;
}

function buildTemplateIndex(files) {
  const index = new Map();
  for (const file of files) {
    if (!HTML_EXTS.has(file.ext)) continue;
    if (file.rel.startsWith('templates/')) {
      index.set(file.rel.slice('templates/'.length), file.rel);
    }
  }
  return index;
}

function tryResolveFile(fromFile, spec) {
  if (!spec || spec.startsWith('data:')) return null;
  if (/^https?:\/\//i.test(spec)) return null;
  const trimmed = spec.trim();
  if (/^\{\{/.test(trimmed)) return null;
  if (/^\/(static|templates)\//.test(trimmed)) {
    const repoAbsolute = path.normalize(path.join(REPO_ROOT, trimmed.replace(/^\//, '')));
    if (fs.existsSync(repoAbsolute) && fs.statSync(repoAbsolute).isFile()) {
      return repoAbsolute;
    }
  }
  const withoutQuery = trimmed.split('?')[0].split('#')[0];
  const dir = path.dirname(fromFile);
  const resolved = path.normalize(path.resolve(dir, withoutQuery));
  const candidates = [
    resolved,
    resolved + '.js',
    resolved + '.jsx',
    resolved + '.mjs',
    resolved + '.css',
    resolved + '.html',
    resolved + '.py',
    path.join(resolved, 'index.js'),
    path.join(resolved, 'index.jsx'),
  ];
  for (const candidate of candidates) {
    try {
      if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return path.normalize(candidate);
    } catch {
      // ignore
    }
  }
  return null;
}

function extractCssImports(content, fromFile) {
  const imports = [];
  const re = /@import\s+(?:url\s*\(\s*)?['"]?([^'")\s;]+)['"]?\s*\)?/gi;
  let match;
  while ((match = re.exec(content)) !== null) {
    const target = tryResolveFile(fromFile, match[1].trim());
    if (target) imports.push(target);
  }
  return imports;
}

function extractHtmlRefs(content, fromFile) {
  const refs = [];
  const scriptRe = /<script[^>]+src\s*=\s*["']([^"']+)["']/gi;
  const linkRe = /<link[^>]+href\s*=\s*["']([^"']+)["']/gi;
  let match;
  while ((match = scriptRe.exec(content)) !== null) {
    const target = tryResolveFile(fromFile, match[1]);
    if (target) refs.push(target);
  }
  while ((match = linkRe.exec(content)) !== null) {
    const target = tryResolveFile(fromFile, match[1]);
    if (target) refs.push(target);
  }
  return refs;
}

function extractTemplateIncludes(content, templateIndex) {
  const refs = [];
  const includeRe = /{%\s*(?:include|extends)\s+['"]([^'"]+)['"]/g;
  let match;
  while ((match = includeRe.exec(content)) !== null) {
    const target = templateIndex.get(match[1]);
    if (target) refs.push(target);
  }
  return refs;
}

function classifyJsKind(relPath, exportNames, defaultExportName) {
  if (/\.jsx$/i.test(relPath)) return 'component';
  const base = path.basename(relPath, path.extname(relPath));
  if (/component$/i.test(base) || /^[A-Z]/.test(defaultExportName || '')) return 'component';
  if (exportNames.length && exportNames.every((name) => name !== 'default' && /^[a-z_$]/.test(String(name)))) {
    return 'function';
  }
  return 'module';
}

function moduleLikeKindsFromPath(rel) {
  const text = rel.toLowerCase();
  const kinds = [];
  if (text.includes('service')) kinds.push('service');
  if (text.includes('util')) kinds.push('utility');
  if (text.includes('auth')) kinds.push('auth');
  if (text.includes('config') || text.includes('.env') || text.includes('procfile') || text.includes('render')) {
    kinds.push('config');
  }
  if (text.includes('admin')) kinds.push('admin');
  if (text.includes('gallery') || text.includes('activities') || text.includes('genealogy')) kinds.push('feature');
  return kinds;
}

function tagFromText(rel, content) {
  const text = `${rel}\n${content}`.toLowerCase();
  const tags = [];
  if (/(auth|login|logout|password|token|session|csrf|current_user|permission)/.test(text)) tags.push('auth', 'security');
  if (/(cursor\.execute|mysql|database|select |insert |update |delete |commit|rollback|db_)/.test(text)) tags.push('database', 'sql');
  if (/(tree|ancestor|descendant|lineage|branch)/.test(text)) tags.push('tree');
  if (/(graph|cytoscape|network|node|edge)/.test(text)) tags.push('graph');
  if (/(fetch\(|axios|\/api\/|@app\.route|@.*\.route)/.test(text)) tags.push('api');
  if (/(render_template|template|jinja|innerhtml|domcontentloaded|document\.getelementbyid)/.test(text)) tags.push('rendering');
  if (/(render\.yaml|procfile|gunicorn|deploy|railway|volume|cookie_domain|environment|secret_key)/.test(text)) {
    tags.push('deployment', 'config');
  }
  if (/(backup|restore|archive|dump|filesystem|os\.path|pathlib|send_file)/.test(text)) tags.push('backup', 'file-system');
  if (/(pytest|test_|assert |unittest)/.test(text)) tags.push('testing');
  if (/(helper|util|format|sanitize|escapehtml)/.test(text)) tags.push('utility');
  if (/(frontend|document\.|window\.|cytoscape|css|html|template|component)/.test(text)) tags.push('frontend');
  if (/(recursive|recursion)/.test(text)) tags.push('recursion');
  return uniq(tags);
}

function inheritedSymbolTags(fileTags) {
  const allow = new Set(['frontend', 'rendering', 'tree', 'graph', 'utility', 'testing', 'api']);
  return Array.isArray(fileTags) ? fileTags.filter((tag) => allow.has(tag)) : [];
}

function technicalKindsForNode(type, rel, tags, extra = {}) {
  const kinds = moduleLikeKindsFromPath(rel);
  if (type === 'api_route') kinds.push('api_route');
  if (type === 'style') kinds.push('style');
  if (type === 'component') kinds.push('frontend_component');
  if (type === 'config') kinds.push('config');
  if (tags.includes('database')) kinds.push('database_related');
  if (tags.includes('auth') || tags.includes('security')) kinds.push('security_related');
  if (tags.includes('utility')) kinds.push('utility');
  if (extra.isEntryPoint) kinds.push('entry_point');
  if (extra.functionRole === 'helper') kinds.push('helper_function');
  if (extra.functionRole === 'db') kinds.push('database_function');
  if (extra.functionRole === 'auth') kinds.push('auth_function');
  return uniq(kinds);
}

function makeFileNode(file, content) {
  const type = classifyFileNodeType(file.rel, file.ext);
  const tags = tagFromText(file.rel, content);
  const isEntryPoint = isEntryPointFile(file.rel);
  return {
    id: file.rel,
    label: toLabel(file.rel),
    type,
    kind: type === 'file' ? 'module' : type,
    path: file.rel,
    language: languageOf(file.rel, file.ext),
    extension: file.ext.replace(/^\./, '') || 'other',
    description: '',
    riskLevel: 'low',
    tags,
    technicalKinds: technicalKindsForNode(type, file.rel, tags, { isEntryPoint }),
    calls: [],
    calledBy: [],
    relatedFiles: [],
    learningNotes: [],
    suggestedTests: [],
    securityNotes: [],
    functions: [],
    exports: [],
    classes: [],
    routeIds: [],
    isEntryPoint,
    isSecurityRelated: tags.includes('security') || tags.includes('auth'),
    isDatabaseRelated: tags.includes('database'),
    hasManyDependencies: false,
    isOrphan: false,
  };
}

function collectCallNames(text) {
  const names = [];
  const re = /\b([A-Za-z_][A-Za-z0-9_]*)\s*\(/g;
  const excluded = new Set([
    'if',
    'for',
    'while',
    'switch',
    'catch',
    'return',
    'function',
    'class',
    'new',
    'super',
    'console',
  ]);
  let match;
  while ((match = re.exec(text)) !== null) {
    const name = match[1];
    if (!excluded.has(name)) names.push(name);
  }
  return names;
}

function extractQuotedApiPaths(text) {
  const paths = [];
  const re = /['"`](\/api\/[^'"`]+)['"`]/g;
  let match;
  while ((match = re.exec(text)) !== null) paths.push(match[1]);
  return uniq(paths);
}

function parseJsFile(fullPath, rel, fileIndexAbsToRel) {
  const content = safeRead(fullPath);
  const importSpecs = [];
  const importSymbolMap = new Map();
  const exportNames = [];
  let defaultExportName = '';
  const functionDefs = [];
  const classDefs = [];
  const templateRefs = [];
  let ast = null;

  const tryParse = (sourceType) => {
    try {
      return acorn.parse(content, {
        ecmaVersion: 'latest',
        sourceType,
        allowAwaitOutsideFunction: true,
      });
    } catch {
      return null;
    }
  };
  ast = tryParse('module') || tryParse('script');

  if (ast) {
    acornWalk.simple(ast, {
      ImportDeclaration(node) {
        const spec = node.source.value;
        importSpecs.push(spec);
        const abs = tryResolveFile(fullPath, spec);
        const targetRel = abs ? fileIndexAbsToRel.get(abs) : null;
        if (targetRel && Array.isArray(node.specifiers)) {
          for (const specifier of node.specifiers) {
            if (specifier.local && specifier.local.name) {
              importSymbolMap.set(specifier.local.name, targetRel);
            }
          }
        }
      },
      ExportNamedDeclaration(node) {
        if (node.declaration) {
          const decl = node.declaration;
          if (decl.type === 'FunctionDeclaration' && decl.id) {
            exportNames.push(decl.id.name);
          } else if (decl.type === 'ClassDeclaration' && decl.id) {
            exportNames.push(decl.id.name);
          } else if (decl.type === 'VariableDeclaration') {
            for (const item of decl.declarations || []) {
              if (item.id && item.id.name) exportNames.push(item.id.name);
            }
          }
        }
        for (const specifier of node.specifiers || []) {
          if (specifier.exported && specifier.exported.name) exportNames.push(specifier.exported.name);
        }
      },
      ExportDefaultDeclaration(node) {
        const decl = node.declaration;
        exportNames.push('default');
        if (decl.type === 'FunctionDeclaration' && decl.id) defaultExportName = decl.id.name;
        if (decl.type === 'ClassDeclaration' && decl.id) defaultExportName = decl.id.name;
      },
      FunctionDeclaration(node) {
        if (!node.id || !node.id.name) return;
        functionDefs.push({
          name: node.id.name,
          start: node.start,
          end: node.end,
          exported: exportNames.includes(node.id.name),
        });
      },
      VariableDeclarator(node) {
        if (!node.id || !node.id.name || !node.init) return;
        if (node.init.type === 'ArrowFunctionExpression' || node.init.type === 'FunctionExpression') {
          functionDefs.push({
            name: node.id.name,
            start: node.start,
            end: node.end,
            exported: exportNames.includes(node.id.name),
          });
        }
      },
      ClassDeclaration(node) {
        if (!node.id || !node.id.name) return;
        classDefs.push({
          name: node.id.name,
          start: node.start,
          end: node.end,
          exported: exportNames.includes(node.id.name),
        });
      },
      CallExpression(node) {
        if (
          node.callee &&
          node.callee.type === 'Identifier' &&
          node.callee.name === 'fetch' &&
          node.arguments &&
          node.arguments[0] &&
          node.arguments[0].type === 'Literal'
        ) {
          templateRefs.push(node.arguments[0].value);
        }
      },
    });
  }

  const resolvedImports = [];
  for (const spec of importSpecs) {
    const abs = tryResolveFile(fullPath, spec);
    if (abs && fileIndexAbsToRel.has(abs)) resolvedImports.push(fileIndexAbsToRel.get(abs));
  }

  const localFunctionNames = new Set(functionDefs.map((item) => item.name));
  const functionCalls = [];
  for (const fn of functionDefs) {
    const snippet = content.slice(fn.start, fn.end);
    const calls = collectCallNames(snippet);
    functionCalls.push({
      name: fn.name,
      calls,
      apiPaths: extractQuotedApiPaths(snippet),
      isRecursive: calls.includes(fn.name),
    });
  }

  const kind = classifyJsKind(rel, exportNames, defaultExportName);
  const ext = path.extname(rel).replace(/^\./, '') || 'js';

  return {
    rel,
    kind,
    extension: ext,
    imports: uniq(resolvedImports),
    functions: functionDefs,
    classes: classDefs,
    exports: uniq(exportNames),
    importSymbolMap,
    localFunctionNames,
    functionCalls,
    apiRefs: uniq(templateRefs),
    content,
  };
}

function resolvePythonImportFile(currentRel, moduleSpec, fileIndexByModule) {
  if (!moduleSpec) return null;
  let targetModule = moduleSpec;
  if (moduleSpec.startsWith('.')) {
    const dots = moduleSpec.match(/^\.+/)[0].length;
    const rest = moduleSpec.slice(dots);
    let currentModule = currentRel.replace(/\.py$/i, '').replace(/\//g, '.');
    if (!currentRel.endsWith('__init__.py')) {
      currentModule = currentModule.split('.').slice(0, -1).join('.');
    }
    const baseParts = currentModule ? currentModule.split('.') : [];
    const prefix = baseParts.slice(0, Math.max(0, baseParts.length - (dots - 1)));
    targetModule = rest ? prefix.concat(rest.split('.')).join('.') : prefix.join('.');
  }
  return fileIndexByModule.get(targetModule) || null;
}

function parseFlaskRoutesFromDecorators(decorators) {
  const routes = [];
  for (const decorator of decorators) {
    const routeMatch = decorator.match(/@[\w.]+\.(route|get|post|put|patch|delete)\s*\((.*)\)\s*$/);
    if (!routeMatch) continue;
    const decoratorKind = routeMatch[1].toLowerCase();
    const argsText = routeMatch[2];
    const pathMatch = argsText.match(/['"]([^'"]+)['"]/);
    if (!pathMatch) continue;
    const routePath = pathMatch[1];
    let methods = [];
    const methodsMatch = argsText.match(/methods\s*=\s*\[([^\]]+)\]/i);
    if (methodsMatch) {
      methods = methodsMatch[1]
        .split(',')
        .map((item) => item.replace(/['"\s]/g, '').toUpperCase())
        .filter(Boolean);
    } else if (decoratorKind !== 'route') {
      methods = [decoratorKind.toUpperCase()];
    } else {
      methods = ['GET'];
    }
    for (const method of methods) {
      routes.push({ method, path: routePath });
    }
  }
  return routes;
}

function parsePythonFile(fullPath, rel, fileIndexByModule, templateIndex) {
  const content = safeRead(fullPath);
  const lines = content.split(/\r?\n/);
  const imports = [];
  const importSymbolMap = new Map();
  const topLevelDefs = [];
  const classes = [];
  let pendingDecorators = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    const importMatch = line.match(/^\s*import\s+([A-Za-z0-9_.,\s]+)$/);
    if (importMatch) {
      const specs = importMatch[1].split(',');
      for (const raw of specs) {
        const cleaned = raw.trim();
        if (!cleaned) continue;
        const parts = cleaned.split(/\s+as\s+/);
        const moduleSpec = parts[0].trim();
        const alias = (parts[1] || moduleSpec.split('.').pop()).trim();
        const targetFile = resolvePythonImportFile(rel, moduleSpec, fileIndexByModule);
        if (targetFile) {
          imports.push(targetFile);
          importSymbolMap.set(alias, targetFile);
        }
      }
    }

    const fromImportMatch = line.match(/^\s*from\s+([.\w]+)\s+import\s+(.+)$/);
    if (fromImportMatch) {
      const moduleSpec = fromImportMatch[1].trim();
      const targetFile = resolvePythonImportFile(rel, moduleSpec, fileIndexByModule);
      if (targetFile) imports.push(targetFile);
      const names = fromImportMatch[2].split(',');
      for (const raw of names) {
        const cleaned = raw.trim();
        if (!cleaned) continue;
        const parts = cleaned.split(/\s+as\s+/);
        const importedName = parts[0].trim();
        const alias = (parts[1] || importedName).trim();
        if (targetFile) importSymbolMap.set(alias, targetFile);
      }
    }

    if (/^\s*@/.test(line)) {
      pendingDecorators.push(trimmed);
      continue;
    }

    const classMatch = line.match(/^class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(|:)/);
    if (classMatch) {
      classes.push({
        name: classMatch[1],
        lineIndex: i,
      });
      pendingDecorators = [];
      continue;
    }

    const defMatch = line.match(/^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(/);
    if (defMatch) {
      topLevelDefs.push({
        name: defMatch[1],
        lineIndex: i,
        decorators: pendingDecorators,
      });
      pendingDecorators = [];
      continue;
    }

    if (trimmed) pendingDecorators = [];
  }

  for (let i = 0; i < topLevelDefs.length; i++) {
    const current = topLevelDefs[i];
    const next = topLevelDefs[i + 1];
    const endLine = next ? next.lineIndex : lines.length;
    current.body = lines.slice(current.lineIndex, endLine).join('\n');
    current.routes = parseFlaskRoutesFromDecorators(current.decorators || []);
  }

  for (let i = 0; i < classes.length; i++) {
    const current = classes[i];
    const nextClass = classes[i + 1];
    const nextDef = topLevelDefs.find((item) => item.lineIndex > current.lineIndex);
    const endLineCandidates = [nextClass?.lineIndex, nextDef?.lineIndex].filter(Number.isInteger);
    const endLine = endLineCandidates.length ? Math.min(...endLineCandidates) : lines.length;
    current.body = lines.slice(current.lineIndex, endLine).join('\n');
  }

  const renderRefs = [];
  const renderRe = /render_template\(\s*['"]([^'"]+)['"]/g;
  let renderMatch;
  while ((renderMatch = renderRe.exec(content)) !== null) {
    const target = templateIndex.get(renderMatch[1]);
    if (target) renderRefs.push(target);
  }

  return {
    rel,
    imports: uniq(imports),
    importSymbolMap,
    functions: topLevelDefs,
    classes,
    renderRefs: uniq(renderRefs),
    content,
  };
}

function addNode(nodesById, data) {
  const existing = nodesById.get(data.id);
  if (existing) {
    nodesById.set(data.id, {
      ...existing,
      ...data,
      tags: uniq([...(existing.tags || []), ...(data.tags || [])]),
      technicalKinds: uniq([...(existing.technicalKinds || []), ...(data.technicalKinds || [])]),
      functions: uniq([...(existing.functions || []), ...(data.functions || [])]),
      exports: uniq([...(existing.exports || []), ...(data.exports || [])]),
      classes: uniq([...(existing.classes || []), ...(data.classes || [])]),
      routeIds: uniq([...(existing.routeIds || []), ...(data.routeIds || [])]),
    });
    return;
  }
  nodesById.set(data.id, {
    description: '',
    riskLevel: 'low',
    tags: [],
    technicalKinds: [],
    calls: [],
    calledBy: [],
    relatedFiles: [],
    learningNotes: [],
    suggestedTests: [],
    securityNotes: [],
    functions: [],
    exports: [],
    classes: [],
    routeIds: [],
    isEntryPoint: false,
    isSecurityRelated: false,
    isDatabaseRelated: false,
    hasManyDependencies: false,
    isOrphan: false,
    ...data,
  });
}

function addEdge(edges, edgeKeys, source, target, type, label) {
  if (!source || !target || source === target) return;
  const key = `${source}::${target}::${type}`;
  if (edgeKeys.has(key)) return;
  edgeKeys.add(key);
  edges.push({
    id: `e_${edges.length + 1}`,
    source,
    target,
    type,
    label,
  });
}

function ensureDatabaseNode(nodesById) {
  const dbId = 'database:mysql';
  if (!nodesById.has(dbId)) {
    addNode(nodesById, {
      id: dbId,
      label: 'database:mysql',
      type: 'database',
      kind: 'database',
      path: 'database:mysql',
      language: 'sql',
      extension: 'db',
      tags: ['database', 'sql'],
      technicalKinds: ['database'],
      description: 'Điểm đại diện cho MySQL/database access trong project.',
      isDatabaseRelated: true,
    });
  }
  return dbId;
}

function guessFunctionRole(name, tags) {
  const lower = String(name || '').toLowerCase();
  if (tags.includes('database') || /(db|query|cursor|sql|backup|restore)/.test(lower)) return 'db';
  if (tags.includes('auth') || /(auth|login|logout|password|token|session|permission)/.test(lower)) return 'auth';
  if (/(format|normalize|sanitize|escape|helper|util)/.test(lower)) return 'helper';
  return '';
}

function createFunctionNode(fileRel, fnName, language, baseTags, extra = {}) {
  const type = extra.isClass ? 'class' : extra.isRoute ? 'api_route' : 'function';
  const tags = uniq([...(baseTags || []), ...(extra.tags || [])]);
  const functionRole = type === 'api_route' ? '' : guessFunctionRole(fnName, tags);
  return {
    id: makeNodeId(fileRel, type, fnName),
    label: extra.isRoute ? fnName : fnName,
    type,
    kind: type,
    path: fileRel,
    parentId: fileRel,
    language,
    extension: language,
    tags,
    technicalKinds: technicalKindsForNode(type, fileRel, tags, { functionRole }),
    isEntryPoint: !!extra.isEntryPoint,
    isSecurityRelated: tags.includes('security') || tags.includes('auth'),
    isDatabaseRelated: tags.includes('database'),
    routePath: extra.routePath || '',
    httpMethod: extra.httpMethod || '',
    functionRole,
    description: '',
    calls: [],
    calledBy: [],
    relatedFiles: [],
    learningNotes: [],
    suggestedTests: [],
    securityNotes: [],
  };
}

function enrichDescriptions(node) {
  const tags = node.tags || [];
  if (node.type === 'api_route') {
    const method = node.httpMethod || 'GET';
    const routePath = node.routePath || node.label;
    return `${method} ${routePath} - entry point API/route của hệ thống.`;
  }
  if (node.type === 'database') {
    return 'Node đại diện cho lớp truy cập cơ sở dữ liệu và các thao tác SQL.';
  }
  if (node.type === 'class') {
    return `Class ${node.label} dùng cho ${tags.length ? tags.join(', ') : 'logic nghiệp vụ'}.`;
  }
  if (node.type === 'function') {
    if (node.functionRole === 'db') return `Hàm ${node.label} liên quan truy vấn hoặc cập nhật dữ liệu.`;
    if (node.functionRole === 'auth') return `Hàm ${node.label} liên quan xác thực hoặc kiểm soát truy cập.`;
    if (tags.includes('tree') || tags.includes('graph')) {
      return `Hàm ${node.label} xử lý quan hệ cây/đồ thị hoặc duyệt dữ liệu có cấu trúc.`;
    }
    return `Hàm ${node.label} trong module ${path.basename(node.path)}.`;
  }
  if (node.type === 'style') {
    return 'File style/CSS phục vụ trình bày giao diện.';
  }
  if (node.type === 'config') {
    return 'File cấu hình hoặc triển khai của project.';
  }
  if (node.type === 'component') {
    return 'Template/partial hoặc frontend component phục vụ rendering.';
  }
  if (tags.includes('database')) return 'File/module có liên quan đến database hoặc truy vấn SQL.';
  if (tags.includes('auth')) return 'File/module có liên quan đến xác thực hoặc bảo mật.';
  if (node.isEntryPoint) return 'Điểm vào quan trọng của ứng dụng hoặc luồng xử lý.';
  return 'File/module mã nguồn trong project.';
}

function buildLearningNotes(node) {
  const notes = [];
  const tags = node.tags || [];
  if (tags.includes('recursion')) notes.push('Liên quan recursion và cách tránh lặp vô hạn.');
  if (tags.includes('tree')) notes.push('Liên quan tree traversal, ancestor/descendant hoặc dữ liệu phân cấp.');
  if (tags.includes('graph')) notes.push('Liên quan graph modeling, node-edge relationship hoặc visualization.');
  if (tags.includes('api')) notes.push('Liên quan thiết kế API, request/response và validation.');
  if (tags.includes('database')) notes.push('Liên quan SQL, connection pooling, transaction hoặc data consistency.');
  if (tags.includes('auth')) notes.push('Liên quan authentication, session và access control.');
  if (tags.includes('rendering')) notes.push('Liên quan frontend rendering, template flow hoặc DOM update.');
  if (tags.includes('deployment')) notes.push('Liên quan deploy, environment variables hoặc runtime config.');
  if (tags.includes('backup')) notes.push('Liên quan backup/restore, data recovery và volume/storage.');
  if (!notes.length && node.type === 'style') notes.push('Liên quan UI styling, layout và khả năng đọc giao diện.');
  return notes;
}

function buildSuggestedTests(node) {
  const tests = [];
  const tags = node.tags || [];
  if (node.type === 'api_route') {
    tests.push('Kiểm tra status code, input validation và response shape.');
  }
  if (tags.includes('auth') || node.isSecurityRelated) {
    tests.push('Kiểm tra authorization, session boundary và access control.');
  }
  if (node.isDatabaseRelated) {
    tests.push('Kiểm tra SQL path, dữ liệu ghi/đọc và rollback khi lỗi.');
  }
  if (tags.includes('tree') || tags.includes('graph') || tags.includes('recursion')) {
    tests.push('Kiểm tra edge case vòng lặp, dữ liệu thiếu parent/child và input lớn.');
  }
  if (node.riskLevel === 'high') {
    tests.push('Ưu tiên regression test, security review và log/audit path.');
  }
  if (node.type === 'style' || node.type === 'component') {
    tests.push('Kiểm tra responsive/layout và không làm vỡ UI hiện có.');
  }
  return uniq(tests);
}

function buildSecurityNotes(node) {
  const notes = [];
  if (node.type === 'api_route' && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(node.httpMethod)) {
    notes.push('Route có khả năng thay đổi dữ liệu, cần kiểm tra auth/permission rõ ràng.');
  }
  if (node.isSecurityRelated) {
    notes.push('Có liên quan auth/session/password/token, cần review secret handling và access control.');
  }
  if (node.isDatabaseRelated && node.riskLevel === 'high') {
    notes.push('Kiểm tra câu SQL ghi/xóa/sửa, tránh thiếu audit hoặc thiếu guard.');
  }
  return notes;
}

function computeRisk(node, outgoing, incoming) {
  const text = `${node.label} ${node.path} ${(node.tags || []).join(' ')} ${(node.technicalKinds || []).join(' ')}`.toLowerCase();
  const hasHighKeyword = [...RISK_HIGH_KEYWORDS, ...SECURITY_KEYWORDS].some((keyword) => text.includes(keyword));
  const hasComplexKeyword = COMPLEXITY_KEYWORDS.some((keyword) => text.includes(keyword));
  const mutatingRoute = node.type === 'api_route' && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(node.httpMethod);
  const writesDb = outgoing.some((edge) => edge.type === 'writes_db');
  const readsDb = outgoing.some((edge) => edge.type === 'reads_db');
  const manyDeps = outgoing.filter((edge) => VIEW_RELEVANT_EDGE_TYPES.has(edge.type)).length >= 6;
  const manyCallers = incoming.filter((edge) => VIEW_RELEVANT_EDGE_TYPES.has(edge.type)).length >= 5;

  if (mutatingRoute || writesDb || (node.isSecurityRelated && hasHighKeyword) || /backup|restore|admin/.test(text)) {
    return 'high';
  }
  if (node.type === 'style' || (node.type === 'component' && !manyDeps && !manyCallers && !readsDb)) {
    return 'low';
  }
  if (hasComplexKeyword || node.isDatabaseRelated || node.isSecurityRelated || manyDeps || manyCallers || readsDb) {
    return 'medium';
  }
  return hasHighKeyword ? 'medium' : 'low';
}

function buildOverview(nodes, edges) {
  const fileNodes = nodes.filter((node) => ['file', 'config', 'component', 'style'].includes(node.type));
  const functionNodes = nodes.filter((node) => node.type === 'function');
  const routeNodes = nodes.filter((node) => node.type === 'api_route');
  const highRiskNodes = nodes.filter((node) => node.riskLevel === 'high');
  const orphanNodes = nodes.filter((node) => node.isOrphan);

  const topDependencyFiles = fileNodes
    .map((node) => ({
      id: node.id,
      label: node.label,
      path: node.path,
      count: node.dependencyCount || 0,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  const topCalledNodes = nodes
    .map((node) => ({
      id: node.id,
      label: node.label,
      path: node.path,
      count: node.dependentCount || 0,
      type: node.type,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  const reviewAreas = [];
  if (highRiskNodes.length) reviewAreas.push('Review các node high-risk trước, đặc biệt route ghi dữ liệu và module auth/admin.');
  if (routeNodes.some((node) => node.riskLevel === 'high')) reviewAreas.push('Ưu tiên kiểm tra API POST/PUT/PATCH/DELETE và permission guard.');
  if (fileNodes.some((node) => node.hasManyDependencies)) reviewAreas.push('Các file phụ thuộc nhiều nên được tách nhỏ hoặc thêm test regression.');
  if (orphanNodes.length) reviewAreas.push('Có orphan node, kiểm tra xem là dead code hay entry point chưa được scan đủ.');
  if (!reviewAreas.length) reviewAreas.push('Graph hiện tương đối ổn định; ưu tiên học từ entry point và luồng API chính.');

  return {
    totalFiles: fileNodes.length,
    totalFunctions: functionNodes.length,
    totalApiRoutes: routeNodes.length,
    highRiskCount: highRiskNodes.length,
    orphanCount: orphanNodes.length,
    topDependencyFiles,
    topCalledNodes,
    reviewAreas,
  };
}

function main() {
  const { root, out } = parseArgs();
  const rootNorm = path.normalize(path.resolve(root));

  if (!fs.existsSync(rootNorm)) {
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
  for (const file of files) {
    fileIndexAbsToRel.set(path.normalize(file.full), file.rel);
  }
  const fileIndexByModule = buildPythonModuleIndex(files);
  const templateIndex = buildTemplateIndex(files);

  const nodesById = new Map();
  const edges = [];
  const edgeKeys = new Set();
  const localFunctionIndex = new Map();
  const pendingJsApiEdges = [];

  // Bước 1: luôn tạo file node trước để UI file view không bị phụ thuộc parser.
  for (const file of files) {
    const content = safeRead(file.full);
    addNode(nodesById, makeFileNode(file, content));
  }

  // Bước 2: phân tích từng file và sinh node/edge chi tiết.
  for (const file of files) {
    const fileNode = nodesById.get(file.rel);
    const content = safeRead(file.full);

    if (STYLE_EXTS.has(file.ext)) {
      const imports = extractCssImports(content, file.full);
      for (const abs of imports) {
        const targetRel = fileIndexAbsToRel.get(path.normalize(abs));
        if (targetRel) addEdge(edges, edgeKeys, file.rel, targetRel, 'imports', 'imports');
      }
      fileNode.description = 'File style/CSS của giao diện admin hoặc trang công khai.';
      continue;
    }

    if (HTML_EXTS.has(file.ext)) {
      const refs = extractHtmlRefs(content, file.full);
      const templateRefs = extractTemplateIncludes(content, templateIndex);
      for (const abs of refs) {
        const targetRel = fileIndexAbsToRel.get(path.normalize(abs));
        if (targetRel) addEdge(edges, edgeKeys, file.rel, targetRel, 'uses', 'uses');
      }
      for (const targetRel of templateRefs) {
        addEdge(edges, edgeKeys, file.rel, targetRel, 'renders', 'renders');
      }
      continue;
    }

    if (JS_EXTS.has(file.ext)) {
      const info = parseJsFile(file.full, file.rel, fileIndexAbsToRel);
      fileNode.kind = info.kind;
      fileNode.functions = uniq(info.functions.map((item) => item.name));
      fileNode.classes = uniq(info.classes.map((item) => item.name));
      fileNode.exports = info.exports;
      fileNode.tags = uniq([...fileNode.tags, ...tagFromText(file.rel, info.content)]);
      fileNode.technicalKinds = technicalKindsForNode(fileNode.type, file.rel, fileNode.tags, {
        isEntryPoint: fileNode.isEntryPoint,
      });

      for (const targetRel of info.imports) {
        addEdge(edges, edgeKeys, file.rel, targetRel, 'imports', 'imports');
      }

      for (const classDef of info.classes) {
        const classTags = uniq([...inheritedSymbolTags(fileNode.tags), ...tagFromText(classDef.name, info.content.slice(classDef.start, classDef.end))]);
        const classNode = createFunctionNode(file.rel, classDef.name, 'js', classTags, { isClass: true });
        addNode(nodesById, classNode);
        addEdge(edges, edgeKeys, file.rel, classNode.id, 'defines', 'defines');
      }

      for (const fn of info.functions) {
        localFunctionIndex.set(`${file.rel}::${fn.name}`, makeNodeId(file.rel, 'function', fn.name));
      }

      for (const fn of info.functions) {
        const callInfo = info.functionCalls.find((item) => item.name === fn.name);
        const fnTags = uniq([
          ...inheritedSymbolTags(fileNode.tags),
          ...tagFromText(fn.name, info.content.slice(fn.start, fn.end)),
          ...(callInfo && callInfo.isRecursive ? ['recursion'] : []),
          ...((callInfo && callInfo.apiPaths.length) ? ['api'] : []),
        ]);
        const fnNode = createFunctionNode(file.rel, fn.name, 'js', fnTags);
        addNode(nodesById, fnNode);
        addEdge(edges, edgeKeys, file.rel, fnNode.id, 'defines', 'defines');

        for (const callName of (callInfo ? callInfo.calls : [])) {
          const localTarget = localFunctionIndex.get(`${file.rel}::${callName}`) || makeNodeId(file.rel, 'function', callName);
          if (nodesById.has(localTarget)) {
            addEdge(edges, edgeKeys, fnNode.id, localTarget, 'calls', 'calls');
          } else if (info.importSymbolMap.has(callName)) {
            addEdge(edges, edgeKeys, fnNode.id, info.importSymbolMap.get(callName), 'calls', 'calls');
          }
        }

        for (const apiPath of (callInfo ? callInfo.apiPaths : [])) {
          pendingJsApiEdges.push({
            sourceId: fnNode.id,
            httpMethod: 'GET',
            routePath: apiPath,
          });
        }
      }
      continue;
    }

    if (PY_EXTS.has(file.ext)) {
      const info = parsePythonFile(file.full, file.rel, fileIndexByModule, templateIndex);
      fileNode.functions = uniq(info.functions.map((item) => item.name));
      fileNode.classes = uniq(info.classes.map((item) => item.name));
      fileNode.tags = uniq([...fileNode.tags, ...tagFromText(file.rel, info.content)]);
      fileNode.technicalKinds = technicalKindsForNode(fileNode.type, file.rel, fileNode.tags, {
        isEntryPoint: fileNode.isEntryPoint,
      });

      for (const targetRel of info.imports) {
        addEdge(edges, edgeKeys, file.rel, targetRel, 'imports', 'imports');
      }

      for (const targetRel of info.renderRefs) {
        addEdge(edges, edgeKeys, file.rel, targetRel, 'renders', 'renders');
      }

      for (const classDef of info.classes) {
        const classTags = uniq([...inheritedSymbolTags(fileNode.tags), ...tagFromText(classDef.name, classDef.body || '')]);
        const classNode = createFunctionNode(file.rel, classDef.name, 'py', classTags, { isClass: true });
        addNode(nodesById, classNode);
        addEdge(edges, edgeKeys, file.rel, classNode.id, 'defines', 'defines');
      }

      const localPythonFunctionIds = new Map();
      for (const fn of info.functions) {
        localPythonFunctionIds.set(fn.name, makeNodeId(file.rel, 'function', fn.name));
      }
      for (const fn of info.functions) {
        const fnTags = uniq([...inheritedSymbolTags(fileNode.tags), ...tagFromText(fn.name, fn.body || '')]);
        const fnNode = createFunctionNode(file.rel, fn.name, 'py', fnTags);
        addNode(nodesById, fnNode);
        addEdge(edges, edgeKeys, file.rel, fnNode.id, 'defines', 'defines');

        const bodyLower = (fn.body || '').toLowerCase();
        const callNames = collectCallNames(fn.body || '');
        for (const callName of callNames) {
          if (localPythonFunctionIds.has(callName)) {
            addEdge(edges, edgeKeys, fnNode.id, localPythonFunctionIds.get(callName), 'calls', 'calls');
          } else if (info.importSymbolMap.has(callName)) {
            addEdge(edges, edgeKeys, fnNode.id, info.importSymbolMap.get(callName), 'calls', 'calls');
          }
        }

        const renderRe = /render_template\(\s*['"]([^'"]+)['"]/g;
        let renderMatch;
        while ((renderMatch = renderRe.exec(fn.body || '')) !== null) {
          const templateRel = templateIndex.get(renderMatch[1]);
          if (templateRel) addEdge(edges, edgeKeys, fnNode.id, templateRel, 'renders', 'renders');
        }

        const hasDbAccess = /(cursor\.execute|mysql|database|db_)/.test(bodyLower);
        if (hasDbAccess) {
          const dbNodeId = ensureDatabaseNode(nodesById);
          const writesDb = DB_WRITE_KEYWORDS.some((keyword) => bodyLower.includes(keyword));
          addEdge(edges, edgeKeys, fnNode.id, dbNodeId, writesDb ? 'writes_db' : 'reads_db', writesDb ? 'writes DB' : 'reads DB');
        }

        if (fn.routes && fn.routes.length) {
          for (const route of fn.routes) {
            const routeLabel = `${route.method} ${route.path}`;
            const routeNode = createFunctionNode(file.rel, routeLabel, 'py', uniq([...fnTags, 'api']), {
              isRoute: true,
              routePath: route.path,
              httpMethod: route.method,
              isEntryPoint: true,
            });
            routeNode.id = makeNodeId(file.rel, 'route', routeLabel);
            routeNode.label = routeLabel;
            addNode(nodesById, routeNode);
            addEdge(edges, edgeKeys, file.rel, routeNode.id, 'defines', 'defines');
            addEdge(edges, edgeKeys, routeNode.id, fnNode.id, 'route_to_handler', 'route_to_handler');
            fileNode.routeIds = uniq([...(fileNode.routeIds || []), routeNode.id]);
          }
        }
      }
      continue;
    }

    if (isConfigFile(file.rel, file.ext)) {
      fileNode.tags = uniq([...fileNode.tags, ...tagFromText(file.rel, content), 'config']);
      fileNode.technicalKinds = technicalKindsForNode(fileNode.type, file.rel, fileNode.tags, {
        isEntryPoint: fileNode.isEntryPoint,
      });
      continue;
    }
  }

  // Bước 3: enrich nodes bằng adjacency / risk / notes.
  const routeNodeIndex = new Map();
  for (const node of nodesById.values()) {
    if (node.type !== 'api_route') continue;
    const key = `${String(node.httpMethod || 'GET').toUpperCase()} ${node.routePath || node.label}`;
    routeNodeIndex.set(key, node.id);
    if (!routeNodeIndex.has(`ANY ${node.routePath || node.label}`)) {
      routeNodeIndex.set(`ANY ${node.routePath || node.label}`, node.id);
    }
  }
  for (const edge of pendingJsApiEdges) {
    const directKey = `${edge.httpMethod} ${edge.routePath}`;
    const fallbackKey = `ANY ${edge.routePath}`;
    const targetId = routeNodeIndex.get(directKey) || routeNodeIndex.get(fallbackKey);
    if (targetId) {
      addEdge(edges, edgeKeys, edge.sourceId, targetId, 'calls', 'calls API');
    }
  }

  // Bước 4: enrich nodes bằng adjacency / risk / notes.
  const nodes = [...nodesById.values()];
  const outgoingByNode = new Map();
  const incomingByNode = new Map();

  for (const node of nodes) {
    outgoingByNode.set(node.id, []);
    incomingByNode.set(node.id, []);
  }
  for (const edge of edges) {
    if (!outgoingByNode.has(edge.source)) outgoingByNode.set(edge.source, []);
    if (!incomingByNode.has(edge.target)) incomingByNode.set(edge.target, []);
    outgoingByNode.get(edge.source).push(edge);
    incomingByNode.get(edge.target).push(edge);
  }

  for (const node of nodes) {
    const outgoing = outgoingByNode.get(node.id) || [];
    const incoming = incomingByNode.get(node.id) || [];
    const relatedEdgeSet = outgoing.concat(incoming).filter((edge) => VIEW_RELEVANT_EDGE_TYPES.has(edge.type));
    const calls = uniq(
      outgoing
        .filter((edge) => VIEW_RELEVANT_EDGE_TYPES.has(edge.type))
        .map((edge) => edge.target),
    );
    const calledBy = uniq(
      incoming
        .filter((edge) => VIEW_RELEVANT_EDGE_TYPES.has(edge.type))
        .map((edge) => edge.source),
    );
    const relatedFiles = uniq(
      relatedEdgeSet
        .map((edge) => {
          const otherId = edge.source === node.id ? edge.target : edge.source;
          const targetNode = nodesById.get(otherId);
          if (!targetNode) return null;
          return ['file', 'config', 'component', 'style'].includes(targetNode.type) ? targetNode.id : targetNode.parentId || null;
        })
        .filter(Boolean),
    );

    node.calls = calls;
    node.calledBy = calledBy;
    node.relatedFiles = relatedFiles;
    node.dependencyCount = outgoing.filter((edge) => VIEW_RELEVANT_EDGE_TYPES.has(edge.type)).length;
    node.dependentCount = incoming.filter((edge) => VIEW_RELEVANT_EDGE_TYPES.has(edge.type)).length;
    node.hasManyDependencies = node.dependencyCount >= 6;
    node.isOrphan = outgoing.length + incoming.length === 0;
    node.isSecurityRelated = node.isSecurityRelated || node.tags.includes('security') || node.tags.includes('auth');
    node.isDatabaseRelated = node.isDatabaseRelated || node.tags.includes('database');
    node.riskLevel = computeRisk(node, outgoing, incoming);
    node.description = node.description || enrichDescriptions(node);
    node.learningNotes = buildLearningNotes(node);
    node.suggestedTests = buildSuggestedTests(node);
    node.securityNotes = buildSecurityNotes(node);
  }

  const payload = {
    nodes: nodes.map((node) => ({ data: node })),
    edges: edges.map((edge) => ({ data: edge })),
    meta: {
      scannedRoot: rootNorm,
      generatedAt: new Date().toISOString(),
      fileCount: files.length,
      nodeCount: nodes.length,
      edgeCount: edges.length,
      overview: buildOverview(nodes, edges),
      graphVersion: 2,
    },
  };

  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, JSON.stringify(payload, null, 2), 'utf8');
  console.log(`OK: ${nodes.length} nodes, ${edges.length} edges -> ${out}`);
}

main();
