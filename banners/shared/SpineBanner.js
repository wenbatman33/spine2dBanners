import { h } from "./vue.esm-browser.prod.js";

let managerPromise;

function loadManager() {
  if (window.CommonSpinePlayer) return Promise.resolve(window.CommonSpinePlayer);
  if (!managerPromise) {
    managerPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = new URL("./common-spine-player.js", import.meta.url).href;
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
  props: { id: { type: String, required: true } },
  data: () => ({ active: false, revision: 0, error: "" }),
  mounted() {
    this.active = true;
    this.mountPlayer();
  },
  beforeUnmount() {
    this.active = false;
    window.CommonSpinePlayer?.unmount(this.$el);
  },
  watch: { id: "mountPlayer" },
  methods: {
    async mountPlayer() {
      if (!this.active) return;
      const revision = ++this.revision;
      this.error = "";
      try {
        const manager = await loadManager();
        // Ignore pending loads after removal or a newer id change.
        if (!this.active || revision !== this.revision) return;
        manager.unmount(this.$el);
        manager.mount(this.$el, { id: this.id });
      } catch (error) {
        if (this.active && revision === this.revision) {
          this.error = "加载失败";
          console.error(error);
        }
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
