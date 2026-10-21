import fs from 'node:fs';import vm from 'node:vm';import path from 'node:path';import assert from 'node:assert/strict';import{fileURLToPath}from'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(dir),html=fs.readFileSync(path.join(root,'CAD方案文档地图.html'),'utf8'),data=JSON.parse(html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1]),code=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];new vm.Script(code);
const els=new Map();function el(id){if(!els.has(id))els.set(id,{value:'',checked:false,hidden:false,innerHTML:'',textContent:id==='data'?JSON.stringify(data):'',style:{},offsetWidth:900,offsetHeight:600,clientWidth:1100,clientHeight:650,classList:{toggle(){},add(){},remove(){}},querySelectorAll(){return[]},getBoundingClientRect(){return{left:0,top:0,right:224,height:67}},setAttribute(){}});return els.get(id)}
const context=vm.createContext({document:{getElementById:el,querySelectorAll(){return[]},querySelector(){return null}},requestAnimationFrame(){},location:{hash:'',protocol:'file:'},setTimeout(){},clearTimeout(){},console,URLSearchParams,getComputedStyle(){return{getPropertyValue(){return'#446be7'}}}});vm.runInContext(code.split("$('revision').textContent")[0],context);const run=s=>vm.runInContext(s,context);const checks=[];function test(n,fn){fn();checks.push({name:n,passed:true})}
test('脚本语法有效',()=>assert.ok(code.length));test('稳定ID唯一',()=>assert.equal(new Set(data.nodes.map(n=>n.id)).size,data.nodes.length));test('每个节点主树恰有一个位置',()=>assert.equal(run('total(tree)'),data.nodes.length));test('全部关系端点存在',()=>{const ids=new Set(data.nodes.map(n=>n.id));assert.ok(data.edges.every(e=>ids.has(e.source)&&ids.has(e.target)))});
test('初始视图只有九个分类分支',()=>{const h=run('folderHTML(tree)');assert.equal((h.match(/data-folder=/g)||[]).length,10);assert.ok(!h.includes('data-doc='))});
const wiki=data.nodes.find(n=>n.path.endsWith('28-持续知识编译与工程Wiki设计.md'));assert.ok(wiki);test('Wiki按长期设计归类',()=>assert.equal(wiki.group,'knowledge'));
for(const number of ['16','18','20','22','24'])test(number+'实验设计不混入长期设计',()=>assert.equal(data.nodes.find(n=>n.path.match(new RegExp('/'+number+'-'))).sub,'kbplan'));
test('五对方案和结果有明确编排关系',()=>assert.equal(data.edges.filter(e=>e.kind.startsWith('实验方案')).length,5));
test('展开祖先可定位Wiki节点',()=>{run(`let p=parents.get(${JSON.stringify(wiki.id)});while(p){state.open.add(p);p=parents.get(p)}`);assert.ok(run('folderHTML(tree)').includes(wiki.id))});
test('选择节点写入稳定深链',()=>{run(`choose(${JSON.stringify(wiki.id)},false)`);assert.equal(context.location.hash,'doc='+wiki.id)});
test('标题搜索',()=>{el('search').value='持续知识编译';run('results()');assert.ok(el('search-results').innerHTML.includes(wiki.id))});
test('正文搜索独立开关',()=>{el('search').value='SCOPED_VALIDATED';el('fulltext').checked=true;run('results()');assert.ok(el('search-results').innerHTML.includes(wiki.id))});
test('搜索不存在项显示缺口',()=>{el('search').value='absolutely-no-cad-term-xyz';run('results()');assert.ok(el('search-results').innerHTML.includes('没有匹配'))});
test('预览渲染不执行源HTML',()=>assert.ok(data.nodes.every(n=>!/<script\b|<iframe\b|<img\b/i.test(n.preview_html))));
test('模板无残留MES入口',()=>assert.ok(!html.split('<script id="data"')[0].includes('新MES')&&!code.includes('01-知识库建设路线.md')));
test('所有源入口当前存在',()=>assert.ok(data.nodes.every(n=>fs.existsSync(n.source_path))));
test('附件类型显示为材料入口',()=>assert.ok(data.nodes.filter(n=>n.source_kind!=='markdown').every(n=>n.body.includes('未解析或核准'))));
test('离线原文件链接使用相对路径',()=>assert.ok(data.nodes.every(n=>!n.href.startsWith('http')&&!n.href.startsWith('/'))));
test('局部关系图可生成',()=>{run('renderGraph()');assert.ok(el('map').innerHTML.includes('graph-center'))});
test('浅深主题与缩放入口存在',()=>assert.ok(code.includes('cad-doc-theme')&&code.includes('Math.max(.45')));
const receipt={ok:true,checks,notes:'纯数据和函数检查，不替代浏览器视觉交互验证',nodes:data.nodes.length};fs.writeFileSync(path.join(dir,'静态交互核查结果.json'),JSON.stringify(receipt,null,2));console.log(JSON.stringify({ok:true,tests:checks.length,nodes:data.nodes.length}));
