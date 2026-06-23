let currentPackage = {};

function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    if (show) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        // Add a slight delay for opacity transition if needed
        setTimeout(() => {
            modal.querySelector('.bg-gray-900\\/50')?.classList.remove('opacity-0');
            modal.querySelector('.transform')?.classList.remove('scale-95', 'opacity-0');
        }, 10);
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function closeAllModals() {
    toggleModal('mpesaModal', false);
    toggleModal('successModal', false);
}

// Close modals when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.matches('.modal-overlay')) {
        closeAllModals();
    }
});

function purchaseTokens(packageType, tokens, amount) {
    currentPackage = {
        type: packageType,
        tokens: tokens,
        amount: amount
    };

    const packageNames = {
        'basic': 'Basic Package',
        'standard': 'Standard Package',
        'premium': 'Premium Package',
        'mega': 'Mega Package'
    };

    document.getElementById('packageTitle').textContent = packageNames[packageType];
    document.getElementById('packageDetails').textContent = `${tokens.toLocaleString()} Tokens for KES ${amount.toLocaleString()}`;
    document.getElementById('amount').value = amount;
    document.getElementById('tokens').value = tokens;
    document.getElementById('package').value = packageType;

    toggleModal('mpesaModal', true);
}

document.getElementById('mpesaForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const form = this;
    const formData = new FormData(form);
    const phone = formData.get('phone');

    // Validate phone number
    if (!/^[0-9]{9}$/.test(phone)) {
        alert('Please enter a valid 9-digit phone number (e.g., 712345678)');
        return;
    }

    // Add 254 prefix
    formData.set('phone', '254' + phone);

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Processing...';
    submitBtn.classList.add('opacity-75', 'cursor-not-allowed');

    // Get STK URL from form attribute
    const stkUrl = form.getAttribute('data-stk-url');

    fetch(stkUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        toggleModal('mpesaModal', false);

        if (data.success) {
            toggleModal('successModal', true);
        } else {
            alert('Payment initiation failed: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        submitBtn.classList.remove('opacity-75', 'cursor-not-allowed');
    });
});
