/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ─── Layout constants ────────────────────────────────────────────────────────
const PIXELS_PER_HOUR = 100;
const HOUR_START = 0;   // 12 AM
const HOUR_END = 24;  // 12 AM next day
const VISIBLE_HOURS = HOUR_END - HOUR_START;
const DAY_WIDTH = VISIBLE_HOURS * PIXELS_PER_HOUR; // 1440px/day
const ROW_HEIGHT = 64;  // px per row

// ─── Status colours & labels ─────────────────────────────────────────────────
const STATE_COLORS = {
    pending: "#a855f7",
    ready: "#22c55e",
    progress: "#3b82f6",
    waiting: "#f59e0b",
    blocked: "#ef4444",
    done: "#6b7280",
    cancel: "#d1d5db",
};
const STATE_LABELS = {
    pending: "Pending",
    ready: "Ready",
    progress: "In Progress",
    waiting: "Waiting",
    blocked: "Blocked",
    done: "Done",
    cancel: "Cancelled",
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
function toOdooUTC(date) {
    return date.toISOString().replace("T", " ").substring(0, 19);
}
function fromOdooUTC(str) {
    if (!str) return null;
    return new Date(str.replace(" ", "T") + "Z");
}
function midnightLocal(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
}

// ─── Main Component ──────────────────────────────────────────────────────────
export class MrpGanttView extends Component {
    static template = "mrp_workcenter_gantt.GanttView";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        const today = midnightLocal(new Date());
        this.state = useState({
            zoom: "week",
            rangeStart: today,
            workcenters: [],   // all active WCs
            hiddenWcIds: [],   // WCs hidden from view
            workorders: [],   // enriched WOs
            users: [],   // list of active users/operators
            productions: {},   // productionId → {user, name}
            loading: true,
            showManager: false,
            showEditModal: false,
            editingWo: null, // copy of WO being edited
            newMachineName: "",
            showFreeSlots: true,
        });
        this._drag = {};
        onMounted(() => this._loadData());
    }

    // ── Actions ───────────────────────────────────────────────────────────────
    onCreateJob() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "New Manufacturing Order",
            res_model: "mrp.production",
            views: [[false, "form"]],
            target: "current",
            context: {
                default_date_start: toOdooUTC(new Date()),
            }
        });
    }

    onEditWo(wo) {
        const start = fromOdooUTC(wo.date_start);
        // Format date to local datetime-local input string: YYYY-MM-DDTHH:MM
        const offset = start.getTimezoneOffset();
        const localDate = new Date(start.getTime() - (offset * 60 * 1000));
        const dateStr = localDate.toISOString().substring(0, 16);

        this.state.editingWo = {
            id: wo.id,
            name: wo.name,
            workcenter_id: wo.workcenter_id ? wo.workcenter_id[0] : false,
            user_id: wo._userId || false,
            duration_expected: ((wo.duration_expected || 60) / 60).toFixed(2), // minutes to hours
            date_start: dateStr,
            state: wo.state,
            production_id: wo.production_id ? wo.production_id[0] : false,
        };
        this.state.showEditModal = true;
    }

    async saveEdit() {
        const wo = this.state.editingWo;
        if (!wo.date_start) {
            this.notification.add("Please select a start date and time.", { type: "warning" });
            return;
        }

        // Convert the local input string (YYYY-MM-DDTHH:MM) back to UTC Odoo string
        const localDate = new Date(wo.date_start);
        const odooDateStr = toOdooUTC(localDate);

        this.state.loading = true;
        try {
            // 1. Update Work Order details (convert hours input back to minutes)
            await this.orm.write("mrp.workorder", [wo.id], {
                workcenter_id: wo.workcenter_id,
                duration_expected: parseFloat(wo.duration_expected) * 60,
                date_start: odooDateStr,
                state: wo.state,
            });

            // 2. Update Responsible operator on the MO
            if (wo.production_id && wo.user_id) {
                await this.orm.write("mrp.production", [wo.production_id], {
                    user_id: wo.user_id,
                });
            }

            this.state.showEditModal = false;
            this.notification.add("Job details updated successfully ✓", { type: "success" });
            await this._loadData();
        } catch (e) {
            console.error(e);
            this.notification.add("Failed to save changes. Make sure values are correct.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async deleteJob() {
        const wo = this.state.editingWo;
        if (!confirm(`Are you sure you want to delete/cancel this job (${wo.name})?`)) return;

        this.state.loading = true;
        try {
            // Cancel the work order, which removes it from the active Gantt view
            await this.orm.write("mrp.workorder", [wo.id], { state: "cancel" });
            this.state.showEditModal = false;
            this.notification.add("Job deleted successfully ✓", { type: "success" });
            await this._loadData();
        } catch (e) {
            console.error(e);
            this.notification.add("Failed to delete the job.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    closeEditModal() {
        this.state.showEditModal = false;
        this.state.editingWo = null;
    }

    // ── Range ─────────────────────────────────────────────────────────────────
    get rangeEnd() {
        const end = new Date(this.state.rangeStart);
        const days = { day: 1, week: 7, month: 30 }[this.state.zoom] ?? 7;
        end.setDate(end.getDate() + days);
        return end;
    }
    get totalWidth() {
        return ((this.rangeEnd - this.state.rangeStart) / 86_400_000) * DAY_WIDTH;
    }
    get dayWidth() { return DAY_WIDTH; }
    get headerDays() {
        const days = [], cur = new Date(this.state.rangeStart);
        while (cur < this.rangeEnd) { days.push(new Date(cur)); cur.setDate(cur.getDate() + 1); }
        return days;
    }
    get visibleWorkcenters() {
        return this.state.workcenters.filter(wc => !this.state.hiddenWcIds.includes(wc.id));
    }
    get rangeLabel() {
        const M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const D = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        const s = this.state.rangeStart;
        const e = new Date(this.rangeEnd); e.setDate(e.getDate() - 1);
        if (this.state.zoom === 'day')
            return `${D[s.getDay()]}, ${s.getDate()} ${M[s.getMonth()]} ${s.getFullYear()}`;
        if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear())
            return `${s.getDate()} – ${e.getDate()} ${M[s.getMonth()]} ${s.getFullYear()}`;
        return `${s.getDate()} ${M[s.getMonth()]} – ${e.getDate()} ${M[e.getMonth()]} ${s.getFullYear()}`;
    }

    /** Returns hour slots for day-zoom header: [{ label, leftPx }] */
    get headerHours() {
        const slots = [];
        for (let h = HOUR_START; h < HOUR_END; h++) {
            slots.push({
                label: this.formatHour(h),
                leftPx: (h - HOUR_START) * PIXELS_PER_HOUR,
            });
        }
        return slots;
    }

    formatHour(h) {
        if (h === 0) return '12 AM';
        if (h === 12) return '12 PM';
        return h < 12 ? `${h} AM` : `${h - 12} PM`;
    }

    // ── Data loading ──────────────────────────────────────────────────────────
    async _loadData() {
        this.state.loading = true;
        try {
            const [workcenters, workorders, users] = await Promise.all([
                this.orm.searchRead(
                    "mrp.workcenter",
                    [["active", "=", true]],
                    ["id", "name"],
                    { order: "name asc" }
                ),
                this.orm.searchRead(
                    "mrp.workorder",
                    [
                        ["date_start", "!=", false],
                        ["state", "not in", ["cancel"]],
                        ["date_start", "<", toOdooUTC(this.rangeEnd)],
                    ],
                    ["id", "name", "workcenter_id", "date_start",
                        "duration_expected", "state", "production_id"],
                    { limit: 1000 }
                ),
                this.orm.searchRead(
                    "res.users",
                    [["active", "=", true], ["share", "=", false]],
                    ["id", "name"],
                    { order: "name asc" }
                ),
            ]);

            // Enrich work orders with MO info (responsible user, MO name)
            const prodIds = [...new Set(workorders.map(w => w.production_id?.[0]).filter(Boolean))];
            const productions = prodIds.length
                ? await this.orm.read("mrp.production", prodIds, ["id", "name", "user_id"])
                : [];
            const prodMap = Object.fromEntries(productions.map(p => [p.id, p]));

            workorders.forEach(wo => {
                const prod = wo.production_id ? prodMap[wo.production_id[0]] : null;
                wo._moRef = prod?.name ?? "—";
                wo._userName = prod?.user_id?.[1] ?? "Unassigned";
                wo._userId = prod?.user_id?.[0] ?? false;
            });

            this.state.workcenters = workcenters;
            this.state.workorders = workorders;
            this.state.users = users;
        } catch (e) {
            console.error(e);
            this.notification.add("Failed to load schedule data.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    // ── Per-WC data helpers ───────────────────────────────────────────────────
    getWorkordersForWC(wcId) {
        return this.state.workorders.filter(w => w.workcenter_id?.[0] === wcId);
    }

    /** Return capacity summary string for a work center row header */
    getWcStats(wcId) {
        const wos = this.getWorkordersForWC(wcId)
            .filter(w => w.state !== "done" && w.state !== "cancel");
        const totalH = (wos.reduce((s, w) => s + (w.duration_expected || 0), 0) / 60).toFixed(1);
        return `${wos.length} job${wos.length !== 1 ? "s" : ""}  ·  ${totalH}h booked`;
    }

    /**
     * Compute free-time slots for a work center within the visible range.
     * Returns array of { style } objects for rendering green strips.
     */
    getFreeSlots(wcId) {
        if (!this.state.showFreeSlots) return [];

        const busyIntervals = this.getWorkordersForWC(wcId)
            .filter(w => fromOdooUTC(w.date_start))
            .map(w => {
                const s = fromOdooUTC(w.date_start);
                const e = new Date(s.getTime() + (w.duration_expected || 60) * 60_000);
                return { s, e };
            })
            .sort((a, b) => a.s - b.s);

        const slots = [];
        this.headerDays.forEach((day, di) => {
            const dayStart = new Date(day); dayStart.setHours(HOUR_START, 0, 0, 0);
            const dayEnd = new Date(day); dayEnd.setHours(HOUR_END, 0, 0, 0);
            const busy = busyIntervals.filter(i => i.e > dayStart && i.s < dayEnd);

            const pushSlot = (from, to) => {
                const wPx = (to - from) / 3_600_000 * PIXELS_PER_HOUR;
                if (wPx < 8) return;
                const h = Math.max(from.getHours() + from.getMinutes() / 60, HOUR_START);
                const lPx = di * DAY_WIDTH + (h - HOUR_START) * PIXELS_PER_HOUR;
                slots.push({ style: `left:${lPx}px; width:${wPx}px;` });
            };

            if (!busy.length) {
                pushSlot(dayStart, dayEnd);
                return;
            }

            let prev = dayStart;
            for (const { s, e } of busy) {
                const clampS = s < dayStart ? dayStart : s;
                if (clampS > prev) pushSlot(prev, clampS);
                prev = e > prev ? e : prev;
            }
            if (prev < dayEnd) pushSlot(prev, dayEnd);
        });
        return slots;
    }

    // ── Pill styles ───────────────────────────────────────────────────────────
    computePillStyle(wo) {
        const start = fromOdooUTC(wo.date_start);
        if (!start) return "display:none";
        const durMs = (wo.duration_expected || 60) * 60_000;
        const end = new Date(start.getTime() + durMs);
        if (end < this.state.rangeStart || start >= this.rangeEnd) return "display:none";

        const offsetHours = (start - this.state.rangeStart) / 3_600_000;
        const dayIndex = Math.floor(offsetHours / 24);
        const hourOfDay = start.getHours() + start.getMinutes() / 60;
        const leftPx = dayIndex * DAY_WIDTH + (hourOfDay - HOUR_START) * PIXELS_PER_HOUR;
        const widthPx = Math.max((wo.duration_expected || 60) / 60 * PIXELS_PER_HOUR, 36);
        const color = STATE_COLORS[wo.state] ?? STATE_COLORS.ready;

        return `left:${leftPx}px; width:${widthPx}px; background-color:${color};`;
    }

    computeDayStripeStyle(i) {
        return `left:${i * DAY_WIDTH}px; width:${DAY_WIDTH}px;`;
    }

    get todayLineStyle() {
        const now = new Date(), s = this.state.rangeStart;
        if (now < s || now >= this.rangeEnd) return "display:none";
        const di = Math.floor((now - s) / 86_400_000);
        const h = now.getHours() + now.getMinutes() / 60;
        return `left:${di * DAY_WIDTH + (h - HOUR_START) * PIXELS_PER_HOUR}px`;
    }

    isToday(day) {
        const t = new Date();
        return day.getFullYear() === t.getFullYear() &&
            day.getMonth() === t.getMonth() &&
            day.getDate() === t.getDate();
    }

    formatDayHeader(day) {
        const D = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        return `${D[day.getDay()]} ${day.getDate()}/${day.getMonth() + 1}`;
    }

    // ── Tooltip ───────────────────────────────────────────────────────────────
    getTooltip(wo) {
        const start = fromOdooUTC(wo.date_start);
        const durH = ((wo.duration_expected || 0) / 60).toFixed(1);
        return [
            `📋 ${wo.name}`,
            `🔧 MO: ${wo._moRef}`,
            `👤 ${wo._userName}`,
            `⏰ Start: ${start ? start.toLocaleString() : "—"}`,
            `⌛ Duration: ${durH} h`,
            `🔵 Status: ${STATE_LABELS[wo.state] ?? wo.state}`,
        ].join("\n");
    }

    getStateLabel(s) { return STATE_LABELS[s] ?? s; }
    getStateColor(s) { return STATE_COLORS[s] ?? STATE_COLORS.ready; }

    // ── Navigation ────────────────────────────────────────────────────────────
    _shift(dir) {
        const d = { day: 1, week: 7, month: 30 }[this.state.zoom] ?? 7;
        const s = new Date(this.state.rangeStart);
        s.setDate(s.getDate() + dir * d);
        this.state.rangeStart = s;
        this._loadData();
    }
    onPrev() { this._shift(-1); }
    onNext() { this._shift(+1); }
    onToday() { this.state.rangeStart = midnightLocal(new Date()); this._loadData(); }
    onZoom(z) { this.state.zoom = z; this._loadData(); }
    onWheel(ev) {
        // Pinch-to-zoom or Ctrl+Scroll Wheel triggers this
        if (ev.ctrlKey) {
            ev.preventDefault();
            const zooms = ["day", "week", "month"];
            const currentIdx = zooms.indexOf(this.state.zoom);
            if (ev.deltaY < 0) {
                // Scroll UP -> Zoom IN
                if (currentIdx > 0) {
                    this.onZoom(zooms[currentIdx - 1]);
                }
            } else {
                // Scroll DOWN -> Zoom OUT
                if (currentIdx < zooms.length - 1) {
                    this.onZoom(zooms[currentIdx + 1]);
                }
            }
        }
    }

    // ── Machine Manager ───────────────────────────────────────────────────────
    toggleManager() { this.state.showManager = !this.state.showManager; }

    isWcVisible(wcId) { return !this.state.hiddenWcIds.includes(wcId); }

    toggleWcVisibility(wcId) {
        const h = this.state.hiddenWcIds, i = h.indexOf(wcId);
        if (i === -1) h.push(wcId); else h.splice(i, 1);
    }

    async addNewMachine() {
        const name = this.state.newMachineName.trim();
        if (!name) {
            this.notification.add("Please enter a machine name.", { type: "warning" });
            return;
        }
        try {
            await this.orm.create("mrp.workcenter", [{ name, default_capacity: 1 }]);
            this.state.newMachineName = "";
            this.notification.add(`"${name}" created successfully ✓`, { type: "success" });
            await this._loadData();
        } catch (_e) {
            this.notification.add("Failed to create work center.", { type: "danger" });
        }
    }

    async deactivateMachine(wcId, wcName) {
        if (!confirm(`Remove "${wcName}" from the system? It will be deactivated.`)) return;
        try {
            await this.orm.write("mrp.workcenter", [wcId], { active: false });
            this.notification.add(`"${wcName}" deactivated ✓`, { type: "success" });
            await this._loadData();
        } catch (_e) {
            this.notification.add("Failed to deactivate.", { type: "danger" });
        }
    }

    onNewMachineInput(ev) { this.state.newMachineName = ev.target.value; }

    onNewMachineKeydown(ev) { if (ev.key === "Enter") this.addNewMachine(); }

    // ── Drag & Drop ───────────────────────────────────────────────────────────
    onDragStart(ev, woId) {
        this._drag = { woId, startX: ev.clientX };
        ev.dataTransfer.effectAllowed = "move";
        setTimeout(() => { ev.target && (ev.target.style.opacity = "0.45"); }, 0);
    }
    onDragEnd(ev) { ev.target && (ev.target.style.opacity = "1"); }
    onDragOver(ev) { ev.preventDefault(); ev.dataTransfer.dropEffect = "move"; }

    async onDrop(ev, wcId) {
        ev.preventDefault();
        const { woId, startX } = this._drag;
        if (!woId) return;
        const wo = this.state.workorders.find(w => w.id === woId);
        if (!wo) return;
        const dH = (ev.clientX - startX) / PIXELS_PER_HOUR;
        const newStart = new Date(fromOdooUTC(wo.date_start).getTime() + dH * 3_600_000);
        try {
            await this.orm.write("mrp.workorder", [woId], {
                date_start: toOdooUTC(newStart),
                workcenter_id: wcId,
                duration_expected: wo.duration_expected, // Lock the original duration!
            });
            this.notification.add("Work order rescheduled ✓", { type: "success" });
            await this._loadData();
        } catch (_e) {
            this.notification.add("Could not reschedule — the work order may be locked.", { type: "warning" });
        }
    }

    // ── Legend ────────────────────────────────────────────────────────────────
    get legendItems() {
        return [
            { label: "Ready", color: STATE_COLORS.ready },
            { label: "In Progress", color: STATE_COLORS.progress },
            { label: "Waiting", color: STATE_COLORS.waiting },
            { label: "Pending", color: STATE_COLORS.pending },
            { label: "Blocked", color: STATE_COLORS.blocked },
            { label: "Done", color: STATE_COLORS.done },
            { label: "Free Time", color: "#d1fae5", border: true },
        ];
    }
}

registry.category("actions").add("mrp_gantt_client_action", MrpGanttView);
