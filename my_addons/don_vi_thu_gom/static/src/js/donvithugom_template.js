/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class DonViThuGomModelTemplate extends Component {
    setup() {
        this.state = useState({
            items: [],
            newName: "",
            newTitle: "",
            newAddress: "",
            selectedIds: new Set(),
        });

        onWillStart(async () => {
            this.state.items = await rpc("/donvithugom/list", {});
        });
    }

    // Đây là giao diện tạo dơn vị thu gom
    async addDonViThuGom() {
        if (!this.state.newName.trim()) {
            alert("Vui lòng nhập tên!");
            return;
        }
        if (!this.state.newTitle.trim()) {
            alert("Vui lòng nhập mô tả!");
            return;
        }
        if (!this.state.newAddress.trim()) {
            alert("Vui lòng nhập địa chỉ!");
            return;
        }
        const newItem = await rpc("/donvithugom/create", { 
            name: this.state.newName, 
            title: this.state.newTitle,
            address: this.state.newAddress
        });
        // Thêm cái item vào list
        this.state.items.push(newItem);
        // Reset lại trạng thái cũ
        this.state.newName = "";
        this.state.newTitle = "";
        this.state.newAddress = "";
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
        await rpc("/donvithugom/delete_bulk", { ids }); // Chưa tạo controller này

        this.state.items = this.state.items.filter(item => !this.state.selectedIds.has(item.id));
        this.state.selectedIds.clear();
    }

    async viewDetail(id) {
        const detail = await rpc("/donvithugom/detail", { id });
        alert(`Tên: ${detail.name}\nMô tả: ${detail.title}\nĐịa chỉ: ${detail.address}\nTạo lúc: ${detail.create_date}`);
    }

    async editDonViThuGom(item) {
        const newName = prompt("Nhập tên mới:", item.name);
        const newTitle = prompt("Nhập mô tả mới:", item.title || "");
        const newAddress = prompt("Nhập địa chỉ mới:", item.address || "");
        // Không update nếu không có thay đổi
        if (
            (!newName || newName === item.name) 
            &&
            (!newTitle || newTitle === item.title)
             &&
            (!newAddress || newAddress === item.address)
        ) 
            {
            return;
        }

        const result = await rpc("/donvithugom/update", {
            id: item.id,
            ...(newName && newName !== item.name ? { name: newName } : {}),
            ...(newTitle && newTitle !== item.title ? { title: newTitle } : {}),
            ...(newAddress && newAddress !== item.address ? { address: newAddress } : {}),
        });

        if (result?.status === "success") {
            if (newName && newName !== item.name) item.name = newName;
            if (newTitle && newTitle !== item.title) item.title = newTitle;
            if (newAddress&& newAddress !== item.address) item.address = newAddress;
        } else {
            alert("Cập nhật thất bại: " + (result?.error || "Lỗi không xác định"));
        }
    }

    static template = "don_vi_thu_gom.DonViThuGomModelTemplate";
}

registry.category("actions").add("don_vi_thu_gom.donvithugom_template", DonViThuGomModelTemplate);
