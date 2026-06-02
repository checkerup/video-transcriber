// PR1 — Settings tab. Audio mode + device pickers.

function settingsTab() {
  return {
    devices: { platform: '', mic: [], system: [], selected: {} },
    form: { audio_mode: 'both', mic_device: '', system_device: '' },
    busy: false,
    savedOk: false,
    error: '',

    async init() {
      await this.refreshDevices();
      await this.loadCurrent();
    },

    async refreshDevices() {
      this.busy = true; this.error = '';
      try {
        const api = window.pywebview && window.pywebview.api;
        if (!api) return;
        const d = await api.list_audio_devices();
        if (d && d.error) {
          this.error = d.error;
          return;
        }
        this.devices = Object.assign({ mic: [], system: [], selected: {} }, d || {});
        if (this.devices.selected) {
          this.form.audio_mode    = this.devices.selected.audio_mode    || this.form.audio_mode;
          this.form.mic_device    = this.devices.selected.mic_device    || '';
          this.form.system_device = this.devices.selected.system_device || '';
        }
      } catch (e) {
        this.error = (e && e.message) || String(e);
      } finally {
        this.busy = false;
      }
    },

    async loadCurrent() {
      try {
        const api = window.pywebview && window.pywebview.api;
        if (!api) return;
        const rec = await api.get_recorder_config();
        if (rec && !rec.error) {
          this.form.audio_mode    = rec.audio_mode    || this.form.audio_mode;
          this.form.mic_device    = rec.mic_device    || '';
          this.form.system_device = rec.system_device || '';
        }
      } catch (_) { /* non-fatal */ }
    },

    async save() {
      this.busy = true; this.savedOk = false; this.error = '';
      try {
        const api = window.pywebview.api;
        const res = await api.set_recorder_config({
          audio_mode:    this.form.audio_mode,
          mic_device:    this.form.mic_device,
          system_device: this.form.system_device,
        });
        if (res && res.error) {
          this.error = res.error;
        } else {
          this.savedOk = true;
          setTimeout(() => this.savedOk = false, 2500);
        }
      } catch (e) {
        this.error = (e && e.message) || String(e);
      } finally {
        this.busy = false;
      }
    },
  };
}

window.settingsTab = settingsTab;
