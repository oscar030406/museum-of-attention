export const strings = {
  zh: {
    museum: "注意力博物馆", title: "关系图", settings: "页面设置", language: "English",
    light: "浅色", dark: "深色", views: "看法", overview: "总图", star: "星团",
    starNote: "星团在正式站查看", loadError: "馆藏数据未能打开。请刷新页面。",
    grouping: "怎么分行", room: "按展室", field: "按领域", collectedOnly: "只看已收藏的",
    search: "找一件展品", next: "下一个", found: n => `找到 ${n} 件`, empty: "没有叫这个名字的",
    count: n => `${n} 件`, year: "年份", unknownYear: "年份不详", unknownVenue: "出处不详",
    other: "八室之外的线索", legend: "图例", collected: "已收藏", pending: "还没收", anchor: "导览里讲到的",
    lineage: "前作和后作", citation: "引用", total: "图上共",
  },
  en: {
    museum: "Museum of Attention", title: "Relationship map", settings: "Page settings", language: "简体中文",
    light: "Light", dark: "Dark", views: "Views", overview: "Overview", star: "Star cluster",
    starNote: "The star cluster is on the museum site", loadError: "The collection could not load. Refresh the page to try again.",
    grouping: "Rows", room: "By room", field: "By field", collectedOnly: "Held only",
    search: "Find an exhibit", next: "Next", found: n => `${n} found`, empty: "Nothing by that name",
    count: n => `${n} ${n === 1 ? "exhibit" : "exhibits"}`, year: "Year", unknownYear: "Year not recorded", unknownVenue: "Venue not recorded",
    other: "Lines outside the eight rooms", legend: "Key", collected: "Held", pending: "Not yet held", anchor: "On the tour",
    lineage: "Earlier and later versions", citation: "Cites", total: "On this map",
  },
};

const esc = value => String(value).replace(/[&<>"']/g, char =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const normalize = value => value.normalize("NFKC").toLowerCase();
const hasYear = year => Number.isInteger(year) && year >= 2014;
const other = "other";

function roomAssignments(exhibits, chapters) {
  const anchors = new Map();
  const profiles = chapters.map(chapter => {
    const anchorExhibits = chapter.anchors.map(({ id }) => exhibits.get(id)).filter(Boolean);
    for (const { id } of anchorExhibits) {
      if (!anchors.has(id)) anchors.set(id, chapter.id);
    }
    return { chapter, anchorExhibits };
  });

  function roomFor(exhibit) {
    const { id, year, halls } = exhibit;
    if (anchors.has(id)) return anchors.get(id);
    if (exhibit.room) return exhibit.room === "beyond" ? other : exhibit.room;
    if (!hasYear(year)) return other;

    const choices = [];
    for (const { chapter, anchorExhibits } of profiles) {
      const [start, end] = chapter.years;
      if (year < start || year > end) continue;
      const matches = anchorExhibits.filter(anchor =>
        halls.some(hall => anchor.halls.some(candidate => candidate.field === hall.field)));
      if (!matches.length) continue;
      const sameTask = matches.some(anchor => halls.some(hall => hall.task &&
        anchor.halls.some(candidate => candidate.field === hall.field && candidate.task === hall.task)));
      const distance = Math.min(...matches.filter(anchor => hasYear(anchor.year))
        .map(anchor => Math.abs(anchor.year - year)));
      choices.push({ row: chapter.id, sameTask, distance, count: matches.length });
    }
    choices.sort((a, b) => Number(b.sameTask) - Number(a.sameTask) || a.distance - b.distance || b.count - a.count);
    return choices[0]?.row ?? other;
  }

  return { anchors, rooms: new Map(Array.from(exhibits.values(), exhibit => [exhibit.id, roomFor(exhibit)])) };
}

function relationshipIndex(data, exhibits) {
  const links = new Map(Array.from(exhibits.keys(), id => [id, new Map()]));
  function add(source, target, kind) {
    if (source === target || !links.has(source) || !links.has(target)) return;
    links.get(source).set(target, kind);
    links.get(target).set(source, kind);
  }
  const { works, edges } = data.citation_graph;
  for (const { citing, cited } of edges) {
    for (const source of works[citing] || []) {
      for (const target of works[cited] || []) add(source, target, "citation");
    }
  }
  for (const { source, target } of data.edges) add(source, target, "lineage");
  return links;
}

export function mountOverview(host, data, { lang = "zh", exhibitHref }) {
  const words = strings[lang];
  const exhibits = new Map(data.exhibits.map(exhibit => [exhibit.id, exhibit]));
  const { chapters } = data.story;
  const { anchors, rooms } = roomAssignments(exhibits, chapters);
  const fields = new Set(data.halls.fields.map(({ field }) => field));
  const fieldFor = exhibit => exhibit.halls.find(({ field }) => fields.has(field))?.field ?? other;
  const rows = {
    room: chapters.map(chapter => [chapter.id, chapter[`title_${lang}`]]),
    field: data.halls.fields.map(({ field, en }) => [field, lang === "en" ? en : field]),
  };
  const byName = data.exhibits.map(exhibit => ({
    exhibit,
    names: [exhibit.name_en, exhibit.name_zh].filter(Boolean).map(normalize),
  }));
  const years = [];
  const latest = Math.max(...data.exhibits.map(exhibit => exhibit.year).filter(hasYear));
  for (let year = 2014; year <= latest; year++) years.push(year);
  if (data.exhibits.some(exhibit => !hasYear(exhibit.year))) years.push(null);
  const links = relationshipIndex(data, exhibits);
  const events = new AbortController();

  host.classList.add("overview-map");
  host.innerHTML = `
    <div class="ov-controls">
      <div class="ov-search">
        <input type="search" aria-label="${words.search}" placeholder="${words.search}" autocomplete="off">
        <button type="button" class="ov-next" hidden>${words.next}</button>
      </div>
      <div class="ov-options">
        <div class="ov-segment" role="group" aria-label="${words.grouping}">
          <button type="button" data-group="room" aria-pressed="true">${words.room}</button>
          <button type="button" data-group="field" aria-pressed="false">${words.field}</button>
        </div>
        <label class="ov-filter"><input type="checkbox"> ${words.collectedOnly}</label>
      </div>
      <span class="ov-results" role="status" hidden></span>
    </div>
    <div class="ov-key">
      <span class="ov-total"></span>
      <ul class="ov-legend" aria-label="${words.legend}">
        <li><i class="ov-key-dot"></i>${words.collected}</li>
        <li><i class="ov-key-dot ov-key-open"></i>${words.pending}</li>
        <li><i class="ov-key-dot ov-key-anchor"></i>${words.anchor}</li>
        <li><i class="ov-key-line"></i>${words.lineage}</li>
        <li><i class="ov-key-line ov-key-citation"></i>${words.citation}</li>
      </ul>
    </div>
    <div class="ov-chart" role="region" aria-label="${words.overview}"></div>
    <div class="ov-tooltip" role="tooltip" hidden></div>`;
  const find = selector => host.querySelector(selector);
  const chart = find(".ov-chart");
  const tooltip = find(".ov-tooltip");
  const search = find('input[type="search"]');
  const filter = find('input[type="checkbox"]');
  const results = find(".ov-results");
  const next = find(".ov-next");

  let group = "room";
  let chartWidth = 0;
  let marks = new Map();
  let near = [];
  let active = null;
  let paths;
  let matches = [];
  let matchIndex = 0;
  let searchTimer;

  function titleFor(exhibit) {
    return exhibit.name_en || exhibit.name_zh || exhibit.id;
  }

  function venueFor(exhibit) {
    return (lang === "en" && exhibit.en?.venue) || exhibit.venue || words.unknownVenue;
  }

  function anchorNames(items) {
    return items.filter(exhibit => anchors.has(exhibit.id)).map(exhibit =>
      `<a class="ov-anchor-name" data-exhibit="${esc(exhibit.id)}" tabindex="-1"
        href="${esc(exhibitHref(exhibit))}">${esc(titleFor(exhibit))}</a>`).join("");
  }

  function cell(items, width, mobile) {
    const pitch = mobile ? 14 : 8;
    const inset = mobile ? 7 : 4;
    const columns = Math.max(1, Math.floor(width / pitch));
    const height = Math.ceil(items.length / columns) * pitch;
    const ordered = [...items].sort((a, b) => Number(anchors.has(b.id)) - Number(anchors.has(a.id)));
    const dots = ordered.map((exhibit, index) => {
      const { id, status } = exhibit;
      const x = inset + index % columns * pitch;
      const y = inset + Math.floor(index / columns) * pitch;
      const label = [titleFor(exhibit), exhibit.year || words.unknownYear,
        venueFor(exhibit), status === "collected" ? words.collected : words.pending].join(" · ");
      return `<a class="ov-dot ${status === "collected" ? "is-collected" : ""} ${anchors.has(id) ? "is-anchor" : ""}"
        data-exhibit="${esc(id)}" href="${esc(exhibitHref(exhibit))}" aria-label="${esc(label)}">
        <rect class="ov-hit" x="${x - inset}" y="${y - inset}" width="${pitch}" height="${pitch}"/>
        <circle class="ov-ring" cx="${x}" cy="${y}" r="3.65"/>
        <circle class="ov-mark" cx="${x}" cy="${y}" r="2.55"/>
      </a>`;
    }).join("");
    const labels = mobile ? anchorNames(ordered) : "";
    return `<div class="ov-cell">${items.length ? `<svg class="ov-dots" width="100%" height="${height}">${dots}</svg>` : ""}${labels}</div>`;
  }

  function render() {
    inspect(null);
    const mobile = chartWidth < 900;
    host.classList.toggle("is-vertical", mobile);
    const labelWidth = mobile ? 108 : 168;
    const cellPadding = mobile ? 16 : 13;
    const slotWidth = (chartWidth - 2 - labelWidth) / (mobile ? 1 : years.length);
    chart.style.setProperty("--ov-label-width", `${labelWidth}px`);
    chart.style.setProperty("--ov-year-count", years.length);
    const visible = data.exhibits.filter(exhibit => !filter.checked || exhibit.status === "collected");
    const sourceRows = rows[group];
    const buckets = new Map([...sourceRows, [other, words.other]].map(([id, name]) =>
      [id, { name, total: 0, anchors: [], cells: new Map(years.map(year => [year, []])) }]));
    const yearTotals = new Map(years.map(year => [year, 0]));
    for (const exhibit of visible) {
      const row = buckets.get(group === "room" ? rooms.get(exhibit.id) : fieldFor(exhibit));
      const year = hasYear(exhibit.year) ? exhibit.year : null;
      row.cells.get(year).push(exhibit);
      if (anchors.has(exhibit.id)) row.anchors.push(exhibit);
      row.total++;
      yearTotals.set(year, yearTotals.get(year) + 1);
    }
    if (group === "field" && !buckets.get(other).total) buckets.delete(other);
    const yearName = year => year === null ? words.unknownYear : year;
    const heading = (name, count) => `<span>${esc(name)}</span><small>${words.count(count)}</small>`;
    const makeCell = items => cell(items, slotWidth - cellPadding, mobile);
    const values = Array.from(buckets.values());
    find(".ov-total").textContent = `${words.total} ${words.count(visible.length)}`;
    chart.innerHTML = (mobile
      ? years.map(year => `<section class="ov-year-section">
          <h2 class="ov-year-title">${heading(yearName(year), yearTotals.get(year))}</h2>
          ${values.filter(row => row.cells.get(year).length).map(row => `<div class="ov-row">
            <h3 class="ov-row-title">${heading(row.name, row.cells.get(year).length)}</h3>
            ${makeCell(row.cells.get(year))}</div>`).join("")}</section>`).join("")
      : `<div class="ov-year-row"><div class="ov-axis-name">${words.year}</div>
          ${years.map(year => `<div class="ov-year-title">${heading(yearName(year), yearTotals.get(year))}</div>`).join("")}</div>
        ${values.map(row => `<section class="ov-row">
          <h2 class="ov-row-title">${heading(row.name, row.total)}</h2>
          ${years.map(year => makeCell(row.cells.get(year))).join("")}
          ${row.anchors.length ? `<div class="ov-anchor-list">${anchorNames(row.anchors)}</div>` : ""}
          </section>`).join("")}`)
      + `<svg class="ov-links" aria-hidden="true"><path class="ov-citations"/><path class="ov-lineage"/></svg>`;
    paths = {
      citation: chart.querySelector(".ov-citations"),
      lineage: chart.querySelector(".ov-lineage"),
    };
    marks = new Map(Array.from(chart.querySelectorAll(".ov-dot"), dot => [dot.dataset.exhibit, {
      dot, circle: dot.querySelector(".ov-mark"),
    }]));
    for (const label of chart.querySelectorAll(".ov-anchor-name")) {
      marks.get(label.dataset.exhibit).label = label;
    }
    updateSearch();
  }

  function inspect(id) {
    if (id === active) return;
    if (active !== null) marks.get(active).dot.classList.remove("is-active");
    active = id;
    for (const element of near) element.classList.remove("is-near");
    near = [];
    chart.classList.toggle("is-inspecting", id !== null);
    tooltip.hidden = id === null;
    if (id === null) {
      for (const path of Object.values(paths)) path.removeAttribute("d");
      return;
    }

    const origin = chart.getBoundingClientRect();
    const center = mark => {
      const rect = mark.circle.getBoundingClientRect();
      return [rect.left + rect.width / 2, rect.top + rect.height / 2];
    };
    const [clientX, clientY] = center(marks.get(id));
    const x = clientX - origin.left - chart.clientLeft;
    const y = clientY - origin.top - chart.clientTop;
    const segments = { citation: [], lineage: [] };
    const neighbors = [marks.get(id)];
    for (const [target, kind] of links.get(id)) {
      const mark = marks.get(target);
      if (!mark) continue;
      const [cx, cy] = center(mark);
      const dx = cx - clientX;
      const dy = cy - clientY;
      const padding = 3 / Math.hypot(dx, dy);
      segments[kind].push(`M${x + dx * padding},${y + dy * padding}l${dx * (1 - 2 * padding)},${dy * (1 - 2 * padding)}`);
      neighbors.push(mark);
    }
    for (const [kind, path] of Object.entries(paths)) path.setAttribute("d", segments[kind].join(" "));
    near = neighbors.flatMap(mark => [mark.dot, mark.label].filter(Boolean));
    for (const element of near) element.classList.add("is-near");
    marks.get(id).dot.classList.add("is-active");

    const exhibit = exhibits.get(id);
    const name = [titleFor(exhibit), lang === "zh" && exhibit.name_en && exhibit.name_zh].filter(Boolean).join(" · ");
    tooltip.innerHTML = `<strong>${esc(name)}</strong><span>${exhibit.year || words.unknownYear} · ${esc(venueFor(exhibit))}</span>`;
    const { offsetWidth: width, offsetHeight: height } = tooltip;
    tooltip.style.left = `${Math.max(8, Math.min(clientX + 10, innerWidth - width - 8))}px`;
    tooltip.style.top = `${Math.max(8, clientY + height + 12 <= innerHeight ? clientY + 10 : clientY - height - 10)}px`;
  }

  function updateSearch() {
    for (const mark of matches) mark.dot.classList.remove("is-match", "is-current");
    const query = normalize(search.value.trim());
    const ranked = [];
    if (query) {
      for (const { exhibit, names } of byName) {
        const mark = marks.get(exhibit.id);
        if (!mark || !names.some(name => name.includes(query))) continue;
        const rank = names.includes(query) ? 0 : names.some(name => name.startsWith(query)) ? 1 : 2;
        ranked.push({ mark, rank });
      }
    }
    matches = ranked.sort((a, b) => a.rank - b.rank).map(({ mark }) => mark);
    matchIndex = 0;
    for (const mark of matches) mark.dot.classList.add("is-match");
    results.hidden = !query;
    results.textContent = !query ? "" : matches.length ? words.found(matches.length) : words.empty;
    next.hidden = matches.length < 2;
  }

  function showMatch(offset) {
    if (!matches.length) return;
    matches[matchIndex].dot.classList.remove("is-current");
    matchIndex = (matchIndex + offset) % matches.length;
    const match = matches[matchIndex].dot;
    match.classList.add("is-current");
    match.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function listen(element, type, handle) {
    element.addEventListener(type, handle, { signal: events.signal });
  }
  const exhibitAt = target => target?.closest?.("[data-exhibit]")?.dataset.exhibit ?? null;
  listen(chart, "pointerover", event => {
    if (event.pointerType !== "touch") inspect(exhibitAt(event.target));
  });
  listen(chart, "pointerleave", () => inspect(null));
  listen(chart, "focusin", event => inspect(exhibitAt(event.target)));
  listen(chart, "focusout", () => inspect(null));
  listen(host, "keydown", event => {
    if (event.key === "Escape") inspect(null);
  });
  listen(window, "scroll", () => inspect(null));
  listen(search, "input", () => {
    updateSearch();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => showMatch(0), 180);
  });
  listen(search, "keydown", event => {
    if (event.key !== "Enter" || event.isComposing) return;
    clearTimeout(searchTimer);
    showMatch(matches[matchIndex]?.dot.classList.contains("is-current") ? 1 : 0);
  });
  listen(next, "click", () => showMatch(1));
  listen(filter, "change", render);
  for (const button of host.querySelectorAll("[data-group]")) {
    listen(button, "click", () => {
      if (group === button.dataset.group) return;
      find(`[data-group="${group}"]`).setAttribute("aria-pressed", "false");
      group = button.dataset.group;
      button.setAttribute("aria-pressed", "true");
      render();
    });
  }

  const observer = new ResizeObserver(() => {
    const width = chart.offsetWidth;
    if (width === chartWidth) return;
    chartWidth = width;
    render();
  });
  observer.observe(chart);
  return () => {
    observer.disconnect();
    events.abort();
    clearTimeout(searchTimer);
    host.replaceChildren();
  };
}
