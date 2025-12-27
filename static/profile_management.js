// Show the delete confirmation modal
function showDeleteModal() {
    document.getElementById('delete-modal').style.display = 'flex';
}

// Hide the delete confirmation modal
function hideDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
}

// Delete account function
function deleteAccount() {
    // Make API call to delete account
    fetch('/delete_account', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Account deletion failed');
    })
    .then(data => {
        // Show success message
        const successMessage = document.getElementById('success-message');
        successMessage.style.display = 'block';
        
        // Disable the delete button
        document.querySelector('.btn-danger').disabled = true;
        document.querySelector('.btn-danger').textContent = 'Data Deleted';
        
        // Redirect to login page after a delay
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while deleting your account.');
    });
    
    hideDeleteModal();
}

function goToDashboard() {
    window.location.href = "{{ url_for('profile') }}";
}

// Close modal if user clicks outside of it
window.onclick = function(event) {
    const modal = document.getElementById('delete-modal');
    if (event.target === modal) {
        hideDeleteModal();
    }
}