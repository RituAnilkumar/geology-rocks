// SPDX-FileCopyrightText: Geology Rocks contributors
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Test results page: lists saved specimen tests and records the true rock type.
"use strict";

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
};

function showError(msg) {
  $("error").textContent = msg;
  $("error").hidden = false;
  setTimeout(() => ($("error").hidden = true), 6000);
}

function rockSelect(rocks, value) {
  const sel = el("select");
  const blank = el("option", null, "— not filled in —");
  blank.value = "";
  sel.append(blank);
  let group = null;
  let known = value === "" || value === "not_in_key";
  for (const r of rocks) {
    if (!group || group.label !== r.group) {
      group = el("optgroup");
      group.label = r.group;
      sel.append(group);
    }
    const o = el("option", null, r.name);
    o.value = r.id;
    group.append(o);
    if (r.id === value) known = true;
  }
  const nik = el("option", null, "Not in the key");
  nik.value = "not_in_key";
  sel.append(nik);
  if (!known) {                       // typed by hand in a spreadsheet
    const o = el("option", null, value + " (as typed)");
    o.value = value;
    sel.append(o);
  }
  sel.value = value;
  return sel;
}

async function load() {
  const data = await (await fetch("/api/tests")).json();
  $("folder").textContent = data.folder;
  const filled = data.tests.filter((t) => t.true_rock).length;
  $("count").textContent = `${data.tests.length} test(s) saved; true rock type filled in for ${filled}.`;
  const body = $("tests").querySelector("tbody");
  body.replaceChildren();
  if (!data.tests.length) {
    const tr = el("tr");
    const td = el("td", "hint", "No tests saved yet. Use “Save this test” on the key page.");
    td.colSpan = 9;
    tr.append(td);
    body.append(tr);
  }
  for (const t of data.tests) {
    const tr = el("tr");
    const when = t.saved_at.replace("T", " ").slice(0, 16);
    const sel = rockSelect(data.rocks, t.true_rock);
    const status = el("span", "saved");
    sel.onchange = async () => {
      status.textContent = "";
      const res = await fetch("/api/set-truth", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_id: t.run_id, true_rock: sel.value }) });
      if (!res.ok) { showError((await res.json()).error || "Could not save."); return; }
      status.textContent = " ✓";
    };
    const truth = el("td");
    truth.append(sel, status);
    tr.append(el("td", null, when), el("td", null, t.specimen), el("td", null, t.tester),
      el("td", null, t.experience), el("td", null, t.result),
      el("td", null, t.top_rock + (t.top_rock_p ? ` (${Math.round(t.top_rock_p * 100)}%)` : "")),
      el("td", null, t.confidence), truth, el("td", "notes-cell", t.notes));
    if (t.file && t.file !== "test-runs.csv") tr.title = "From " + t.file;
    body.append(tr);
  }
}

load().catch((e) => showError("Could not load tests: " + e));
