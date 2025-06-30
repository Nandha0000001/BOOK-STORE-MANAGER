// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Quantity controls for product detail page
    const quantityInput = document.getElementById('quantity');
    const incrementBtn = document.querySelector('.increment-btn');
    const decrementBtn = document.querySelector('.decrement-btn');
    
    if (quantityInput && incrementBtn && decrementBtn) {
        // Increment quantity
        incrementBtn.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value, 10);
            const maxStock = parseInt(quantityInput.getAttribute('max'), 10);
            
            if (currentValue < maxStock) {
                quantityInput.value = currentValue + 1;
            }
        });
        
        // Decrement quantity
        decrementBtn.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value, 10);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });
        
        // Validate manual input
        quantityInput.addEventListener('change', function() {
            let currentValue = parseInt(quantityInput.value, 10);
            const maxStock = parseInt(quantityInput.getAttribute('max'), 10);
            
            if (isNaN(currentValue) || currentValue < 1) {
                quantityInput.value = 1;
            } else if (currentValue > maxStock) {
                quantityInput.value = maxStock;
            }
        });
    }
    
    // Cart quantity controls
    const cartQuantityInputs = document.querySelectorAll('.cart-quantity');
    
    cartQuantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            let currentValue = parseInt(this.value, 10);
            const maxStock = parseInt(this.getAttribute('max'), 10);
            
            if (isNaN(currentValue) || currentValue < 0) {
                this.value = 0;
            } else if (currentValue > maxStock) {
                this.value = maxStock;
            }
            
            // Submit form when quantity changes
            this.closest('form').submit();
        });
    });
    
    // Book search form
    const searchForm = document.getElementById('searchForm');
    const categorySelect = document.getElementById('category');
    
    if (searchForm && categorySelect) {
        categorySelect.addEventListener('change', function() {
            searchForm.submit();
        });
    }
    
    // Book deletion confirmation
    const deleteBookBtns = document.querySelectorAll('.delete-book-btn');
    
    deleteBookBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this book? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // User deletion confirmation
    const deleteUserBtns = document.querySelectorAll('.delete-user-btn');
    
    deleteUserBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
});
