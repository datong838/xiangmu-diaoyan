import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const base = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.resolve(base, '../专业群AI工作站方案文档地图.html');
const dataPath = path.resolve(base, '文档图谱数据.json');
const html = fs.readFileSync(htmlPath, 'utf8');
const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const ids = new Set(data.nodes.map(n => n.id));
const checks = {
  selfContainedData: html.includes('<script id="data" type="application/json">') && !html.includes('__PG_DATA__'),
  uniqueIds: ids.size === data.nodes.length,
  eightPrimaryGroups: data.groups.length === 8,
  everyNodeClassified: data.nodes.every(n => n.group && n.sub && n.role && n.status),
  everyGroupUsed: data.groups.every(g => data.nodes.some(n => n.group === g.id)),
  edgeEndpoints: data.edges.every(e => ids.has(e.source) && ids.has(e.target)),
  deepLinkRoute: html.includes("h.has('doc')"),
  searchControl: html.includes('id="search"') && html.includes('function results()'),
  treeControls: ['id="level"', 'id="collapse"', 'id="expand"', 'id="reset"'].every(x => html.includes(x)),
  relationView: html.includes('id="graph-mode"') && html.includes('function renderGraph()'),
  themeControl: html.includes('id="theme"'),
  reviewBoundary: html.includes('待评审 · 未冻结 · 未授权继续编码'),
};
const result = {ok: Object.values(checks).every(Boolean), checks, stats: data.stats};
fs.writeFileSync(path.resolve(base, '静态交互核查结果.json'), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result));
process.exit(result.ok ? 0 : 1);
