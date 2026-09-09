(function (global) {
  "use strict";

  if (global.CommonSpinePlayer) return;

  const MAX_LIVE_PLAYERS = 8;
  const MAX_PARKED_PLAYERS = 4;
  const DEFAULT_ASSET_VERSION = "20260907-optimized";
  const HOST_SELECTOR = "[data-spine], [data-spine-player]";
  const LAYOUT_SELECTOR = `${HOST_SELECTOR}, .spine-banner`;
  const DEFAULT_VIEWPORT = {
    x: -310,
    y: -136,
    width: 620,
    height: 272,
    padLeft: "0%",
    padRight: "0%",
    padTop: "0%",
    padBottom: "0%"
  };

  const instances = new Map();
  const live = new Set();
  const parked = [];
  const managerUrl = document.currentScript && document.currentScript.src;
  const sharedBase = new URL(".", managerUrl || new URL("./banners/shared/common-spine-player.js", document.baseURI)).href;
  let serial = 0;
  let runtimePromise;

  const layout = document.createElement("style");
  layout.textContent = `
    :where(${LAYOUT_SELECTOR}) {
      display: block;
      position: relative;
      width: 100%;
      max-width: 620px;
      aspect-ratio: 620 / 272;
      overflow: hidden;
    }
    :where(${LAYOUT_SELECTOR}) > .spine-player { width: 100%; height: 100%; }
    :where(${LAYOUT_SELECTOR}) > .spine-player > canvas { display: block; width: 100%; height: 100%; }
    :where(${LAYOUT_SELECTOR}):not([data-spine-controls="true"]) .spine-player-controls { display: none !important; }
    :where(${LAYOUT_SELECTOR}) .spine-player-button-icon-spine-logo { display: none !important; }
    .spine-loading {
      position: absolute; inset: 0; z-index: 1;
      display: grid; place-items: center; pointer-events: none;
      background: #071020; color: #c4d2e6;
      font: 14px/1.5 system-ui, "PingFang SC", sans-serif;
    }
    :where(${LAYOUT_SELECTOR})[data-spine-state="ready"] > .spine-loading { display: none !important; }
  `;
  document.head.appendChild(layout);

  function setHostState(host, state) {
    host.dataset.spineState = state;
    host.setAttribute("aria-busy", String(state === "loading"));
    const message = host.querySelector(":scope > .spine-loading");
    if (message) message.textContent = state === "error" ? "加载失败" : "加载中…";
  }

  function loadStylesheet(url) {
    const existing = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).find((link) => link.href === url);
    if (existing && existing.sheet) return Promise.resolve();
    if (existing) {
      return new Promise((resolve, reject) => {
        existing.addEventListener("load", resolve, { once: true });
        existing.addEventListener("error", () => reject(new Error(`無法載入 ${url}`)), { once: true });
      });
    }
    return new Promise((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = url;
      link.dataset.commonSpineRuntime = "style";
      link.addEventListener("load", resolve, { once: true });
      link.addEventListener("error", () => { link.remove(); reject(new Error(`無法載入 ${url}`)); }, { once: true });
      document.head.appendChild(link);
    });
  }

  function loadScript(url) {
    if (global.spine && global.spine.SpinePlayer) return Promise.resolve();
    const existing = Array.from(document.scripts).find((script) => script.src === url);
    if (existing) {
      return new Promise((resolve, reject) => {
        existing.addEventListener("load", resolve, { once: true });
        existing.addEventListener("error", () => reject(new Error(`無法載入 ${url}`)), { once: true });
      });
    }
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = url;
      script.dataset.commonSpineRuntime = "script";
      script.addEventListener("load", resolve, { once: true });
      script.addEventListener("error", () => { script.remove(); reject(new Error(`無法載入 ${url}`)); }, { once: true });
      document.head.appendChild(script);
    });
  }

  function loadRuntime() {
    if (!runtimePromise) {
      runtimePromise = Promise.all([
        loadStylesheet(new URL("spine-player-3.8.css", sharedBase).href),
        loadScript(new URL("spine-player-3.8.js", sharedBase).href)
      ]).then(requireRuntime).catch((error) => { runtimePromise = null; throw error; });
    }
    return runtimePromise;
  }

  function requireRuntime() {
    if (!global.spine || !global.spine.SpinePlayer) {
      throw new Error("Spine runtime 尚未載入，請先引入 spine-player-3.8.js");
    }

    const prototype = global.spine.SpinePlayer.prototype;
    if (!prototype.__commonPlayerInputPatch) {
      const originalSetupInput = prototype.setupInput;
      prototype.setupInput = function () {
        if (this.config.showControls) originalSetupInput.call(this);
      };
      prototype.__commonPlayerInputPatch = true;
    }
  }

  function safeCall(target, method) {
    try {
      if (target && typeof target[method] === "function") target[method]();
    } catch (_) {
      // A partially loaded WebGL player may not own every disposable yet.
    }
  }

  function disposePlayer(entry) {
    const player = entry.player;
    entry.destroyed = true;
    if (!player) {
      entry.state = "idle";
      setHostState(entry.host, "idle");
      live.delete(entry);
      const emptyParkedIndex = parked.indexOf(entry);
      if (emptyParkedIndex >= 0) parked.splice(emptyParkedIndex, 1);
      return;
    }

    player.stopRequestAnimationFrame = true;
    safeCall(player, "stopRendering");
    safeCall(player, "pause");
    if (player.dom) player.dom.remove();
    if (player.canvas && entry.onContextLost) {
      player.canvas.removeEventListener("webglcontextlost", entry.onContextLost);
    }

    entry.player = null;
    entry.state = "idle";
    setHostState(entry.host, "idle");
    live.delete(entry);
    const parkedIndex = parked.indexOf(entry);
    if (parkedIndex >= 0) parked.splice(parkedIndex, 1);

    // The legacy runtime may already have queued one final animation frame.
    // Wait until it has observed stopRequestAnimationFrame before releasing GL.
    requestAnimationFrame(() => requestAnimationFrame(() => {
      safeCall(player.sceneRenderer, "dispose");
      safeCall(player.assetManager, "dispose");
      try {
        const gl = player.context && player.context.gl;
        const loseContext = gl && gl.getExtension("WEBGL_lose_context");
        if (loseContext) loseContext.loseContext();
      } catch (_) {}
      if (player.canvas) {
        player.canvas.width = 1;
        player.canvas.height = 1;
      }
    }));
  }

  function trimParkedPlayers() {
    while (parked.length > MAX_PARKED_PLAYERS) disposePlayer(parked.shift());
  }

  function park(entry) {
    if (!entry.player || entry.state === "parked") return;

    entry.player.stopRequestAnimationFrame = true;
    safeCall(entry.player, "stopRendering");
    safeCall(entry.player, "pause");
    if (entry.player.dom) entry.player.dom.remove();
    entry.state = "parked";
    setHostState(entry.host, "parked");
    live.delete(entry);
    const prior = parked.indexOf(entry);
    if (prior >= 0) parked.splice(prior, 1);
    parked.push(entry);
    trimParkedPlayers();
  }

  function enforceLiveLimit(incoming) {
    while (live.size >= MAX_LIVE_PLAYERS) {
      const candidate = Array.from(live).find((entry) => entry !== incoming && !entry.visible);
      if (!candidate) break;
      park(candidate);
    }
  }

  function resume(entry) {
    const player = entry.player;
    if (!player || entry.state !== "parked") return false;

    enforceLiveLimit(entry);
    const parkedIndex = parked.indexOf(entry);
    if (parkedIndex >= 0) parked.splice(parkedIndex, 1);
    entry.host.appendChild(player.dom);
    player.stopRequestAnimationFrame = false;
    entry.state = "live";
    setHostState(entry.host, player.loaded ? "ready" : "loading");
    live.add(entry);

    if (!document.hidden && !entry.reducedMotion) safeCall(player, "play");
    requestAnimationFrame(() => {
      if (entry.player === player && entry.state === "live") player.drawFrame();
    });
    return true;
  }

  function resolveFolderSource(src) {
    if (typeof src !== "string" || !src.trim()) throw new Error("請填入 Banner 資料夾路徑");
    const folder = new URL(src.trim(), document.baseURI);
    if (!/^https?:$/.test(folder.protocol)) throw new Error("請使用 HTTP 或 HTTPS 資料夾網址");
    if (/\.(?:json|atlas|html?)$/i.test(folder.pathname)) throw new Error("src 請指向資料夾，不是檔案");
    if (!folder.pathname.endsWith("/")) folder.pathname += "/";
    return folder.href;
  }

  function configFromElement(host, options) {
    const id = options.id || host.dataset.spine;
    const base = options.src
      ? new URL("banner", options.src).href
      : host.dataset.spineBase || (id && new URL(`../${id}/banner`, sharedBase).href);
    const version = host.dataset.spineVersion ?? DEFAULT_ASSET_VERSION;
    const suffix = version ? `?v=${encodeURIComponent(version)}` : "";
    return {
      jsonUrl: host.dataset.spineJson || `${base}.json${suffix}`,
      atlasUrl: host.dataset.spineAtlas || `${base}.atlas${suffix}`,
      animation: host.dataset.spineAnimation || "animation",
      loop: host.dataset.spineLoop !== "false",
      alpha: true,
      premultipliedAlpha: host.dataset.spinePremultiplied === "true",
      showControls: host.dataset.spineControls === "true",
      backgroundColor: host.dataset.spineBackground || "#00000000",
      fullScreenBackgroundColor: host.dataset.spineBackground || "#00000000",
      viewport: { ...DEFAULT_VIEWPORT }
    };
  }

  async function create(entry) {
    if (entry.player || entry.creating || !entry.visible) return;
    entry.destroyed = false;
    entry.creating = true;
    entry.state = "loading";
    setHostState(entry.host, "loading");
    try {
      await loadRuntime();
    } catch (error) {
      if (entry.destroyed || instances.get(entry.host) !== entry) {
        entry.creating = false;
        return;
      }
      setHostState(entry.host, "error");
      entry.state = "error";
      console.error(error);
      entry.creating = false;
      if (typeof entry.options.error === "function") entry.options.error(null, error);
      return;
    }
    if (entry.destroyed || instances.get(entry.host) !== entry || !entry.visible) {
      entry.creating = false;
      if (!entry.destroyed) {
        entry.state = "idle";
        setHostState(entry.host, "idle");
      }
      return;
    }
    enforceLiveLimit(entry);

    entry.destroyed = false;
    const config = configFromElement(entry.host, entry.options);
    const userSuccess = entry.options.success;
    const userError = entry.options.error;

    config.success = (player) => {
      if (entry.destroyed || entry.player !== player) return;
      if (entry.state === "parked") {
        setHostState(entry.host, "parked");
        player.pause();
      } else {
        entry.state = "live";
        setHostState(entry.host, "ready");
        if (entry.reducedMotion || document.hidden || !entry.visible) player.pause();
      }
      if (typeof userSuccess === "function") userSuccess(player);
    };
    config.error = (player, message) => {
      if (entry.destroyed || entry.player !== player) return;
      setHostState(entry.host, "error");
      if (typeof userError === "function") userError(player, message);
    };

    const pageResizeHandler = global.onresize;
    let player;
    try {
      player = new global.spine.SpinePlayer(entry.host, config);
      // Use the DOM loading message, not Spine 3.8's WebGL logo/spinner.
      if (player.loadingScreen) player.loadingScreen.draw = function () {};
    } catch (error) {
      global.onresize = pageResizeHandler;
      entry.creating = false;
      entry.state = "error";
      setHostState(entry.host, "error");
      console.error(error);
      if (typeof userError === "function") userError(null, error);
      return;
    }
    // Spine 3.8 assigns window.onresize for every instance. Restore the host
    // page's handler; the manager's shared resize listener updates all players.
    global.onresize = pageResizeHandler;
    entry.player = player;
    entry.creating = false;
    live.add(entry);

    if (player.canvas) {
      entry.onContextLost = (event) => {
        if (!entry.destroyed) event.preventDefault();
        disposePlayer(entry);
        if (entry.visible) setTimeout(() => create(entry), 60);
      };
      player.canvas.addEventListener("webglcontextlost", entry.onContextLost, { once: true });
    }
  }

  function activate(entry) {
    entry.visible = true;
    if (resume(entry)) return;
    if (!entry.player) create(entry);
    else if (!document.hidden && !entry.reducedMotion) safeCall(entry.player, "play");
  }

  function deactivate(entry) {
    entry.visible = false;
    park(entry);
  }

  const observer = "IntersectionObserver" in global
    ? new IntersectionObserver((records) => {
        for (const record of records) {
          const entry = instances.get(record.target);
          if (!entry) continue;
          if (record.isIntersecting) activate(entry);
          else deactivate(entry);
        }
      }, { rootMargin: "360px 0px", threshold: 0.01 })
    : null;

  function mount(host, options = {}) {
    if (!host || instances.has(host)) return instances.get(host);
    if (options.src !== undefined) options = { ...options, src: resolveFolderSource(options.src) };
    if (!options.src && !options.id && !host.dataset.spine && !host.dataset.spineBase && !host.dataset.spineJson) {
      throw new Error("請指定 Banner src（資料夾路徑）");
    }
    host.classList.add("spine-banner");
    if (!host.querySelector(":scope > .spine-loading")) {
      const message = document.createElement("span");
      message.className = "spine-loading";
      message.setAttribute("role", "status");
      message.lang = "zh-CN";
      host.append(message);
    }
    if (!host.hasAttribute("role")) host.setAttribute("role", "img");
    if (!host.hasAttribute("aria-label") && !host.hasAttribute("aria-labelledby")) {
      host.setAttribute("aria-label", "動畫 Banner");
    }

    const entry = {
      id: ++serial,
      host,
      options,
      player: null,
      creating: false,
      state: "idle",
      visible: false,
      destroyed: false,
      reducedMotion: global.matchMedia("(prefers-reduced-motion: reduce)").matches
    };
    instances.set(host, entry);
    setHostState(host, "idle");

    if (observer) observer.observe(host);
    else activate(entry);
    return entry;
  }

  function mountAll(root = document) {
    return Array.from(root.querySelectorAll(HOST_SELECTOR), (host) => mount(host));
  }

  function unmount(host) {
    const entry = instances.get(host);
    if (!entry) return;
    if (observer) observer.unobserve(host);
    disposePlayer(entry);
    instances.delete(host);
  }

  function getStats() {
    return {
      registered: instances.size,
      live: live.size,
      parked: parked.length,
      ready: Array.from(instances.values()).filter((entry) => entry.host.dataset.spineState === "ready").length
    };
  }

  document.addEventListener("visibilitychange", () => {
    for (const entry of live) {
      if (!entry.player) continue;
      if (document.hidden || entry.reducedMotion) safeCall(entry.player, "pause");
      else if (entry.visible) safeCall(entry.player, "play");
    }
  });

  global.addEventListener("resize", () => {
    for (const entry of live) {
      if (entry.player && entry.player.loaded) entry.player.drawFrame(false);
    }
  });

  global.CommonSpinePlayer = { mount, mountAll, unmount, getStats };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => mountAll(), { once: true });
  } else {
    mountAll();
  }
})(window);
