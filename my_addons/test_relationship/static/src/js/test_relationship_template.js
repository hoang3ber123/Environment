/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class TestRelationshipTemplate extends Component {
    setup() {
        this.state = useState({
            newName: "",
            isCreateModal: false,

            // Dữ liệu danh sách
            items: [],
            filterValue: "",

            // Phân trang
            page: 1,
            pageSize: 10,
            total: 0,
        });

        onWillStart(async () => {
            await this.loadItems();
        });
    }

    async loadItems() {
        const params = {
            page: this.state.page,
            page_size: this.state.pageSize,
        };

        if (this.state.filterValue) {
            params.name = this.state.filterValue;
        }

        const result = await rpc("/test_relationship/list", params);
        this.state.items = result.results;
        this.state.total = result.total;
    }

    async goToPage(page) {
        this.state.page = page;
        await this.loadItems();
    }

    async applyFilters() {
        this.state.page = 1;
        await this.loadItems();
    }

    openCreateModal() {
        this.state.isCreateModal = true;
    }

    closeCreateModal() {
        this.state.isCreateModal = false;
        this.state.newName = "";
    }

    async addItem() {
        if (!this.state.newName.trim()) {
            alert("Vui lòng nhập tên!");
            return;
        }

        const values = {
            name: this.state.newName,
        };

        await rpc("/test_relationship/create", values);
        this.closeCreateModal();
        await this.loadItems(); // Load lại danh sách sau khi tạo
    }

    static template = "test_relationship.TestRelationshipTemplate";
}

registry.category("actions").add("test_relationship.test_relationship_template", TestRelationshipTemplate);
