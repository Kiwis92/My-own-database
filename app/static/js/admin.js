// Update status select color indicator
const statusSelect = document.getElementById('statusSelect');
if (statusSelect) {
    statusSelect.addEventListener('change', function() {
        this.className = 'form-select status-select status-indicator-' + this.value;
    });
}
