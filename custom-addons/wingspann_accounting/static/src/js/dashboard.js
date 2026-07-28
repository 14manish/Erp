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
                currency_symbol: '$'
            },
            isLoading: true,
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
        this.action.doAction('account.action_account_bank_journal_form');
    }
    
    viewJournalItems() {
        this.action.doAction('account.action_account_moves_all_a');
    }
    
    formatCurrency(value) {
        return this.state.data.currency_symbol + " " + value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }
}

WingspannAccountingDashboard.template = "wingspann_accounting.Dashboard";
registry.category("actions").add("wingspann_accounting_dashboard", WingspannAccountingDashboard);
