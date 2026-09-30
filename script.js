/**
 * VK LEDGUR CONVERTER - JavaScript
 * Client-side interactivity and form handling
 */

// ==========================================
// NAVBAR TOGGLE FOR MOBILE
// ==========================================

function toggleMenu() {
    const navMenu = document.getElementById('navMenu');
    if (navMenu) {
        navMenu.classList.toggle('active');
    }
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const navbar = document.querySelector('.navbar');
    const navMenu = document.getElementById('navMenu');
    
    if (navbar && !navbar.contains(event.target) && navMenu) {
        navMenu.classList.remove('active');
    }
});

// Close menu on link click
document.querySelectorAll('.navbar-menu a').forEach(link => {
    link.addEventListener('click', function() {
        const navMenu = document.getElementById('navMenu');
        if (navMenu) {
            navMenu.classList.remove('active');
        }
    });
});

// ==========================================
// FORM VALIDATION
// ==========================================

function validateSignupForm() {
    const fullName = document.getElementById('fullName')?.value.trim();
    const username = document.getElementById('username')?.value.trim();
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirmPassword')?.value;
    
    if (!fullName || fullName.length < 3) {
        alert('Full name must be at least 3 characters');
        return false;
    }
    
    if (!username || username.length < 3 || username.length > 50) {
        alert('Username must be 3-50 characters');
        return false;
    }
    
    if (!password || password.length < 8) {
        alert('Password must be at least 8 characters');
        return false;
    }
    
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return false;
    }
    
    return true;
}

function validateLoginForm() {
    const username = document.getElementById('username')?.value.trim();
    const password = document.getElementById('password')?.value;
    
    if (!username) {
        alert('Username is required');
        return false;
    }
    
    if (!password) {
        alert('Password is required');
        return false;
    }
    
    return true;
}

// ==========================================
// ENTRY FORM VALIDATION
// ==========================================

function validateEntryForm() {
    const entryDate = document.getElementById('entryDate')?.value;
    const details = document.getElementById('details')?.value.trim();
    const debit = parseFloat(document.getElementById('debit')?.value) || 0;
    const credit = parseFloat(document.getElementById('credit')?.value) || 0;
    
    if (!entryDate) {
        alert('Please select a date');
        return false;
    }
    
    if (!details) {
        alert('Please enter transaction details');
        return false;
    }
    
    if (debit < 0 || credit < 0) {
        alert('Debit and credit must be positive numbers');
        return false;
    }
    
    if (debit === 0 && credit === 0) {
        alert('Either debit or credit must be greater than 0');
        return false;
    }
    
    return true;
}

// ==========================================
// FORMATTING FUNCTIONS
// ==========================================

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

// ==========================================
// EDITOR FUNCTIONS (defined in template but available globally)
// ==========================================

async function addEntry(ledgerId) {
    if (!validateEntryForm()) return;
    
    const entryDate = document.getElementById('entryDate').value;
    const details = document.getElementById('details').value.trim();
    const reference = document.getElementById('reference').value.trim();
    const debit = parseFloat(document.getElementById('debit').value) || 0;
    const credit = parseFloat(document.getElementById('credit').value) || 0;
    
    try {
        const response = await fetch(`/api/ledger/${ledgerId}/entries`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                entry_date: entryDate,
                details: details,
                reference: reference,
                debit: debit,
                credit: credit
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showSuccessMessage('Entry added successfully!');
            setTimeout(() => location.reload(), 1500);
        } else {
            showErrorMessage('Error adding entry: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage('Error adding entry');
    }
}

async function editEntry(cell, entryId, type) {
    cell.onblur = async function() {
        const newValue = parseFloat(cell.innerText) || 0;
        
        if (newValue < 0) {
            alert('Amount must be positive');
            location.reload();
            return;
        }
        
        const row = document.getElementById(`entry-${entryId}`);
        const debit = type === 'debit' ? newValue : parseFloat(row.cells[3].innerText);
        const credit = type === 'credit' ? newValue : parseFloat(row.cells[4].innerText);
        
        try {
            const response = await fetch(`/api/entry/${entryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    debit: debit,
                    credit: credit
                })
            });
            
            const data = await response.json();
            if (data.success) {
                showSuccessMessage('Entry updated!');
                setTimeout(() => location.reload(), 1500);
            }
        } catch (error) {
            console.error('Error:', error);
            showErrorMessage('Error updating entry');
        }
    };
}

async function deleteEntry(entryId) {
    if (!confirm('Are you sure you want to delete this entry?')) return;
    
    try {
        const response = await fetch(`/api/entry/${entryId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.success) {
            showSuccessMessage('Entry deleted!');
            setTimeout(() => location.reload(), 1500);
        }
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage('Error deleting entry');
    }
}

async function saveLedger(ledgerId) {
    try {
        const response = await fetch(`/ledger/${ledgerId}/save`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.success) {
            showSuccessMessage('✓ Ledger saved successfully!');
            setTimeout(() => location.reload(), 1500);
        }
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage('Error saving ledger');
    }
}

async function deleteLedger(ledgerId) {
    if (!confirm('Are you sure you want to delete this ledger? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/ledger/${ledgerId}/delete`, {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.success) {
            showSuccessMessage('Ledger deleted!');
            setTimeout(() => window.location.href = '/dashboard', 1500);
        } else {
            showErrorMessage('Error deleting ledger');
        }
    } catch (error) {
        console.error('Error:', error);
        showErrorMessage('Error deleting ledger');
    }
}

// ==========================================
// MESSAGE DISPLAY FUNCTIONS
// ==========================================

function showSuccessMessage(message) {
    showMessage(message, 'success');
}

function showErrorMessage(message) {
    showMessage(message, 'error');
}

function showMessage(message, type) {
    // Remove existing messages
    const existing = document.querySelector('.temporary-message');
    if (existing) {
        existing.remove();
    }
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `temporary-message alert alert-${type}`;
    messageEl.textContent = message;
    messageEl.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        z-index: 1000;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(messageEl);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageEl.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => messageEl.remove(), 300);
    }, 5000);
}

// ==========================================
// ANIMATIONS
// ==========================================

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ==========================================
// INITIALIZE ON PAGE LOAD
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Set today's date if date input exists
    const dateInput = document.getElementById('entryDate');
    if (dateInput) {
        dateInput.valueAsDate = new Date();
    }
    
    // Add any initialization code here
    console.log('VK LEDGUR CONVERTER loaded successfully');
});

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

function confirmAction(message) {
    return confirm(message);
}

function redirectTo(url) {
    window.location.href = url;
}

// Export functions if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toggleMenu,
        validateSignupForm,
        validateLoginForm,
        formatCurrency,
        formatDate,
        showSuccessMessage,
        showErrorMessage,
        addEntry,
        editEntry,
        deleteEntry,
        saveLedger,
        deleteLedger
    };
}
