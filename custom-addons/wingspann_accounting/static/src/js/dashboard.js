/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onPatched, onWillUnmount, useState, useRef } from "@odoo/owl";

export class WingspannAccountingDashboard extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.chartCanvas = useRef("budgetChart");

        this.state = useState({
            /** Budget panel data */
            budgetData: {
                allocated_budget: 0,
                total_expenses: 0,
                remaining_balance: 0,
                expense_categories: [],
                po_commitment: 0,
                pr_commitment: 0,
                currency_symbol: '₹',
                fy_label: 'FY 2026-27',
            },
            /** Legacy accounting panel data */
            data: {
                cash_balance: 0.0,
                receivables: 0.0,
                payables: 0.0,
                recent_moves: [],
                currency_symbol: '₹',
                incoming_monthly: 0.0,
                incoming_weekly: 0.0,
                recent_incoming: [],
                outgoing_monthly: 0.0,
                outgoing_weekly: 0.0,
                recent_outgoing: [],
            },
            isLoading: true,
            showAnalyticsModal: false,
            analyticsType: 'receivables',
        });

        /** Stored chart segment metadata for click-hit-testing */
        this._chartSegments = [];

        onWillStart(async () => {
            await Promise.all([
                this._loadBudgetData(),
                this._loadLegacyData(),
            ]);
        });

        onMounted(() => {
            this._renderDonutChart();
            // Auto-refresh every 60 seconds
            this._refreshInterval = setInterval(async () => {
                await Promise.all([
                    this._loadBudgetData(),
                    this._loadLegacyData(),
                ]);
            }, 60000);
        });

        onWillUnmount(() => {
            // Clean up interval to prevent memory leaks
            if (this._refreshInterval) {
                clearInterval(this._refreshInterval);
                this._refreshInterval = null;
            }
        });

        onPatched(() => {
            if (!this.state.isLoading) {
                this._renderDonutChart();
            }
        });
    }

    // ─────────────────────────────────────────────────────────────────
    // Data loading
    // ─────────────────────────────────────────────────────────────────

    async _loadBudgetData() {
        try {
            const result = await this.orm.call(
                "wingspann.accounting.dashboard",
                "get_budget_dashboard_data",
                []
            );
            this.state.budgetData = result;
        } catch (e) {
            console.error("[WingspannDashboard] Budget data load error:", e);
        }
    }

    async _loadLegacyData() {
        try {
            const result = await this.orm.call(
                "wingspann.accounting.dashboard",
                "get_dashboard_data",
                []
            );
            this.state.data = result;
        } catch (e) {
            console.error("[WingspannDashboard] Legacy data load error:", e);
        } finally {
            this.state.isLoading = false;
        }
    }

    // ─────────────────────────────────────────────────────────────────
    // Donut Chart
    // ─────────────────────────────────────────────────────────────────

    _renderDonutChart() {
        const canvas = this.chartCanvas.el;
        if (!canvas || this.state.isLoading) return;

        const bd = this.state.budgetData;
        const total = bd.allocated_budget > 0 ? bd.allocated_budget : 1;
        const expAmt = Math.min(Math.max(bd.total_expenses, 0), total);
        const remAmt = Math.max(total - expAmt, 0);

        // Set canvas size to match CSS size (retina-safe)
        const cssW = canvas.clientWidth || 340;
        const cssH = canvas.clientHeight || 340;
        const dpr = window.devicePixelRatio || 1;
        canvas.width = cssW * dpr;
        canvas.height = cssH * dpr;

        const ctx = canvas.getContext('2d');
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, cssW, cssH);

        const cx = cssW / 2;
        const cy = cssH / 2;
        // Increase radius by ~15% to 0.92 to match the new request
        const outerR = Math.min(cx, cy) * 0.92;
        // Pull it in the middle a bit more (reduce explode)
        const explode = 8;

        const segments = [
            { value: expAmt, color: '#e53e3e', label: 'Total Expenses', isExpense: true },
            { value: remAmt, color: '#4ddff5ff', label: 'Available Balance', isExpense: false },
        ];

        this._chartSegments = [];
        let startAngle = -Math.PI / 2;   // start at top (12 o'clock)

        for (const seg of segments) {
            if (seg.value <= 0) { this._chartSegments.push(null); continue; }

            const sliceAngle = (seg.value / total) * 2 * Math.PI;
            const midAngle = startAngle + sliceAngle / 2;
            const ox = seg.isExpense ? Math.cos(midAngle) * explode : 0;
            const oy = seg.isExpense ? Math.sin(midAngle) * explode : 0;
            const segCx = cx + ox;
            const segCy = cy + oy;

            // ── Draw segment ──────────────────────────────────────────
            ctx.save();
            if (seg.isExpense) {
                ctx.shadowColor = 'rgba(229, 62, 62, 0.7)';
                ctx.shadowBlur = 25;
            }
            ctx.beginPath();
            ctx.moveTo(segCx, segCy);
            ctx.arc(segCx, segCy, outerR, startAngle, startAngle + sliceAngle);
            ctx.closePath();

            // Add a white stroke around the slice to emphasize separation
            ctx.fillStyle = seg.color;
            ctx.fill();

            if (seg.isExpense) {
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 3;
                ctx.stroke();
            }
            ctx.restore();

            // ── Store for click detection ─────────────────────────────
            this._chartSegments.push({
                startAngle,
                endAngle: startAngle + sliceAngle,
                cx: segCx, cy: segCy,
                outerR, innerR: 0,
                isExpense: seg.isExpense,
            });

            // ── Label logic ───────────────────────────────────────────
            if (sliceAngle > 0.05) {
                const isNarrow = sliceAngle < 0.9; // Less than ~14%

                // For a solid pie, center of area is roughly at 2/3 of radius.
                // If it's narrow, push the text further out toward the edge where the slice is wider
                const labelR = isNarrow ? outerR * 0.85 : outerR * 0.65;
                const labelAngle = midAngle;

                const lx = segCx + Math.cos(labelAngle) * labelR;
                const ly = segCy + Math.sin(labelAngle) * labelR;

                const pct = Math.round((seg.value / total) * 100);
                const sym = bd.currency_symbol;
                const fs = Math.max(10, Math.min(13, cssW / 28));

                ctx.save();
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                // White text inside the slice
                ctx.fillStyle = '#ffffff';
                ctx.font = `500 ${fs}px Inter, sans-serif`;
                ctx.fillText(`${seg.label}:`, lx, ly - 10);

                ctx.fillStyle = '#ffffff';
                ctx.font = `bold ${fs - 1}px Inter, sans-serif`;
                const displayAmt = this.formatCurrency(seg.value);
                ctx.fillText(`${displayAmt} (${pct}%)`, lx, ly + 10);

                ctx.restore();
            }

            startAngle += sliceAngle;
        }
    }

    /** Handle click on the canvas — drill-down if expense slice was clicked */
    onChartClick(ev) {
        const canvas = this.chartCanvas.el;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const mx = ev.clientX - rect.left;
        const my = ev.clientY - rect.top;

        for (const seg of this._chartSegments) {
            if (!seg || !seg.isExpense) continue;
            const dx = mx - seg.cx;
            const dy = my - seg.cy;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < seg.innerR || dist > seg.outerR) continue;

            // Normalize angles to [0, 2π] for reliable comparison
            const norm = (a) => ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
            const a = norm(Math.atan2(dy, dx));
            const s = norm(seg.startAngle);
            const e = norm(seg.endAngle);

            const inSlice = s <= e ? (a >= s && a <= e) : (a >= s || a <= e);
            if (inSlice) {
                this.drillDownExpenses();
                return;
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────
    // Actions
    // ─────────────────────────────────────────────────────────────────

    drillDownExpenses() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Expense Details — Vendor Bills',
            res_model: 'account.move',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['move_type', '=', 'in_invoice'], ['state', '=', 'posted']],
        });
    }

    async setBudget() {
        const current = this.state.budgetData.allocated_budget || 1000000;
        const input = window.prompt(
            `Set Allocated Budget for ${this.state.budgetData.fy_label}\n(Current: ₹ ${Math.round(current).toLocaleString('en-IN')})`,
            String(Math.round(current))
        );
        if (input === null) return; // user cancelled
        const val = parseFloat(input.replace(/[^0-9.]/g, ''));
        if (isNaN(val) || val <= 0) {
            window.alert('Please enter a valid positive number.');
            return;
        }
        await this.orm.call(
            'wingspann.accounting.dashboard',
            'set_allocated_budget',
            [val]
        );
        await this._loadBudgetData();
    }

    async refreshNow() {
        await Promise.all([
            this._loadBudgetData(),
            this._loadLegacyData(),
        ]);
    }

    openPOList() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Open PO Commitments',
            res_model: 'purchase.order',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'purchase']],
        });
    }

    openPRList() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Pending Purchase Requests (RFQ)',
            res_model: 'purchase.order',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', 'in', ['draft', 'sent']]],
        });
    }

    createInvoice() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Customer Invoice',
            res_model: 'account.move',
            view_mode: 'form',
            views: [[false, 'form']],
            context: { default_move_type: 'out_invoice' },
        });
    }

    createBill() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Vendor Bill',
            res_model: 'account.move',
            view_mode: 'form',
            views: [[false, 'form']],
            context: { default_move_type: 'in_invoice' },
        });
    }

    viewJournalItems() {
        this.action.doAction('account.action_account_moves_all_a');
    }

    closeAnalyticsModal() {
        this.state.showAnalyticsModal = false;
    }

    openReceivablesAnalytics() {
        this.state.analyticsType = 'receivables';
        this.state.showAnalyticsModal = true;
    }

    openPayablesAnalytics() {
        this.state.analyticsType = 'payables';
        this.state.showAnalyticsModal = true;
    }

    viewPayments(type) {
        this.closeAnalyticsModal();
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: type === 'inbound' ? 'Customer Payments' : 'Vendor Payments',
            res_model: 'account.payment',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'posted'], ['payment_type', '=', type]],
        });
    }

    // ─────────────────────────────────────────────────────────────────
    // Formatting helpers
    // ─────────────────────────────────────────────────────────────────

    /** Short label: 10,00,000 → "10.0 L", 1,00,00,000 → "1.00 Cr" */
    _fmtShort(value) {
        if (!value || isNaN(value)) return '0';
        const v = Math.abs(value);
        if (v >= 10_000_000) return (value / 10_000_000).toFixed(2) + ' Cr';
        if (v >= 100_000) return (value / 100_000).toFixed(2) + ' L';
        if (v >= 1_000) return (value / 1_000).toFixed(1) + 'K';
        return String(Math.round(value));
    }

    /** Full Indian-format with currency symbol, e.g. "₹ 4,00,000" */
    formatCurrency(value) {
        const sym = this.state.budgetData.currency_symbol
            || this.state.data.currency_symbol || '₹';
        if (!value || isNaN(value)) return `${sym} 0`;
        const abs = Math.abs(Math.round(value));
        const str = String(abs);
        const last3 = str.length > 3 ? str.slice(-3) : str;
        const rest = str.length > 3 ? str.slice(0, -3) : '';
        const fmt = (rest ? rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' : '') + last3;
        return `${sym} ${value < 0 ? '-' : ''}${fmt}`;
    }
}

WingspannAccountingDashboard.template = "wingspann_accounting.Dashboard";
registry.category("actions").add("wingspann_accounting_dashboard", WingspannAccountingDashboard);
