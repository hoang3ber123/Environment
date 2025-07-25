/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class TestModelTemplate extends Component {
    setup() {
        this.state = useState({
            items: [],
            newName: "",
            newTitle: "",
            selectedIds: new Set(),
        });

        onWillStart(async () => {
            this.state.items = await rpc("/test/list", {});
        });
    }

    async addTest() {
        if (!this.state.newName.trim()) {
            alert("Vui lòng nhập tên!");
            return;
        }
        if (!this.state.newTitle.trim()) {
            alert("Vui lòng nhập mô tả!");
            return;
        }
        const newItem = await rpc("/test/create", { 
            name: this.state.newName, 
            title: this.state.newTitle
        });
        // Thêm cái item vào list
        this.state.items.push(newItem);
        // Reset lại trạng thái cũ
        this.state.newName = "";
        this.state.newTitle = "";
    }
    
    toggleSelection(id) {
        if (this.state.selectedIds.has(id)) {
            this.state.selectedIds.delete(id);
        } else {
            this.state.selectedIds.add(id);
        }
    }

    async deleteSelected() {
        if (this.state.selectedIds.size === 0) return;

        const ids = Array.from(this.state.selectedIds);
        await rpc("/test/delete_bulk", { ids }); // Chưa tạo controller này

        this.state.items = this.state.items.filter(item => !this.state.selectedIds.has(item.id));
        this.state.selectedIds.clear();
    }

    async viewDetail(id) {
        const detail = await rpc("/test/detail", { id });
        alert(`Tên: ${detail.name}\nMô tả: ${detail.title}\nTạo lúc: ${detail.create_date}`);
    }

    async editTest(item) {
        const newName = prompt("Nhập tên mới:", item.name);
        const newTitle = prompt("Nhập mô tả mới:", item.title || "");
        // Không update nếu không có thay đổi
        if (
            (!newName || newName === item.name) 
            &&
            (!newTitle || newTitle === item.title)) 
            {
            return;
        }

        const result = await rpc("/test/update", {
            id: item.id,
            ...(newName && newName !== item.name ? { name: newName } : {}),
            ...(newTitle && newTitle !== item.title ? { title: newTitle } : {}),
        });

        if (result?.status === "success") {
            if (newName && newName !== item.name) item.name = newName;
            if (newTitle && newTitle !== item.title) item.title = newTitle;
        } else {
            alert("Cập nhật thất bại: " + (result?.error || "Lỗi không xác định"));
        }
    }

    static template = "test.TestModelTemplate";
}

registry.category("actions").add("test.test_list", TestModelTemplate);
