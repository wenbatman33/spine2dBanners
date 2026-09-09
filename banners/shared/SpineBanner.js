import { h } from "./vue.esm-browser.prod.js";

const PLAYER_VERSION = "20260909-src-2";
let managerPromise;

function loadManager() {
  if (window.CommonSpinePlayer) return Promise.resolve(window.CommonSpinePlayer);
  if (!managerPromise) {
    managerPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      const url = new URL("./common-spine-player.js", import.meta.url);
      url.searchParams.set("v", PLAYER_VERSION);
      script.src = url.href;
      script.onload = () => resolve(window.CommonSpinePlayer);
      script.onerror = () => {
        managerPromise = null;
        script.remove();
        reject(new Error("無法載入 Banner 播放器"));
      };
      document.head.append(script);
    });
  }
  return managerPromise;
}

export default {
  name: "SpineBanner",
  props: { src: { type: String, required: true } },
  emits: ["load", "error"],
  data: () => ({ active: false, revision: 0, error: "" }),
  mounted() {
    this.active = true;
    this.mountPlayer();
  },
  beforeUnmount() {
    this.active = false;
    window.CommonSpinePlayer?.unmount(this.$el);
  },
  watch: { src: "mountPlayer" },
  methods: {
    async mountPlayer() {
      if (!this.active) return;
      const revision = ++this.revision;
      this.error = "";
      window.CommonSpinePlayer?.unmount(this.$el);
      this.$el.dataset.spineState = "loading";
      this.$el.setAttribute("aria-busy", "true");
      const current = () => this.active && revision === this.revision;
      const failed = (error) => {
        if (!current()) return;
        this.error = "加载失败";
        this.$el.dataset.spineState = "error";
        this.$el.setAttribute("aria-busy", "false");
        this.$emit("error", error);
      };
      try {
        const manager = await loadManager();
        // Ignore pending loads after removal or a newer source change.
        if (!current()) return;
        manager.mount(this.$el, {
          src: this.src,
          success: () => { if (current()) this.$emit("load"); },
          error: (_, message) => failed(message)
        });
      } catch (error) {
        failed(error);
      }
    }
  },
  render() {
    return h("div", {
      class: "spine-banner",
      style: { position: "relative", width: "100%", aspectRatio: "620 / 272" }
    }, [h("span", {
      class: "spine-loading",
      role: "status",
      lang: "zh-CN",
      style: {
        position: "absolute", inset: "0", zIndex: "1",
        display: "grid", placeItems: "center", pointerEvents: "none",
        background: "#071020", color: "#c4d2e6",
        font: '14px/1.5 system-ui, "PingFang SC", sans-serif'
      }
    }, this.error || "加载中…")]);
  }
};
