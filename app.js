const state = { data: null, selected: null, month: null };
const format = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" });
const number = (value, suffix = "") => Number.isFinite(value) ? `${Math.round(value)}${suffix}` : "—";

fetch("data/health-history.json").then(r => r.json()).then(data => {
  state.data = data; state.selected = data.days.at(-1)?.date; state.month = new Date(`${state.selected}T12:00:00`); render();
}).catch(() => { document.body.innerHTML = "<main class='shell'><h1>Нет данных</h1><p class='muted'>Сначала запустите import_whoop.py.</p></main>" });

function current() { return state.data.days.find(day => day.date === state.selected); }
function render() { renderCalendar(); renderDay(current()); }
function renderDay(day) {
  document.querySelector("#selected-date").textContent = format.format(new Date(`${day.date}T12:00:00`));
  document.querySelector("#summary").innerHTML = card("Stress Score", number(day.stressScore), day.stressScore == null ? "недостаточно baseline" : "экспериментальный") + card("HRV", number(day.hrv, " мс"), "RMSSD") + card("RHR", number(day.rhr, " bpm"), "пульс в покое") + card("Цикл", day.cycleDay ? `день ${day.cycleDay}` : "—", "по событиям");
  const sleep = day.sleep || {};
  document.querySelector("#sleep").innerHTML = metrics([["Длительность", number(sleep.asleepMinutes / 60, " ч")], ["Долг сна", number(sleep.debtMinutes, " мин")], ["Эффективность", number(sleep.efficiency, "%")], ["Согласованность", number(sleep.consistency, "%")]]);
  const tags = [...(day.symptoms || []), ...(day.context || []), ...(day.workouts || []).map(w => w.activity)];
  document.querySelector("#context").innerHTML = tags.length ? tags.map(tag => `<span class='tag'>${tag}</span>`).join("") : "<p class='empty'>Нет отмеченного контекста.</p>";
}
function card(label, value, note) { return `<article class='card'><label>${label}</label><strong>${value}</strong><span class='muted'>${note}</span></article>`; }
function metrics(items) { return items.map(([label, value]) => `<div class='metric'><span>${label}</span><strong>${value}</strong></div>`).join(""); }
function renderCalendar() {
  const m = state.month, year = m.getFullYear(), month = m.getMonth(), first = new Date(year, month, 1), last = new Date(year, month + 1, 0);
  document.querySelector("#month").textContent = new Intl.DateTimeFormat("ru-RU", { month:"long", year:"numeric" }).format(m);
  const days = state.data.days.reduce((map, day) => (map[day.date] = day, map), {}); let html = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"].map(x => `<div class='weekday'>${x}</div>`).join("");
  const lead = (first.getDay() + 6) % 7; html += "<i></i>".repeat(lead);
  for (let n = 1; n <= last.getDate(); n++) { const key = `${year}-${String(month + 1).padStart(2, "0")}-${String(n).padStart(2, "0")}`, record = days[key], selected = key === state.selected; html += `<button class='day ${record ? "has-data" : ""} ${selected ? "selected" : ""}' data-date='${key}'>${n}${record?.stressScore != null ? `<small>${Math.round(record.stressScore)}</small>` : ""}</button>`; }
  document.querySelector("#calendar").innerHTML = html;
  document.querySelectorAll(".day.has-data").forEach(button => button.onclick = () => { state.selected = button.dataset.date; state.month = new Date(`${state.selected}T12:00:00`); render(); });
}
document.querySelector("#previous").onclick = () => { state.month.setMonth(state.month.getMonth() - 1); renderCalendar(); };
document.querySelector("#next").onclick = () => { state.month.setMonth(state.month.getMonth() + 1); renderCalendar(); };
