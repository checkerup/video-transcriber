// PR1 — Watcher tab.
// Registers an Alpine component that polls the recorder status every 2s
// and exposes start/stop buttons. Wired to pywebview's JsApi.

function watcherTab() {
  return {
    isRecording: false,
    currentOutput: '',
    error: '',
    busy: false,
    _timer: null,

    async init() {
      await this.refresh();
      this._timer = setInterval(() => this.refresh().catch(() => {}), 2000);
    },

    async refresh() {
      try {
        // pywebview exposes JsApi methods on window.pywebview.api.
        const api = window.pywebview && window.pywebview.api;
        if (!api) return;
        // The recorder status endpoint already exists in the current api.py.
        // We call it defensively in case the name differs across branches.
        const status = await (api.get_recorder_status
          ? api.get_recorder_status()
          : { is_recording: false, output: '' });
        this.isRecording = !!status.is_recording;
        this.currentOutput = status.output || '';
      } catch (e) {
        // Don't blow up the UI — surface in the error slot.
        this.error = (e && e.message) || String(e);
      }
    },

    async start() {
      this.busy = true; this.error = '';
      try {
        const api = window.pywebview.api;
        const res = await api.start_recording();
        if (res && res.error) this.error = res.error;
        await this.refresh();
      } catch (e) {
        this.error = (e && e.message) || String(e);
      } finally {
        this.busy = false;
      }
    },

    async stop() {
      this.busy = true; this.error = '';
      try {
        const api = window.pywebview.api;
        const res = await api.stop_recording();
        if (res && res.error) this.error = res.error;
        await this.refresh();
      } catch (e) {
        this.error = (e && e.message) || String(e);
      } finally {
        this.busy = false;
      }
    },
  };
}

// Make available to Alpine without a bundler.
window.watcherTab = watcherTab;
