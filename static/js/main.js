// ملف JavaScript الرئيسي

document.addEventListener('DOMContentLoaded', function() {
    // إخفاء رسائل التنبيه بعد 5 ثوانٍ
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // تفعيل tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // تفعيل popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // تأكيد الحذف
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('هل أنت متأكد من رغبتك في الحذف؟')) {
                e.preventDefault();
            }
        });
    });
    
    // تحديث حقول التاريخ والوقت في نماذج المواعيد
    const dateTimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    dateTimeInputs.forEach(function(input) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        
        if (!input.value) {
            input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
    });
    
    // تحديث حقول التاريخ في نماذج الفواتير
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        
        if (!input.value && input.name === 'due_date') {
            // تعيين تاريخ الاستحقاق بعد 30 يومًا
            const dueDate = new Date();
            dueDate.setDate(dueDate.getDate() + 30);
            const dueYear = dueDate.getFullYear();
            const dueMonth = String(dueDate.getMonth() + 1).padStart(2, '0');
            const dueDay = String(dueDate.getDate()).padStart(2, '0');
            
            input.value = `${dueYear}-${dueMonth}-${dueDay}`;
        } else if (!input.value) {
            input.value = `${year}-${month}-${day}`;
        }
    });
    
    // تحديث المبلغ المتبقي في نموذج إضافة دفعة
    const paymentAmountInput = document.getElementById('amount');
    const remainingAmountElement = document.getElementById('remaining_amount');
    
    if (paymentAmountInput && remainingAmountElement) {
        const remainingAmount = parseFloat(remainingAmountElement.dataset.value);
        
        paymentAmountInput.addEventListener('input', function() {
            const enteredAmount = parseFloat(this.value) || 0;
            
            if (enteredAmount > remainingAmount) {
                this.value = remainingAmount;
                alert('المبلغ المدخل يتجاوز المبلغ المتبقي!');
            }
        });
    }
    
    // تفعيل البحث في الجداول
    const tableSearchInput = document.getElementById('table-search');
    if (tableSearchInput) {
        tableSearchInput.addEventListener('keyup', function() {
            const searchText = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('.searchable-table tbody tr');
            
            tableRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchText)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // تفعيل طباعة الصفحة
    const printButtons = document.querySelectorAll('.btn-print');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });
});
