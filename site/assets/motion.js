// 动效。四件事：玫瑰窗点亮、穿过花窗进展室、论文图从展墙飞到展签、展墙文字随滚动浮现。
// 系统设了「减少动态效果」时全部不做。这个文件加载失败时，页面照常能用。
window.Motion = (() => {
  const calm = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  const root = document.documentElement;
  let twinkle = 0;

  // 换页。浏览器支持视图过渡时，旧页面和新页面之间做一次过渡，否则直接换。
  function swap(fn, kind) {
    if (calm() || !document.startViewTransition) { fn(); return; }
    if (kind) root.dataset.vt = kind;
    const tr = document.startViewTransition(fn);
    tr.finished.finally(() => { delete root.dataset.vt; });
  }

  // 点花窗的一片花瓣：记下点的位置，换页时旧页面朝这一点放大，像穿过窗子走进展室。
  let pending = null;
  function throughWindow(el) {
    const r = el.getBoundingClientRect();
    root.style.setProperty("--vt-x", `${r.left + r.width / 2}px`);
    root.style.setProperty("--vt-y", `${r.top + r.height / 2}px`);
    pending = "window";
  }
  function takeKind() { const k = pending; pending = null; return k; }

  // 开展签：页面上那张图和展签里的图用同一个名字，浏览器把前者变形成后者。
  function liftFigure(id, open) {
    if (calm() || !document.startViewTransition) { open(); return; }
    const from = [...document.querySelectorAll(`main .fig[data-id="${CSS.escape(id)}"]`)]
      .find(el => { const r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight && r.width > 0; });
    if (!from || from.classList.contains("fig-ph")) { open(); return; }
    from.style.viewTransitionName = "lifted-figure";
    root.dataset.vt = "figure";
    const tr = document.startViewTransition(async () => {
      from.style.viewTransitionName = "";
      await open();
      const to = document.querySelector("#drawer-root .obj-fig .fig");
      const img = to && to.querySelector("img");
      if (img && img.decode) { try { await img.decode(); } catch (err) { /* 解码失败就照常显示 */ } }
      if (to) to.style.viewTransitionName = "lifted-figure";
    });
    tr.finished.finally(() => {
      delete root.dataset.vt;
      const to = document.querySelector("#drawer-root .obj-fig .fig");
      if (to) to.style.viewTransitionName = "";
    });
  }

  // 玫瑰窗：石框先出现，玻璃从中心一圈圈向外亮起来。一次会话只演一遍。亮完后偶尔有几片闪一下。
  function rose(slot) {
    clearInterval(twinkle);
    if (calm()) return;
    const svg = slot.querySelector("svg");
    if (!svg) return;
    const panes = [...svg.querySelectorAll("path:not(.stone)")];
    let seen = false;
    try { seen = sessionStorage.getItem("rose-lit") === "1"; sessionStorage.setItem("rose-lit", "1"); } catch (err) { /* 存不了就每次都演 */ }
    if (!seen) {
      for (const p of panes) {
        const m = /M(-?[\d.]+) (-?[\d.]+)/.exec(p.getAttribute("d") || "");
        const r = m ? Math.hypot(+m[1], +m[2]) : 0;
        p.style.animationDelay = `${Math.round(250 + r * 3.4 + Math.random() * 260)}ms`;
      }
      // 窗子滚到眼前才开始亮。在那之前玻璃是暗的，只看得见石框。
      slot.classList.add("rose-dark");
      const light = () => {
        slot.classList.replace("rose-dark", "rose-lighting");
        setTimeout(() => { slot.classList.remove("rose-lighting"); for (const p of panes) p.style.animationDelay = ""; }, 3300);
      };
      const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); light(); } }, { threshold: 0.35 });
      io.observe(slot);
    }
    const glass = panes.filter(p => /^f[a-e]\d$/.test(p.getAttribute("class") || ""));
    twinkle = setInterval(() => {
      if (!document.body.contains(slot)) { clearInterval(twinkle); return; }
      if (document.hidden || slot.classList.contains("rose-lighting") || slot.classList.contains("rose-dark")) return;
      for (let k = 0; k < 7; k++) {
        const p = glass[Math.floor(Math.random() * glass.length)];
        if (p) p.animate([{ opacity: 1 }, { opacity: 0.45 }, { opacity: 1 }], { duration: 1500 + Math.random() * 900, easing: "ease-in-out" });
      }
    }, 800);
  }

  // 展墙文字和展品：滚到眼前时浮上来。首屏里的不藏。一下子滚过去的（上沿已经高过视口底）也直接显示。
  let waiting = [];
  function settle() {
    const line = innerHeight * 0.92;
    waiting = waiting.filter(el => {
      if (el.getBoundingClientRect().top >= line) return true;
      el.classList.add("is-in");
      return false;
    });
  }
  addEventListener("scroll", () => { if (waiting.length) settle(); }, { passive: true });   // 至多十几个元素，不必等下一帧
  addEventListener("resize", () => { if (waiting.length) settle(); });
  function reveal() {
    waiting = [];
    if (calm()) return;
    titles();
    const line = innerHeight * 0.92;
    for (const el of document.querySelectorAll("main .wall-text, main .plate, main .room-end")) {
      if (el.getBoundingClientRect().top < line) continue;
      el.classList.add("will-rise");
      waiting.push(el);
    }
  }

  // 标题逐字（英文逐词）升起。延迟按 i/(n-1) 归一，最后一个字准时到位。读屏软件读到的仍是整句。
  function riseTitle(el) {
    if (calm() || !el || el.dataset.risen || el.children.length) return;
    const text = el.textContent;
    const parts = /[一-鿿]/.test(text) ? [...text] : text.split(/(\s+)/);
    const solid = parts.filter(x => x.trim()).length;
    if (solid < 2 || solid > 40) return;
    el.dataset.risen = "1";
    el.setAttribute("aria-label", text);
    const total = 620, stagger = 0.55;
    let i = 0;
    el.textContent = "";
    for (const part of parts) {
      if (!part.trim()) { el.append(part); continue; }
      const clip = document.createElement("span"), inner = document.createElement("span");
      clip.className = "rise-clip"; clip.setAttribute("aria-hidden", "true");
      inner.textContent = part;
      inner.style.animationDelay = `${Math.round(120 + (i / (solid - 1)) * stagger * total)}ms`;
      inner.style.animationDuration = `${Math.round((1 - stagger) * total + 260)}ms`;
      clip.append(inner); el.append(clip); i++;
    }
  }
  function titles() { document.querySelectorAll("main .foyer-title, main .room-head h1, main .page-head h1").forEach(riseTitle); }

  return { titles, swap, throughWindow, takeKind, liftFigure, rose, reveal };
})();
