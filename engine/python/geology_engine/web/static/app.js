// SPDX-FileCopyrightText: Geology Rocks contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Key prototype page. All scoring happens in the Python engine (/api/evaluate);
// this file only keeps track of the user's answers and draws the page.
"use strict";

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
};

let CORE = null;                 // questions, kit, contexts
let CHAR = {};                   // id -> question
const state = {
  order: [],                     // question ids in the order the user dealt with them
  answers: {},                   // id -> state id, or list of ticked ids (multi)
  skipped: {},                   // id -> "skip" | "not_sure"
  current: null,                 // question the user jumped to (else: first suggestion)
  kit: new Set(),
  mode: "expert",
  context: "",
  showAll: false,
  pendingTicks: new Set(),       // multi-select ticks before "Done"
};
let RESULT = null;

async function init() {
  CORE = await (await fetch("/api/core")).json();
  CORE.characters.forEach((c) => (CHAR[c.id] = c));
  $("tau").textContent = Math.round(CORE.params.tau * 100) + "%";
  for (const c of CORE.contexts) {
    const o = el("option", null, c.label);
    o.value = c.id;
    $("context").append(o);
  }
  for (const k of CORE.kit) {
    if (k.default_owned) state.kit.add(k.id);
    const lab = el("label");
    const box = el("input");
    box.type = "checkbox";
    box.checked = k.default_owned;
    box.onchange = () => { box.checked ? state.kit.add(k.id) : state.kit.delete(k.id); update(); };
    lab.append(box, " " + k.name);
    $("kit").append(lab);
  }
  $("context").onchange = (e) => { state.context = e.target.value; update(); };
  $("mode").onchange = (e) => { state.mode = e.target.value; update(); };
  $("restart").onclick = restart;
  initTesting();
  $("more").onclick = () => { state.showAll = !state.showAll; render(); };
  update();
}

function restart() {
  state.order = []; state.answers = {}; state.skipped = {}; state.current = null;
  state.pendingTicks = new Set();
  update();
}

function record(id, kind, value) {
  delete state.answers[id];
  delete state.skipped[id];
  state.order = state.order.filter((x) => x !== id);
  if (kind === "answer") state.answers[id] = value;
  if (kind === "skip" || kind === "not_sure") state.skipped[id] = kind;
  if (kind !== "remove") state.order.push(id);
  state.current = null;
  state.pendingTicks = new Set();
  update();
}

// Show any question so it can be answered or changed. Any old answer stays
// until a new one is chosen.
function reopen(id) {
  state.pendingTicks = new Set(Array.isArray(state.answers[id]) ? state.answers[id] : []);
  state.current = id;
  render();
}

async function update() {
  $("kit-count").textContent = state.kit.size;
  const body = {
    answers: state.order.filter((id) => id in state.answers).map((id) => ({ char: id, state: state.answers[id] })),
    skipped: Object.keys(state.skipped),
    kit: [...state.kit],
    mode: state.mode,
    find_context: state.context || null,
  };
  const res = await fetch("/api/evaluate", { method: "POST", headers: { "Content-Type": "application/json" },
                                              body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) { showError(data.error || "Something went wrong"); return; }
  RESULT = data;
  render();
}

function showError(msg) {
  $("error").textContent = msg;
  $("error").hidden = false;
  setTimeout(() => ($("error").hidden = true), 5000);
}

function answerText(id) {
  const c = CHAR[id];
  if (id in state.skipped) return state.skipped[id] === "skip" ? "Skipped" : "Not sure";
  const v = state.answers[id];
  const labels = (Array.isArray(v) ? v : [v]).map((s) => c.states.find((x) => x.id === s).label);
  return labels.length ? labels.join("; ") : "Nothing ticked";
}

function currentQuestion() {
  if (state.current) return state.current;
  return RESULT.suggested[0] || null;
}

function render() {
  renderQuestionList();
  renderCurrent();
  renderResult();
  renderAnswers();
  renderTrace();
}

function renderQuestionList() {
  const list = $("question-list");
  list.replaceChildren();
  const info = Object.fromEntries(RESULT.questions.map((q) => [q.char, q]));
  const cur = currentQuestion();
  for (const c of CORE.characters) {
    const li = el("li");
    const q = info[c.id];
    let mark = "";
    if (c.id in state.answers) { li.classList.add("answered"); mark = "✓"; }
    else if (c.id in state.skipped) { li.classList.add("skipped"); mark = "–"; }
    else if (q && q.suggested) mark = "★";
    else if (q && !q.kit_ok) mark = "🔒";
    if (q && !q.eligible) li.classList.add("later");
    if (c.id === cur) li.classList.add("current");
    const text = el("span", "q", c.question);
    if (c.id in state.answers || c.id in state.skipped) text.append(el("span", "ans", answerText(c.id)));
    li.append(el("span", "mark", mark), text);
    li.title = q && !q.eligible ? "Not usually asked yet, but you can answer it" : "";
    li.onclick = () => reopen(c.id);
    list.append(li);
  }
}

function renderCurrent() {
  const box = $("current");
  box.replaceChildren();
  const id = currentQuestion();
  if (!id) {
    box.append(el("h2", null, "No more useful questions"),
      el("p", "done-msg", "The key has asked everything that would still help. Your result is on the right."),
      el("p", "hint", "You can still jump to any question in the list to add or change an answer."));
    return;
  }
  const c = CHAR[id];
  const suggested = RESULT.suggested[0] === id;
  const status = id in state.answers ? "You answered: " + answerText(id) + " — pick another to change it"
    : suggested ? "Suggested next question" : "Question you chose";
  box.append(el("p", "hint", status));
  box.append(el("h2", "question", c.question));
  if (c.how_to) box.append(el("p", "howto", c.how_to));
  if (c.safety) box.append(el("p", "safety", "⚠ " + c.safety));
  const missing = c.kit_required.filter((k) => !state.kit.has(k));
  if (missing.length) {
    const names = missing.map((k) => CORE.kit.find((x) => x.id === k).name).join(", ");
    box.append(el("p", "kitnote", "This needs kit you haven't ticked: " + names + ". You can still answer if you have it."));
  }
  const multi = c.kind === "multi";
  if (multi) box.append(el("p", "hint", "Tick all you can see, then press Done. Leave unticked if unsure."));
  const opts = el("div", "options");
  for (const s of c.states) {
    const b = el("button", "option");
    b.type = "button";
    const pic = el("div", "placeholder", s.picture ? "picture" : "picture to come");
    b.append(pic, el("span", null, s.label));
    b.title = s.tells_you;
    if (multi ? state.pendingTicks.has(s.id) : state.answers[id] === s.id) b.classList.add("chosen");
    b.onclick = () => {
      if (!multi) return record(id, "answer", s.id);
      state.pendingTicks.has(s.id) ? state.pendingTicks.delete(s.id) : state.pendingTicks.add(s.id);
      renderCurrent();
    };
    opts.append(b);
  }
  box.append(opts);
  const actions = el("div", "actions");
  if (multi) {
    const done = el("button", null, "Done");
    done.onclick = () => record(id, "answer", [...state.pendingTicks]);
    actions.append(done);
  }
  const notSure = el("button", "secondary", "Not sure");
  notSure.onclick = () => record(id, "not_sure");
  const skip = el("button", "secondary", "Skip");
  skip.onclick = () => record(id, "skip");
  actions.append(notSure, skip);
  box.append(actions);
}

function renderResult() {
  $("phrase").textContent = RESULT.phrase;
  const path = $("path");
  path.replaceChildren();
  for (const n of RESULT.report.path) path.append(el("li", null, `${n.name} — ${n.p}`));
  const list = $("candidates");
  list.replaceChildren();
  const shown = state.showAll ? RESULT.candidates : RESULT.candidates.slice(0, state.mode === "beginner" ? 5 : 10);
  for (const c of shown) {
    const li = el("li");
    const name = el("span", null, c.name + " ");
    name.append(el("span", "grp", c.group));
    const bar = el("div", "bar");
    const fill = el("span");
    fill.style.width = (c.p * 100).toFixed(1) + "%";
    bar.append(fill);
    li.append(name, el("span", "p", c.pct), bar);
    list.append(li);
  }
  $("more").textContent = state.showAll ? "Show fewer" : `Show all ${RESULT.candidates.length}`;
}

function renderAnswers() {
  const list = $("answers");
  list.replaceChildren();
  $("answers-empty").hidden = state.order.length > 0;
  for (const id of state.order) {
    const li = el("li");
    if (id in state.skipped) li.classList.add("skipped");
    const left = el("span", null, CHAR[id].question + " ");
    left.append(el("span", "a", answerText(id)));
    const btns = el("span");
    const change = el("button", "secondary", "change");
    change.onclick = () => reopen(id);
    const remove = el("button", "secondary", "✕");
    remove.title = "Remove this answer";
    remove.onclick = () => record(id, "remove");
    btns.append(change, " ", remove);
    li.append(left, btns);
    list.append(li);
  }
}

function renderTrace() {
  const list = $("trace");
  list.replaceChildren();
  $("trace-empty").hidden = RESULT.trace.length > 0;
  for (const step of RESULT.trace) {
    const li = el("li");
    const said = step.answers.length ? step.answers.map((a) => a.label).join("; ") : "nothing ticked";
    li.append(el("div", "said", `${step.question} → ${said}`));
    for (const a of step.answers) li.append(el("div", "tells", a.tells_you));
    const chips = el("div", "chips");
    for (const ch of step.changes) {
      const cls = ch.factor >= 1.25 ? "chip up" : ch.factor <= 0.8 ? "chip down" : "chip";
      const chip = el("span", cls, `${ch.name}: ${ch.phrase} (${ch.before} → ${ch.after})`);
      chips.append(chip);
    }
    li.append(chips);
    list.append(li);
  }
}

// -- Specimen testing: save each run (TESTING.md section 5) -----------------

function remember(key, value) {
  try { localStorage.setItem("gr-" + key, value); } catch (e) { /* not available */ }
}
function recall(key) {
  try { return localStorage.getItem("gr-" + key) || ""; } catch (e) { return ""; }
}

function testMsg(text, cls) {
  $("t-msg").textContent = text;
  $("t-msg").className = "hint " + (cls || "");
}

function initTesting() {
  for (const x of CORE.experience) {
    const o = el("option", null, x.label);
    o.value = x.id;
    $("t-experience").append(o);
  }
  $("t-tester").value = recall("tester");
  $("t-experience").value = recall("experience");
  $("t-tester").onchange = () => remember("tester", $("t-tester").value.trim());
  $("t-experience").onchange = () => remember("experience", $("t-experience").value);
  for (const c of CORE.confidence) {
    const b = el("button", "secondary", c.label);
    b.type = "button";
    b.onclick = () => saveTest(c.id);
    $("t-confidence").append(b);
  }
  $("t-save").onclick = () => {
    const missing = [];
    if (!$("t-specimen").value.trim()) missing.push("specimen number");
    if (!$("t-tester").value.trim()) missing.push("tester");
    if (!$("t-experience").value) missing.push("experience");
    if (missing.length) return testMsg("Please fill in: " + missing.join(", ") + ".", "bad");
    if (!state.order.length) return testMsg("Answer some questions first.", "bad");
    $("t-save").hidden = true;
    $("t-confirm").hidden = false;
    testMsg("");
  };
  $("t-cancel").onclick = () => { $("t-confirm").hidden = true; $("t-save").hidden = false; };
}

async function saveTest(confidence) {
  const specimen = $("t-specimen").value.trim();
  const body = {
    tester: $("t-tester").value.trim(), experience: $("t-experience").value, specimen,
    confidence, notes: $("t-notes").value.trim(),
    order: state.order,
    answers: state.order.filter((id) => id in state.answers).map((id) => ({ char: id, state: state.answers[id] })),
    skipped: state.skipped,
    kit: [...state.kit], mode: state.mode, find_context: state.context || null,
  };
  const res = await fetch("/api/save-test", { method: "POST", headers: { "Content-Type": "application/json" },
                                               body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) return testMsg(data.error || "Could not save.", "bad");
  $("t-confirm").hidden = true;
  $("t-save").hidden = false;
  $("t-specimen").value = "";
  $("t-notes").value = "";
  restart();
  testMsg(`Saved ✓ specimen ${specimen} (${data.count} test${data.count === 1 ? "" : "s"} in this file). Ready for the next specimen.`, "ok");
}

init().catch((e) => showError("Could not start: " + e));
