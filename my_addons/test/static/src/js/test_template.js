/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class TestModelTemplate extends Component {
    setup() {
        this.state = useState({
<<<<<<< HEAD
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
=======
            /* mấy cái trường này không cần hiểu đâu nhức đầu lắm 
            cứ biết là model có trường nào thì đặt vào thôi
            còn mấy cái items hay selectedIDs thì giữ nguyên nhé
            chỉ cần để ý mấy cái trường new và edit thôi
            */

            // Trường dùng khi thêm mới
            newName: "",
            newTitle: "",
            newImage: "",
            isCreateModal: false, // dùng để bật tắt form tạo

            // Dữ liệu danh sách
            items: [],
            selectedIds: new Set(),

            // Trường cho xem chi tiết
            detailItem: {},
            showModal: false, // dùng để bật tắt form chi tiết
            
            // Trường dùng khi sửa
            editName: "",
            editTitle: "",
            editImage: "",
            editId: null,
            isEditModal: false, // Dùng để bật tắt form chỉnh sửa
            
            // Lọc
            filterField: "name",
            filterValue: "",

            // Phân trang
            page: 1,
            pageSize: 8,
            total: 0,
        });

        // Khi component bắt đầu
        onWillStart(async () => {
            await this.loadItems();
        });
    }

     // 👉 Tải danh sách từ server với filter và phân trang
    async loadItems() {
        const params = {
            page: this.state.page,
            page_size: this.state.pageSize,
        };

        // Thêm điều kiện lọc nếu có
        if (this.state.filterValue) {
            params[this.state.filterField] = this.state.filterValue;
        }

        const result = await rpc("/test/list", params);
        this.state.items = result.results;
        this.state.total = result.total;
        this.state.selectedIds.clear(); // Reset selection
    }


    setFilterField(field) {
        this.state.filterField = field;
    }

    async applyFilters() {
        this.state.page = 1; // Reset về trang 1 khi filter
        await this.loadItems();
    }

    // 👉 Chuyển trang
    async goToPage(page) {
        this.state.page = page;
        await this.loadItems();
    }
        
    // Mỗi lần mà có file thì dùng hàm này nhé 
    // Không cần quan tâm hàm này làm gì chỉ cần biết là 
    // nó xử lý thêm file người dùng chọn bên giao diện
    // vào this.state.newImage là được
    handleImageChange(ev, isEdit = false) {
        const file = ev.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(",")[1];
            if (isEdit) {
                this.state.editImage = base64;
            } else {
                this.state.newImage = base64;
            }
        };
        reader.readAsDataURL(file);
    }
    openCreateModal() {
        this.state.isCreateModal = true;
    }

    closeCreateModal() {
        this.state.isCreateModal = false;
        this.state.newName = "";
        this.state.newTitle = "";
        this.state.newImage = "";
    }

    // Hàm này cần sửa nếu mà thêm trường mới trong module
    // Hàm này dùng để gọi mấy cái hàm bên controller mình viết á
    /* Nếu để ý thì có thấy "/test/create" đây chính là
        Cách mà file này gọi hàm bên controller 
        Có thể về file controller tìm hàm test_create bên trên có
        @http.route('/test/create' trùng với cái gọi bên dưới
    */
    async addTest() {
        // Kiểm tra xem nếu mà user không nhập tên thì thông báo
>>>>>>> a7a2e8c (feature: save state)
        if (!this.state.newName.trim()) {
            alert("Vui lòng nhập tên!");
            return;
        }
<<<<<<< HEAD
=======
        // Kiểm tra xem nếu mà user không title thì thông báo lỗi
>>>>>>> a7a2e8c (feature: save state)
        if (!this.state.newTitle.trim()) {
            alert("Vui lòng nhập mô tả!");
            return;
        }
<<<<<<< HEAD
        const newItem = await rpc("/test/create", { 
            name: this.state.newName, 
            title: this.state.newTitle
        });
        // Thêm cái item vào list
        this.state.items.push(newItem);
        // Reset lại trạng thái cũ
        this.state.newName = "";
        this.state.newTitle = "";
=======

        // Cái này sẽ chứa cái dữ liệu mà user nhập vào
        const values = {
            name: this.state.newName,
            title: this.state.newTitle,
        };
        
        // Nếu như mà đối tượng đó có thêm image thì mình sẽ
        // bỏ cái image đó vào values đúng không ?
        if (this.state.newImage) {
            // Đây là cú pháp bỏ một trường nào đó vào
            // values.{tên trường} = giá trị bỏ vào
            values.image = this.state.newImage;
        }
        
        // Giờ thì mình bỏ values vào hàm để tạo thôi
        // Bạn có thấy nó giống với xử lý bên controller chứ
        const newItem = await rpc("/test/create", values);
        // Reset lại trạng thái cũ
        // Cái này nếu có trường mới thì thêm vào thôi đơn giản mà đúng không ?
        // Reset và đóng modal
        this.closeCreateModal();
        // ✅ Gọi lại API để load lại danh sách
        await this.loadItems();
>>>>>>> a7a2e8c (feature: save state)
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

<<<<<<< HEAD
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
=======
        this.state.selectedIds.clear();
        // ✅ Gọi lại load
        await this.loadItems();
    }

    async viewDetail(id) {
        try {
                const detail = await rpc("/test/detail", { id });
                this.state.detailItem = detail;
                this.state.showModal = true;
            } catch (e) {
                console.error("Lỗi khi lấy chi tiết:", e);
            }
    }

    openEditModal(id) {
        const item = this.state.items.find((item) => item.id === id);
        if (!item) {
            alert("Không tìm thấy mục để sửa");
            return;
        }

        this.state.editName = item.name;
        this.state.editTitle = item.title;
        this.state.editImage = item.image || "";
        this.state.editId = item.id;
        this.state.isEditModal = true;
    }

    async updateEditItem() {
        if (!this.state.editId) {
            alert("Không có ID để cập nhật");
            return;
        }

        if (!this.state.editName.trim()) {
            alert("Vui lòng nhập tên!");
            return;
        }

        if (!this.state.editTitle.trim()) {
            alert("Vui lòng nhập mô tả!");
            return;
        }

        const values = {
            id: this.state.editId,
            name: this.state.editName,
            title: this.state.editTitle,
        };

        if (this.state.editImage) {
            values.image = this.state.editImage;
        }

        const updated = await rpc("/test/update", values);

        // Cập nhật lại danh sách items
        const index = this.state.items.findIndex((item) => item.id === updated.id);
        if (index !== -1) {
            this.state.items[index] = updated;
        }

        // Đóng modal và reset
        this.state.isEditModal = false;
        this.state.editId = null;
        this.state.editName = "";
        this.state.editTitle = "";
        this.state.editImage = "";
        this.state.editFile = null;
>>>>>>> a7a2e8c (feature: save state)
    }

    static template = "test.TestModelTemplate";
}

registry.category("actions").add("test.test_list", TestModelTemplate);
