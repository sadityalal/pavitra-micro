function updateStock(productId, currentStock) {
    document.getElementById('stockQuantity').value = currentStock;
    document.getElementById('stockForm').action = `/admin/products/${productId}/stock`;
    const stockModal = new bootstrap.Modal(document.getElementById('stockModal'));
    stockModal.show();
}

function confirmDelete() {
    return confirm('Are you sure you want to delete this product? This action cannot be undone.');
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Products management initialized');
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
            this.style.transition = 'transform 0.2s ease';
        });
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
});