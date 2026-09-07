(function (global) {
  "use strict";

  if (global.CommonSpinePlayer) return;

  const MAX_LIVE_PLAYERS = 8;
  const MAX_PARKED_PLAYERS = 4;
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
  const sharedBase = managerUrl ? new URL(".", managerUrl).href : "./banners/shared/";
  let serial = 0;
  let runtimePromise;

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
      link.addEventListener("error", () => reject(new Error(`無法載入 ${url}`)), { once: true });
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
      script.addEventListener("error", () => reject(new Error(`無法載入 ${url}`)), { once: true });
      document.head.appendChild(script);
    });
  }

  function loadRuntime() {
    if (!runtimePromise) {
      runtimePromise = Promise.all([
        loadStylesheet(new URL("spine-player-3.8.css", sharedBase).href),
        loadScript(new URL("spine-player-3.8.js", sharedBase).href)
      ]).then(requireRuntime);
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
      entry.host.dataset.spineState = "idle";
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
    entry.host.dataset.spineState = "idle";
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
    entry.host.dataset.spineState = "parked";
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
    entry.host.dataset.spineState = player.loaded ? "ready" : "loading";
    live.add(entry);

    if (!document.hidden && !entry.reducedMotion) safeCall(player, "play");
    requestAnimationFrame(() => {
      if (entry.player === player && entry.state === "live") player.drawFrame();
    });
    return true;
  }

  function configFromElement(host) {
    const base = host.dataset.spineBase;
    const version = host.dataset.spineVersion || "1";
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
    entry.creating = true;
    entry.state = "loading";
    entry.host.dataset.spineState = "loading";
    try {
      await loadRuntime();
    } catch (error) {
      entry.host.dataset.spineState = "error";
      entry.state = "error";
      console.error(error);
      entry.creating = false;
      return;
    }
    if (entry.destroyed || instances.get(entry.host) !== entry || !entry.visible) {
      entry.creating = false;
      if (!entry.destroyed) {
        entry.state = "idle";
        entry.host.dataset.spineState = "idle";
      }
      return;
    }
    enforceLiveLimit(entry);

    entry.destroyed = false;
    const config = configFromElement(entry.host);
    const userSuccess = entry.options.success;
    const userError = entry.options.error;

    config.success = (player) => {
      if (entry.destroyed || entry.player !== player) return;
      if (entry.state === "parked") {
        entry.host.dataset.spineState = "parked";
        player.pause();
      } else {
        entry.state = "live";
        entry.host.dataset.spineState = "ready";
        if (entry.reducedMotion || document.hidden || !entry.visible) player.pause();
      }
      if (typeof userSuccess === "function") userSuccess(player);
    };
    config.error = (player, message) => {
      if (entry.destroyed || entry.player !== player) return;
      entry.host.dataset.spineState = "error";
      if (typeof userError === "function") userError(player, message);
    };

    const pageResizeHandler = global.onresize;
    let player;
    try {
      player = new global.spine.SpinePlayer(entry.host, config);
    } catch (error) {
      global.onresize = pageResizeHandler;
      entry.creating = false;
      entry.state = "error";
      entry.host.dataset.spineState = "error";
      console.error(error);
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
    if (!host.dataset.spineBase && !host.dataset.spineJson) {
      throw new Error("Spine 容器需要 data-spine-base 或 data-spine-json");
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
    host.dataset.spineState = "idle";

    if (observer) observer.observe(host);
    else activate(entry);
    return entry;
  }

  function mountAll(root = document) {
    return Array.from(root.querySelectorAll("[data-spine-player]"), (host) => mount(host));
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
