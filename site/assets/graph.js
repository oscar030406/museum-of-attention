/* 注意力博物馆 · 知识图谱页
   交互参照 codebase-memory-mcp 的 3D 图谱：左边按节点和边的类型筛选，选中一个节点后按层展开邻居。
   渲染用站内打包的 3d-force-graph（assets/vendor/graph3d.min.js），图谱数据是 museum.json 的 graph 字段。
   依赖 app.js 的全局：D、lang、t、esc、$、byId、EN、txt、mechHtml、srcMark、miss、hallName。 */
"use strict";

Object.assign(I18N.zh, {
  "nav.graph": "关系图",
  gTitle: "关系图", gLede: "展品和它们共有的展厅、收集方向、发表地点和仓库连在一起。拖动旋转，滚轮缩放，点一个点看和它相连的。",
  gNodes: "个点", gEdges: "条线", gFilters: "筛选", gAll: "全选", gNone: "全不选",
  gShowLabels: "显示名字", gLayers: "展开几层", gFlat: "压平", gBloom: "发光", gFit: "看全图",
  gSearch: "搜展品、展厅、仓库", gHalls: "展厅", gColor: "展品的颜色是代码来源",
  gLoading: "正在画图……", gFail: "关系图没画出来，这台设备可能不支持 WebGL。谱系页和展品页有同样的内容。",
  gOpen: "看展签", gToGallery: "在展品页看", gNeighbors: n => `相连的有 ${n} 个`, gClear: "取消选中",
  gPanel: "筛选",
  kind: { exhibit: "展品", hall: "展厅", direction: "收集方向", venue: "发表地点", repo: "仓库", year: "年份" },
  lkind: { hall: "在哪个展厅", direction: "哪个方向", venue: "发表在", repo: "同一个仓库", paper: "同一篇论文", lineage: "谱系", year: "论文年份" },
});
Object.assign(I18N.en, {
  "nav.graph": "Connections",
  gTitle: "Connections", gLede: "Each object, joined to the galleries, collecting themes, venues and repositories it shares with others. Drag to turn, scroll to zoom, click a point to see what it connects to.",
  gNodes: "points", gEdges: "lines", gFilters: "Filters", gAll: "All", gNone: "None",
  gShowLabels: "Show names", gLayers: "Depth", gFlat: "Flatten", gBloom: "Glow", gFit: "Show all",
  gSearch: "Search objects, galleries, repos", gHalls: "Galleries", gColor: "Object color shows the code source",
  gLoading: "Drawing…", gFail: "The map did not load. This device may not support WebGL. The lineage and objects pages show the same things.",
  gOpen: "Open label", gToGallery: "See on the objects page", gNeighbors: n => `${n} connected`, gClear: "Clear selection",
  gPanel: "Filters",
  kind: { exhibit: "Objects", hall: "Galleries", direction: "Collecting themes", venue: "Venues", repo: "Repositories", year: "Years" },
  lkind: { hall: "Gallery", direction: "Theme", venue: "Published in", repo: "Same repository", paper: "Same paper", lineage: "Lineage", year: "Paper year" },
});

// 画布始终是深色（像天象厅），所以这里用参考调色板的深色档
const G_COLORS = {
  src: { author: "#3987e5", port: "#d95926", repro: "#199e70", third: "#8f8e88", unknown: "#6e6d69" },
  pending: "#7a5a3a",
  hall: "#f0efec", direction: "#d55181", venue: "#c98500", repo: "#9085e9", year: "#0ca30c",
  link: { hall: "#5598e7", direction: "#d55181", venue: "#c98500", repo: "#9085e9", paper: "#1baf7a", lineage: "#ff8a6b", year: "#0ca30c" },
  dim: "#24272c",
};
const NODE_KINDS = ["exhibit", "hall", "direction", "venue", "repo", "year"];
const LINK_KINDS = ["hall", "direction", "venue", "repo", "paper", "lineage", "year"];
const gState = {
  nodeOn: new Set(["exhibit", "hall", "direction", "venue", "repo"]),
  linkOn: new Set(["hall", "direction", "venue", "repo", "paper", "lineage"]),
  labels: true, layers: 1, flat: false, bloom: true, focus: null, focusSet: null,
};
let G = null;              // ForceGraph3D 实例
let gBloomPass = null;
let gRaf = 0;
let gFitted = false;

function loadGraphLib() {
  if (window.MuseumGraph3D) return Promise.resolve(window.MuseumGraph3D);
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "assets/vendor/graph3d.min.js";
    s.onload = () => resolve(window.MuseumGraph3D);
    s.onerror = () => reject(new Error("graph3d.min.js"));
    document.head.appendChild(s);
  });
}
function webglOk() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch (e) { return false; }
}
function gLabel(n) {
  if (n.kind === "exhibit") return n.label;
  return EN() ? (n.label_en || n.label) : n.label;
}
function gZh(n) { return EN() ? "" : n.label_zh || ""; }
function nodeColorOf(n) {
  if (n.kind !== "exhibit") return G_COLORS[n.kind];
  if (n.status !== "collected") return G_COLORS.pending;
  return G_COLORS.src[n.src || "unknown"];
}

// 当前筛选下的图（3d-force-graph 会改写 link 的 source/target 为对象，所以每次都新建）
function visibleGraph() {
  const nodes = D.graph.nodes.filter(n => gState.nodeOn.has(n.kind));
  const ids = new Set(nodes.map(n => n.id));
  const links = D.graph.links
    .filter(l => gState.linkOn.has(l.kind) && ids.has(l.source) && ids.has(l.target))
    .map(l => ({ ...l }));
  return { nodes: nodes.map(n => ({ ...n })), links };
}
function adjacency(links) {
  const adj = new Map();
  for (const l of links) {
    const a = typeof l.source === "object" ? l.source.id : l.source, b = typeof l.target === "object" ? l.target.id : l.target;
    if (!adj.has(a)) adj.set(a, new Set()); if (!adj.has(b)) adj.set(b, new Set());
    adj.get(a).add(b); adj.get(b).add(a);
  }
  return adj;
}
function neighborhood(id, k, adj) {
  const dist = new Map([[id, 0]]); let frontier = [id];
  for (let d = 1; d <= k; d++) {
    const next = [];
    for (const x of frontier) for (const y of adj.get(x) || []) if (!dist.has(y)) { dist.set(y, d); next.push(y); }
    frontier = next;
  }
  return dist;
}

// 关系图页有两种看法。总图是默认的：平面，横轴年份，纵向分展室，一件展品一个点。星团是原来的 3D 图。
let gView = "map";
let ovCleanup = null;
function viewSwitch() {
  const lab = EN() ? { map: "Map", star: "Constellation", aria: "Ways to view" } : { map: "总图", star: "星团", aria: "看法" };
  return `<div class="view-switch" role="group" aria-label="${lab.aria}">${["map", "star"].map(v => `<button type="button" data-view="${v}" aria-pressed="${gView === v}">${lab[v]}</button>`).join("")}</div>`;
}
function wireViewSwitch() {
  document.querySelectorAll(".view-switch button").forEach(b => b.addEventListener("click", () => {
    if (b.dataset.view === gView) return;
    gView = b.dataset.view;
    graphCleanup();
    renderGraph();
  }));
}
async function renderGraph() {
  if (gView === "star") {
    renderStar();
    document.querySelector(".gpanel")?.insertAdjacentHTML("afterbegin", viewSwitch());
    wireViewSwitch();
    return;
  }
  if (!document.getElementById("overview-css")) document.head.insertAdjacentHTML("beforeend", '<link id="overview-css" rel="stylesheet" href="assets/overview.css">');
  main().innerHTML = `
  <header class="page-head map-head">
    <div><h1>${EN() ? "The whole collection" : "全馆一览"}</h1>
    <p>${EN() ? "Each dot is one exhibit. Read across for years and down for rooms. Rest on a dot to see what it built on, what built on it, and what it cites." : "一个点是一件展品。横着看是年份，竖着看是展室。把鼠标停在一个点上，会连出它的前作、后作和它引用的论文。"}</p></div>
    ${viewSwitch()}
  </header>
  <div id="ov-host"></div>`;
  wireViewSwitch();
  const host = document.getElementById("ov-host");
  try {
    const mod = await import("./overview.js");
    if (!document.body.contains(host) || gView !== "map") return;
    ovCleanup = mod.mountOverview(host, D, { lang: EN() ? "en" : "zh", exhibitHref: e => `#/x/${encodeURIComponent(e.id)}` });
  } catch (err) { host.textContent = String(err); }
}
function renderStar() {
  const kindCount = k => D.graph.nodes.filter(n => n.kind === k).length;
  const linkCount = k => D.graph.links.filter(l => l.kind === k).length;
  const chip = (set, k, label, n, color) => `<button type="button" class="gchip" data-set="${set}" data-k="${k}" aria-pressed="${(set === "n" ? gState.nodeOn : gState.linkOn).has(k)}"><i style="background:${color}"></i>${esc(label)}<span>${n}</span></button>`;
  main().innerHTML = `
  <div class="gpage">
    <aside class="gpanel" id="gpanel" aria-label="${esc(t("gPanel"))}">
      <h1 class="gtitle">${esc(t("gTitle"))}</h1>
      <p class="glede">${esc(t("gLede"))}</p>
      <p class="gcount" id="gcount"></p>
      <div class="gsec"><div class="gsec-h">${esc(t("gNodes"))}<span><button type="button" data-bulk="n-all">${esc(t("gAll"))}</button> | <button type="button" data-bulk="n-none">${esc(t("gNone"))}</button></span></div>
        <div class="gchips">${NODE_KINDS.map(k => chip("n", k, t("kind")[k], kindCount(k), k === "exhibit" ? G_COLORS.src.author : G_COLORS[k])).join("")}</div>
        <div class="glegend">${esc(t("gColor"))}：${["author", "port", "repro", "third", "unknown"].map(k => `<span><i style="background:${G_COLORS.src[k]}"></i>${esc(t("srcName")[k])}</span>`).join("")}<span><i style="background:${G_COLORS.pending}"></i>${esc(t("statusName").pending)}</span></div></div>
      <div class="gsec"><div class="gsec-h">${esc(t("gEdges"))}<span><button type="button" data-bulk="l-all">${esc(t("gAll"))}</button> | <button type="button" data-bulk="l-none">${esc(t("gNone"))}</button></span></div>
        <div class="gchips">${LINK_KINDS.map(k => chip("l", k, t("lkind")[k], linkCount(k), G_COLORS.link[k])).join("")}</div></div>
      <div class="gsec gopts">
        <label><input type="checkbox" id="g-labels" ${gState.labels ? "checked" : ""}> ${esc(t("gShowLabels"))}</label>
        <label><input type="checkbox" id="g-flat" ${gState.flat ? "checked" : ""}> ${esc(t("gFlat"))}</label>
        <label><input type="checkbox" id="g-bloom" ${gState.bloom ? "checked" : ""}> ${esc(t("gBloom"))}</label>
        <label>${esc(t("gLayers"))} <select id="g-layers">${[1, 2, 3].map(k => `<option ${k === gState.layers ? "selected" : ""}>${k}</option>`).join("")}</select></label>
      </div>
      <div class="gsec gsearch"><input id="g-q" type="search" placeholder="${esc(t("gSearch"))}" aria-label="${esc(t("gSearch"))}" autocomplete="off"><ul id="g-hits" role="listbox"></ul></div>
      <div class="gsec"><div class="gsec-h">${esc(t("gHalls"))}</div>
        <ul class="gtree">${D.halls.fields.map(f => {
          const id = `hall:${f.field}`;
          return `<li><button type="button" data-focus="${esc(id)}">${esc(hallName(f.field))}<span>${f.count}</span></button></li>` +
            f.tasks.map(tk => `<li class="sub"><button type="button" data-focus="${esc(id + "/" + tk.task)}">${esc(hallName(f.field, tk.task))}<span>${tk.count}</span></button></li>`).join("");
        }).join("")}</ul></div>
    </aside>
    <section class="gstage" id="gstage">
      <div id="g-canvas" class="gcanvas"><p class="gmsg">${esc(t("gLoading"))}</p></div>
      <div id="g-labels-layer" class="glabels" aria-hidden="true"></div>
      <div class="gtools"><button type="button" class="gbtn gpanel-toggle" id="g-panel-btn">${esc(t("gFilters"))}</button><button type="button" class="gbtn" id="g-fit">${esc(t("gFit"))}</button></div>
      <div class="gcard" id="g-card" hidden></div>
    </section>
  </div>`;
  document.body.classList.add("on-graph");
  wireGraphPanel();
  bootGraph();
}

function wireGraphPanel() {
  const panel = $("#gpanel");
  panel.addEventListener("click", ev => {
    const c = ev.target.closest(".gchip");
    if (c) {
      const set = c.dataset.set === "n" ? gState.nodeOn : gState.linkOn;
      set.has(c.dataset.k) ? set.delete(c.dataset.k) : set.add(c.dataset.k);
      c.setAttribute("aria-pressed", set.has(c.dataset.k));
      refreshData();
      return;
    }
    const b = ev.target.closest("[data-bulk]");
    if (b) {
      const [which, mode] = b.dataset.bulk.split("-");
      const set = which === "n" ? gState.nodeOn : gState.linkOn;
      const all = which === "n" ? NODE_KINDS : LINK_KINDS;
      set.clear(); if (mode === "all") all.forEach(k => set.add(k));
      panel.querySelectorAll(`.gchip[data-set="${which}"]`).forEach(x => x.setAttribute("aria-pressed", set.has(x.dataset.k)));
      refreshData();
      return;
    }
    const f = ev.target.closest("[data-focus]");
    if (f) { focusNode(f.dataset.focus, true); if (innerWidth < 900) panel.classList.remove("open"); }
  });
  $("#g-labels").addEventListener("change", ev => { gState.labels = ev.target.checked; });
  $("#g-flat").addEventListener("change", ev => { gState.flat = ev.target.checked; if (G) G.numDimensions(gState.flat ? 2 : 3); });
  $("#g-bloom").addEventListener("change", ev => { gState.bloom = ev.target.checked; if (gBloomPass) gBloomPass.enabled = gState.bloom; });
  $("#g-layers").addEventListener("change", ev => { gState.layers = +ev.target.value; if (gState.focus) focusNode(gState.focus, false); });
  $("#g-fit").addEventListener("click", () => { clearFocus(); fitAll(600); });
  $("#g-panel-btn").addEventListener("click", () => panel.classList.toggle("open"));
  const q = $("#g-q"), hits = $("#g-hits");
  q.addEventListener("input", () => {
    const s = q.value.trim().toLowerCase();
    if (!s) { hits.innerHTML = ""; return; }
    const res = D.graph.nodes.filter(n => [n.label, n.label_en, n.label_zh].some(x => x && x.toLowerCase().includes(s)))
      .sort((a, b) => (a.label.toLowerCase().startsWith(s) ? 0 : 1) - (b.label.toLowerCase().startsWith(s) ? 0 : 1) || a.label.length - b.label.length).slice(0, 8);
    hits.innerHTML = res.map(n => `<li><button type="button" data-focus="${esc(n.id)}"><i style="background:${nodeColorOf(n)}"></i>${esc(gLabel(n))}<small>${esc(t("kind")[n.kind])}${gZh(n) ? " · " + esc(gZh(n)) : ""}</small></button></li>`).join("");
  });
  hits.addEventListener("click", () => { q.value = ""; hits.innerHTML = ""; });
}

async function bootGraph() {
  const box = $("#g-canvas");
  if (!webglOk()) { box.innerHTML = `<p class="gmsg">${esc(t("gFail"))}</p>`; return; }
  let lib;
  try { lib = await loadGraphLib(); } catch (e) { box.innerHTML = `<p class="gmsg">${esc(t("gFail"))}</p>`; console.error(e); return; }
  if (!document.getElementById("g-canvas")) return;          // 加载期间已离开本页
  box.innerHTML = "";
  const { ForceGraph3D, UnrealBloomPass, OutputPass, Vector2 } = lib;
  const stage = $("#gstage");
  G = new ForceGraph3D(box, { controlType: "orbit" })
    .width(stage.clientWidth).height(stage.clientHeight)
    .backgroundColor("#010203")    // 后期处理链把背景色当线性值，#010203 实际显示为 rgb(13,22,28)
    .showNavInfo(false)
    .nodeId("id")
    .nodeVal(n => n.kind === "exhibit" ? (n.status === "collected" ? 1 : 0.6) : Math.max(3, Math.sqrt(n._deg || 1) * 1.5))
    .nodeRelSize(2.4)
    .nodeOpacity(0.95)
    .nodeResolution(10)
    .nodeColor(n => gState.focusSet && !gState.focusSet.has(n.id) ? G_COLORS.dim : nodeColorOf(n))
    .nodeLabel(n => `<div class="gtip"><b>${esc(gLabel(n))}</b>${gZh(n) ? `<br>${esc(gZh(n))}` : ""}<br><span>${esc(t("kind")[n.kind])}${n.year && n.kind === "exhibit" ? " · " + n.year : ""}</span></div>`)
    .linkColor(l => inFocus(l) ? G_COLORS.link[l.kind] : "#15181c")
    .linkOpacity(0.32)
    .linkWidth(l => l.kind === "lineage" ? 1.4 : 0)
    .linkDirectionalParticles(l => l.kind === "lineage" && inFocus(l) ? 3 : 0)
    .linkDirectionalParticleWidth(2.2)
    .linkDirectionalParticleSpeed(0.006)
    .linkDirectionalParticleColor(() => "#ffd2c4")
    .numDimensions(gState.flat ? 2 : 3)
    .warmupTicks(60)
    .cooldownTicks(160)
    .onEngineStop(() => { if (!gFitted) gFitted = fitAll(900); })
    .onNodeClick(n => focusNode(n.id, true))
    .onBackgroundClick(() => clearFocus());
  G.d3Force("charge").strength(n => n.kind === "exhibit" ? -18 : -90).distanceMax(260);
  G.d3Force("link").distance(l => l.kind === "lineage" || l.kind === "paper" ? 18 : 42).strength(l => l.kind === "year" || l.kind === "venue" ? 0.08 : 0.25);
  try {
    gBloomPass = new UnrealBloomPass(new Vector2(stage.clientWidth, stage.clientHeight), 0.9, 0.4, 0.3);
    gBloomPass.enabled = gState.bloom;
    G.postProcessingComposer().addPass(gBloomPass);
    G.postProcessingComposer().addPass(new OutputPass());   // 后期处理链末尾做色彩空间转换，否则底色发灰
  } catch (e) { console.warn("bloom off", e); gBloomPass = null; }
  gFitted = false;
  refreshData();
  G.cameraPosition({ x: 0, y: 0, z: 1500 });
  // 布局散开以后再对准全图。后台标签页里定时器会被浏览器放慢，所以一直等到对准为止，离开本页时清掉
  const fitTimer = setInterval(() => { if (gFitted || !G) return clearInterval(fitTimer); gFitted = fitAll(900); }, 1500);
  gCleanupHooks.push(() => clearInterval(fitTimer));
  const ro = new ResizeObserver(() => { if (G) { G.width(stage.clientWidth).height(stage.clientHeight); } });
  ro.observe(stage);
  gCleanupHooks.push(() => ro.disconnect());
  labelLoop();
}

function inFocus(l) {
  if (!gState.focusSet) return true;
  const a = l.source.id ?? l.source, b = l.target.id ?? l.target;
  return gState.focusSet.has(a) && gState.focusSet.has(b);
}

function fitAll(ms) {
  if (!G) return false;
  const b = G.getGraphBbox();
  if (!b) return false;
  const ext = Math.max(b.x[1] - b.x[0], b.y[1] - b.y[0], (b.z && b.z[1] - b.z[0]) || 0);
  if (ext < 120) return false;          // 节点还挤在原点附近，等它散开
  G.zoomToFit(ms, 40);
  return true;
}

function refreshData() {
  if (!G) return;
  const data = visibleGraph();
  const deg = new Map(); data.links.forEach(l => { deg.set(l.source, (deg.get(l.source) || 0) + 1); deg.set(l.target, (deg.get(l.target) || 0) + 1); });
  data.nodes.forEach(n => { n._deg = deg.get(n.id) || 0; });
  G.graphData(data);
  $("#gcount").textContent = `${data.nodes.length} ${t("gNodes")} · ${data.links.length} ${t("gEdges")}`;
  if (gState.focus && !data.nodes.some(n => n.id === gState.focus)) clearFocus();
  else if (gState.focus) focusNode(gState.focus, false);
}

function focusNode(id, fly) {
  if (!G) return;
  const data = G.graphData();
  const node = data.nodes.find(n => n.id === id);
  if (!node) {   // 节点被筛选隐藏了：先把它的类型打开
    const raw = D.graph.nodes.find(n => n.id === id); if (!raw) return;
    gState.nodeOn.add(raw.kind);
    document.querySelector(`.gchip[data-set="n"][data-k="${raw.kind}"]`)?.setAttribute("aria-pressed", "true");
    gState.focus = id; refreshData(); return;
  }
  const dist = neighborhood(id, gState.layers, adjacency(data.links));
  gState.focus = id; gState.focusSet = new Set(dist.keys()); gState.focusDist = dist;
  G.nodeColor(G.nodeColor()).linkColor(G.linkColor()).linkDirectionalParticles(G.linkDirectionalParticles());
  if (fly && node.x !== undefined) {
    const d = 120, r = Math.hypot(node.x, node.y, node.z || 0) || 1, k = 1 + d / r;
    G.cameraPosition({ x: node.x * k, y: node.y * k, z: (node.z || 0) * k + (gState.flat ? d : 0) }, node, 900);
  }
  showCard(node, dist.size - 1);
}
function clearFocus() {
  gState.focus = null; gState.focusSet = null; gState.focusDist = null;
  if (G) G.nodeColor(G.nodeColor()).linkColor(G.linkColor()).linkDirectionalParticles(G.linkDirectionalParticles());
  const c = $("#g-card"); if (c) c.hidden = true;
}
function showCard(n, nb) {
  const c = $("#g-card"); if (!c) return;
  let body = "", actions = "";
  if (n.kind === "exhibit") {
    const e = byId.get(n.id);
    body = `<div class="gcard-y">${e.year || "?"}${txt(e, "venue") ? " · " + esc(txt(e, "venue")) : ""}</div>
      <h2>${esc(e.name_en)}</h2>${gZh(n) ? `<div class="gcard-zh">${esc(e.name_zh)}</div>` : ""}
      ${txt(e, "title") ? `<p class="gcard-t">${esc(txt(e, "title"))}</p>` : ""}
      <p>${mechHtml(e)}</p>
      <div>${srcMark(e)}</div>`;
    actions = `<a class="btn" href="#/x/${encodeURIComponent(e.id)}">${esc(t("gOpen"))}</a>`;
  } else {
    body = `<div class="gcard-y">${esc(t("kind")[n.kind])}</div><h2>${esc(gLabel(n))}</h2>`;
    const href = n.kind === "hall" ? `#/gallery?hall=${encodeURIComponent(n.id.startsWith("hall:") && n.parent ? "t:" + n.id.slice(5) : "f:" + n.id.slice(5))}`
      : n.kind === "direction" ? `#/gallery?hall=${encodeURIComponent("d:" + n.id.slice(4))}`
      : n.kind === "year" ? `#/gallery?y0=${n.label}&y1=${n.label}`
      : `#/gallery?q=${encodeURIComponent(n.kind === "repo" ? n.label.split("/").pop() : n.label)}`;
    actions = `<a class="btn" href="${href}">${esc(t("gToGallery"))}</a>`;
  }
  c.innerHTML = `<button type="button" class="gcard-x" aria-label="${esc(t("gClear"))}">✕</button>${body}<p class="muted">${esc(t("gNeighbors", nb))}</p><div class="gcard-a">${actions}</div>`;
  c.hidden = false;
  c.querySelector(".gcard-x").addEventListener("click", clearFocus);
}

// 标签层：每帧把要显示的节点投影到屏幕，按优先级贪心放置，重叠的不画
function labelLoop() {
  const layer = $("#g-labels-layer");
  const pool = [];
  const tick = () => {
    gRaf = requestAnimationFrame(tick);
    if (!G || !layer.isConnected) return;
    const data = G.graphData();
    const cam = G.camera(); cam.updateMatrixWorld(); const m = cam.matrixWorldInverse.elements;
    const W = layer.clientWidth, H = layer.clientHeight;
    const cands = [];
    for (const n of data.nodes) {
      if (n.x === undefined) continue;
      let pri = -1;
      if (gState.focusSet) {
        if (gState.focusSet.has(n.id)) pri = 1000 - 100 * (gState.focusDist.get(n.id) || 0) + (n._deg || 0);
      } else if (gState.labels && n.kind !== "exhibit") {
        if (n.kind === "hall" || n.kind === "direction" || (n._deg || 0) >= 6) pri = 100 + (n._deg || 0);
      }
      if (pri < 0) continue;
      const z = m[2] * n.x + m[6] * n.y + m[10] * (n.z || 0) + m[14];
      if (z > 0) continue;                       // 在镜头背后
      const p = G.graph2ScreenCoords(n.x, n.y, n.z || 0);
      if (p.x < -50 || p.y < -20 || p.x > W + 50 || p.y > H + 20) continue;
      cands.push({ n, pri, x: p.x, y: p.y });
    }
    cands.sort((a, b) => b.pri - a.pri);
    const placed = []; let used = 0;
    for (const c of cands) {
      if (used >= 70) break;
      const text = gLabel(c.n);
      const cjk = (text.match(/[　-鿿＀-￯]/g) || []).length;
      const w = Math.min(220, cjk * 12.5 + (text.length - cjk) * 7 + 10), h = 18;   // 中文字约 12px 宽，西文约 7px
      const r = { x: c.x + 6, y: c.y - h - 2, w, h };
      if (placed.some(q => r.x < q.x + q.w && r.x + r.w > q.x && r.y < q.y + q.h && r.y + r.h > q.y)) continue;
      placed.push(r);
      let el = pool[used];
      if (!el) { el = document.createElement("span"); pool.push(el); layer.appendChild(el); }
      if (el.textContent !== text) el.textContent = text;
      el.className = "glabel k-" + c.n.kind + (gState.focus === c.n.id ? " sel" : "");
      el.style.transform = `translate(${r.x}px, ${r.y}px)`;
      el.style.display = "";
      used++;
    }
    for (let i = used; i < pool.length; i++) pool[i].style.display = "none";
  };
  tick();
}

const gCleanupHooks = [];
function graphCleanup() {
  if (ovCleanup) { ovCleanup(); ovCleanup = null; }
  cancelAnimationFrame(gRaf);
  while (gCleanupHooks.length) gCleanupHooks.pop()();
  if (G) { try { G.pauseAnimation(); G._destructor && G._destructor(); } catch (e) { /* 页面已切走 */ } }
  G = null; gBloomPass = null;
  gState.focus = null; gState.focusSet = null;
  document.body.classList.remove("on-graph");
}
