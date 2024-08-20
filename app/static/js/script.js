console.log("Script loaded successfully!");

document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('form button[type="submit"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            if (!confirm("Are you sure you want to delete this book?")) {
                event.preventDefault();
            }
        });
    });
});
