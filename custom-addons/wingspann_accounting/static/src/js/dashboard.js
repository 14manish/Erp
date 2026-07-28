/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class WingspannAccountingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: {
                cash_balance: 0.0,
                receivables: 0.0,
                payables: 0.0,
                recent_moves: [],
                currency_symbol: '$',
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

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        const result = await this.orm.call(
            "wingspann.accounting.dashboard",
            "get_dashboard_data",
            []
        );
        this.state.data = result;
        this.state.isLoading = false;
    }

    createInvoice() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Customer Invoice',
            res_model: 'account.move',
            view_mode: 'form',
            views: [[false, 'form']],
            context: {'default_move_type': 'out_invoice'}
        });
    }

    createBill() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Vendor Bill',
            res_model: 'account.move',
            view_mode: 'form',
            views: [[false, 'form']],
            context: {'default_move_type': 'in_invoice'}
        });
    }
    
    viewBank() {
        this.action.doAction('account.open_account_journal_dashboard_kanban');
    }
    
    viewJournalItems() {
        this.action.doAction('account.action_account_moves_all_a');
    }

    openReceivablesAnalytics() {
        this.state.analyticsType = 'receivables';
        this.state.showAnalyticsModal = true;
    }

    openPayablesAnalytics() {
        this.state.analyticsType = 'payables';
        this.state.showAnalyticsModal = true;
    }

    closeAnalyticsModal() {
        this.state.showAnalyticsModal = false;
    }

    viewPayments(type) {
        this.closeAnalyticsModal();
        let domain = [['state', '=', 'posted']];
        if (type === 'inbound') {
            domain.push(['payment_type', '=', 'inbound']);
        } else {
            domain.push(['payment_type', '=', 'outbound']);
        }
        
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: type === 'inbound' ? 'Customer Payments' : 'Vendor Payments',
            res_model: 'account.payment',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
        });
    }
    
    formatCurrency(value) {
        return this.state.data.currency_symbol + " " + value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }
}

WingspannAccountingDashboard.template = "wingspann_accounting.Dashboard";
registry.category("actions").add("wingspann_accounting_dashboard", WingspannAccountingDashboard);
