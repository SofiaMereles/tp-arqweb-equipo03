import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { hostname, userInfo } from 'node:os';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { parse } from 'yaml';
import { Parser } from '@asyncapi/parser';
import Ajv2020 from 'ajv/dist/2020.js';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const require = createRequire(import.meta.url);
const root = dirname(fileURLToPath(import.meta.url));
const evidence = resolve(root, '../docs/evidencias/fase5/a3');
const files = ['search-svc', 'audit-svc', 'export-svc', 'media-svc', 'event-bridge'];
const report = {
  evidence: 'F5-E4', test: 'P29', generated_at: new Date().toISOString(),
  host: hostname(), user: userInfo().username, node: process.version,
  results: [], errors: [],
};
let exampleCount = 0;
let rejectionCount = 0;

function check(condition, message) {
  if (!condition) report.errors.push(message);
}

function follow(document, schema) {
  if (!schema?.$ref) return schema;
  const path = schema.$ref.split('/').slice(1);
  return path.reduce((node, key) => node[key.replaceAll('~1', '/').replaceAll('~0', '~')], document);
}

function exampleValidator(document, dialect) {
  const ajv = dialect === 'openapi'
    ? new Ajv2020({ strict: false, allErrors: true })
    : new Ajv({ strict: false, allErrors: true });
  addFormats(ajv);
  ajv.addFormat('binary', true);
  // Un solo documento raíz conserva referencias a components/schemas.
  ajv.addSchema({ ...document, $id: 'urn:bookstack:contract' });
  return (schema, value, location, shouldAccept = true) => {
    try {
      // Mover el schema al mismo documento raíz evita resolver referencias contra un fragmento aislado.
      const rootSchema = { $id: 'urn:bookstack:example', components: document.components, ...schema };
      ajv.removeSchema('urn:bookstack:example');
      const validate = ajv.compile(rootSchema);
      const valid = validate(value);
      check(valid === shouldAccept, `${location}: ${shouldAccept ? ajv.errorsText(validate.errors) : 'aceptó una entrada inválida'}`);
      if (shouldAccept) exampleCount += 1;
      else rejectionCount += 1;
    } catch (error) {
      report.errors.push(`${location}: ${error.message}`);
    }
  };
}

async function load(filename) {
  const raw = await readFile(resolve(root, filename), 'utf8');
  return { document: parse(raw), sha256: createHash('sha256').update(raw).digest('hex') };
}

function validateHttpExamples(document, filename) {
  const validate = exampleValidator(document, 'openapi');
  for (const [path, item] of Object.entries(document.paths)) {
    for (const [method, operation] of Object.entries(item)) {
      if (!['get', 'post', 'put', 'patch', 'delete'].includes(method)) continue;
      check(Boolean(operation.operationId && operation.description), `${filename}: operación incompleta ${path}`);
      for (const param of operation.parameters ?? []) {
        if (Object.hasOwn(param, 'example')) {
          validate(param.schema, param.example, `${filename} ${path} parámetro ${param.name}`);
        }
      }
      const bodies = [operation.requestBody, ...Object.values(operation.responses)];
      for (const body of bodies) {
        for (const [type, content] of Object.entries(body?.content ?? {})) {
          for (const [name, example] of Object.entries(content.examples ?? {})) {
            validate(content.schema, example.value, `${filename} ${method} ${path} ${type} ${name}`);
          }
        }
        for (const [name, header] of Object.entries(body?.headers ?? {})) {
          if (Object.hasOwn(header, 'example')) validate(header.schema, header.example, `${filename} cabecera ${name}`);
        }
      }
      if (path.startsWith('/v2/')) {
        check(Boolean(operation.responses['400'] && operation.responses['503']),
          `${filename} ${path}: faltan respuestas 400/503`);
        check(operation.parameters?.some(p => p.name === 'X-Request-ID'),
          `${filename} ${path}: falta correlación HTTP`);
      }
    }
  }
}

await mkdir(evidence, { recursive: true });
console.log(`F5-E4 / P29 — ${report.generated_at}`);
console.log(`Usuario: ${report.user}. Nodo: ${report.host}. Node: ${report.node}`);
for (const service of files) {
  const filename = `${service}.openapi.yaml`;
  const { document, sha256 } = await load(filename);
  check(document.openapi === '3.1.0', `${filename}: se requiere OpenAPI 3.1.0`);
  const result = spawnSync(process.execPath, [
    require.resolve('@stoplight/spectral-cli/dist/index.js'), 'lint', filename,
    '--ruleset', '.spectral.yaml', '--format', 'json', '--fail-severity', 'warn', '--quiet',
  ], { cwd: root, encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
  let diagnostics = [];
  try { diagnostics = JSON.parse(result.stdout || '[]'); }
  catch { report.errors.push(`${filename}: salida de Spectral inválida: ${result.stdout} ${result.stderr}`); }
  check(!result.error && result.status === 0, `${filename}: Spectral falló ${result.error?.message ?? result.stderr}`);
  validateHttpExamples(document, filename);
  if (service === 'export-svc') {
    const validate = exampleValidator(document, 'openapi');
    validate(document.components.schemas.ExportRequest, { page_id: 42, book_id: 7, format: 'pdf' },
      'ExportRequest rechaza dos orígenes', false);
    validate(document.components.schemas.ExportRequest, { format: 'pdf' },
      'ExportRequest exige un origen', false);
    validate(document.components.schemas.ExportRequest, { page_id: 42, format: 'exe' },
      'ExportRequest rechaza formato desconocido', false);
    const queued = document.paths['/v2/exports'].post.responses['202'].content['application/json'].examples.example.value;
    validate(document.components.schemas.ExportJob, { ...queued, state: 'done' },
      'ExportJob done exige archivo', false);
    validate(document.components.schemas.ExportJob, { ...queued, state: 'failed' },
      'ExportJob failed exige causa', false);
  }
  report.results.push({ file: filename, sha256, tool: 'Spectral', exit_code: result.status, diagnostics });
  console.log(`${filename}: ${result.status === 0 ? 'PASS' : 'FAIL'} — Spectral, ${diagnostics.length} diagnósticos`);
}

const filename = 'bookstack.asyncapi.yaml';
const { document: events, sha256 } = await load(filename);
const parsed = await new Parser().parse(events);
const diagnostics = parsed.diagnostics ?? [];
check(Boolean(parsed.document), 'AsyncAPI: no se pudo interpretar el contrato');
check(diagnostics.every(d => d.severity > 1), 'AsyncAPI: hay errores o advertencias');
check(events.asyncapi === '3.0.0', 'Se requiere AsyncAPI 3.0.0');
const channels = Object.values(events.channels).map(channel => channel.address);
for (const channel of ['bookstack.page.created', 'bookstack.page.updated', 'bookstack.page.deleted',
  'export.requested', 'export.completed', 'media.uploaded']) {
  check(channels.includes(channel), `Falta el canal ${channel}`);
}
const envelope = events.components.schemas.EventEnvelope;
for (const field of ['event_id', 'type', 'version', 'occurred_at', 'request_id', 'payload']) {
  check(envelope.required.includes(field), `El sobre no exige ${field}`);
}
const validateEvent = exampleValidator(events, 'asyncapi');
for (const [name, message] of Object.entries(events.components.messages)) {
  const schema = follow(events, message.payload);
  for (const example of message.examples ?? []) {
    validateEvent(schema, example.payload, `AsyncAPI ${name}`);
  }
}
const sample = events.components.messages.PageUpdated.examples[0].payload;
const sampleSchema = follow(events, events.components.messages.PageUpdated.payload);
const withoutId = structuredClone(sample);
delete withoutId.request_id;
validateEvent(sampleSchema, withoutId, 'El evento exige request_id', false);
validateEvent(sampleSchema, { ...sample, event_id: 'invalido' }, 'El evento exige UUID', false);
validateEvent(sampleSchema, { ...sample, version: '2.0' }, 'El consumidor v1 rechaza versión incompatible', false);
validateEvent(sampleSchema, { ...sample, type: 'bookstack.page.deleted' }, 'El canal exige el tipo correcto', false);
const exampleIds = Object.values(events.components.messages).map(message => message.examples[0].payload.event_id);
check(new Set(exampleIds).size === exampleIds.length, 'Los ejemplos de hechos distintos deben tener UUID distintos');
report.results.push({ file: filename, sha256, tool: '@asyncapi/parser', diagnostics });
console.log(`${filename}: ${parsed.document && diagnostics.every(d => d.severity > 1) ? 'PASS' : 'FAIL'} — AsyncAPI, ${diagnostics.filter(d => d.severity === 0).length} errores, ${diagnostics.filter(d => d.severity === 1).length} advertencias, ${diagnostics.filter(d => d.severity === 2).length} info`);
report.examples_checked = exampleCount;
report.invalid_inputs_rejected = rejectionCount;
report.tool_versions = {};
for (const tool of ['@stoplight/spectral-cli', '@asyncapi/parser', 'ajv', 'ajv-formats', 'yaml']) {
  report.tool_versions[tool] = JSON.parse(await readFile(resolve(root, 'node_modules', tool, 'package.json'), 'utf8')).version;
}
report.status = report.errors.length ? 'FAIL' : 'PASS';
await writeFile(resolve(evidence, 'validation-report.json'), JSON.stringify(report, null, 2) + '\n');
const summary = [
  `F5-E4 / P29 — ${report.status}`, `Fecha UTC: ${report.generated_at}`,
  `Nodo: ${report.host}`, `Usuario: ${report.user}`, `Node: ${report.node}`,
  `Herramientas: ${JSON.stringify(report.tool_versions)}`,
  ...report.results.map(r => `${r.file}: ${r.tool} — ${r.diagnostics.length} diagnósticos; SHA256 ${r.sha256}`),
  `Ejemplos comprobados contra sus esquemas: ${exampleCount}`,
  `Entradas inválidas rechazadas según lo esperado: ${rejectionCount}`,
  `Errores: ${report.errors.length}`, ...report.errors,
].join('\n') + '\n';
await writeFile(resolve(evidence, 'validation-summary.txt'), summary);
console.log(`Ejemplos: ${exampleCount}. Rechazos verificados: ${rejectionCount}. Errores: ${report.errors.length}. Resultado: ${report.status}`);
for (const error of report.errors) console.error(error);
process.exitCode = report.errors.length ? 1 : 0;
