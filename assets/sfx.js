/* CROSSFADE UI sounds. Synthesized with the Web Audio API, no sound files.
   window.SFX:
     select(i)  section change: a two-note chime, one pentatonic pitch per section (Home C5 ... History C6)
     tap()      page change inside a section, menu button: a soft glassy click
     tick(dir)  drum arrow: a heavy detent click, a low thump and a ping (A4 turning right, E4 turning left)
     toggle(on) FRONT on/off: a rising (on) or falling (off) three-step chirp
     ready()    site loaded: three rising tones, C5 G5 C6, the last held with a soft echo
     enabled() / setEnabled(on)   sound on or off, kept in localStorage "cf-sound" (default on)
   Panels in the shell's iframe use the shell's SFX (parent.SFX), so there is one audio context and one mute switch.
   Browsers only start audio after the user has interacted with the page, so nothing plays on first load. */
(function () {
  if (window.SFX) return;
  var ctx = null, out = null;
  var NOTES = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5];   // C5 D5 E5 G5 A5 C6

  function enabled() { try { return localStorage.getItem("cf-sound") !== "0"; } catch (e) { return true; } }
  function setEnabled(on) { try { localStorage.setItem("cf-sound", on ? "1" : "0"); } catch (e) {} }
  function activated() { var u = navigator.userActivation; return !u || u.hasBeenActive; }

  function ac() {
    if (!enabled() || !activated()) return null;
    if (!ctx) {
      var A = window.AudioContext || window.webkitAudioContext;
      if (!A) return null;
      ctx = new A();
      out = ctx.createGain(); out.gain.value = 0.55;
      var comp = ctx.createDynamicsCompressor();          // keeps overlapping sounds from clipping
      comp.threshold.value = -18; comp.ratio.value = 4;
      out.connect(comp); comp.connect(ctx.destination);
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }
  /* one enveloped oscillator: attack a, decay d, optional glide to f2 over the decay */
  function voice(type, f, t, a, d, peak, f2, dest) {
    var o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(f, t);
    if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + a + d);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + a + d);
    o.connect(g); g.connect(dest || out);
    o.start(t); o.stop(t + a + d + 0.05);
  }
  /* a short band-passed noise burst: the "mechanical" part of a click */
  function click(t, dur, peak, freq, q) {
    var n = Math.max(1, Math.floor(ctx.sampleRate * dur)), buf = ctx.createBuffer(1, n, ctx.sampleRate), d = buf.getChannelData(0);
    for (var i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, 3);
    var s = ctx.createBufferSource(), bp = ctx.createBiquadFilter(), g = ctx.createGain();
    s.buffer = buf; bp.type = "bandpass"; bp.frequency.value = freq; bp.Q.value = q || 1.4; g.gain.value = peak;
    s.connect(bp); bp.connect(g); g.connect(out); s.start(t);
  }

  window.SFX = {
    enabled: enabled,
    setEnabled: setEnabled,
    select: function (i) {
      if (!ac()) return;
      var t = ctx.currentTime + 0.005, f = NOTES[((i % NOTES.length) + NOTES.length) % NOTES.length];
      var lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 3200; lp.connect(out);
      click(t, 0.008, 0.25, 4200, 2);
      voice("triangle", f, t, 0.006, 0.34, 0.11, null, lp);             // note
      voice("sine", f * 2, t, 0.004, 0.18, 0.035, null, lp);            // shimmer an octave up
      voice("triangle", f * 1.5, t + 0.055, 0.006, 0.42, 0.09, null, lp); // the fifth, a beat later
    },
    tap: function () {
      if (!ac()) return;
      var t = ctx.currentTime + 0.005;
      click(t, 0.006, 0.18, 5200, 2.5);
      voice("sine", 1900, t, 0.003, 0.05, 0.05, 1400);
    },
    tick: function (dir) {
      if (!ac()) return;
      var t = ctx.currentTime + 0.005, f = dir > 0 ? 440 : 330;          // A4 turning right, E4 turning left
      click(t, 0.018, 0.9, 1100, 1.0);                                   // the detent, low and heavy
      click(t + 0.03, 0.010, 0.35, 1800, 1.4);                           // it settling
      voice("sine", 150, t, 0.003, 0.16, 0.9, 55);                       // body thump, dropping
      voice("triangle", f, t + 0.004, 0.004, 0.2, 0.45, f * 0.94);       // the ping
      voice("sine", f / 2, t + 0.004, 0.004, 0.22, 0.32, f * 0.47);       // an octave under it
      voice("square", f / 4, t + 0.004, 0.002, 0.05, 0.03);              // a little grit
    },
    /* load finished: three rising tones (C5, G5, C6), the last one held, with a soft echo */
    ready: function () {
      if (!ac()) return;
      var t = ctx.currentTime + 0.02, notes = [523.25, 783.99, 1046.5], gap = 0.13;
      var bus = ctx.createGain(), lp = ctx.createBiquadFilter(), dly = ctx.createDelay(1), fb = ctx.createGain(), wet = ctx.createGain();
      lp.type = "lowpass"; lp.frequency.value = 3600;
      dly.delayTime.value = 0.19; fb.gain.value = 0.28; wet.gain.value = 0.35;
      bus.connect(lp); lp.connect(out);
      lp.connect(dly); dly.connect(fb); fb.connect(dly); dly.connect(wet); wet.connect(out);
      notes.forEach(function (f, i) {
        var last = i === notes.length - 1, ts = t + i * gap, d = last ? 0.9 : 0.24;
        voice("triangle", f, ts, 0.008, d, 0.16, null, bus);
        voice("sine", f * 2, ts, 0.006, d * 0.6, 0.05, null, bus);     // shimmer
        voice("sine", f / 2, ts, 0.01, d * 0.8, 0.07, null, bus);      // warmth under it
      });
      click(t, 0.008, 0.2, 4200, 2);
    },
    toggle: function (on) {
      if (!ac()) return;
      var t = ctx.currentTime + 0.005, f = on ? [520, 780, 1040] : [780, 520, 350];
      var lp = ctx.createBiquadFilter(), o = ctx.createOscillator(), g = ctx.createGain();
      lp.type = "lowpass"; lp.frequency.value = 2400;
      o.type = "triangle";
      o.frequency.setValueAtTime(f[0], t);
      o.frequency.setValueAtTime(f[1], t + 0.07);
      o.frequency.exponentialRampToValueAtTime(f[2], t + 0.2);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.12, t + 0.012);
      g.gain.setValueAtTime(0.12, t + 0.16);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.28);
      o.connect(lp); lp.connect(g); g.connect(out);
      o.start(t); o.stop(t + 0.3);
      click(t, 0.008, 0.2, 3000, 1.5);
    }
  };
})();
