function toggleNav() {
    const links = document.getElementById('navLinks');
    if (links) links.classList.toggle('open');
}

// Auto-submit filters on select change
document.querySelectorAll('#filterForm select').forEach(sel => {
    sel.addEventListener('change', () => sel.closest('form').submit());
});

document.querySelectorAll('#filterForm input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', () => radio.closest('form').submit());
});
