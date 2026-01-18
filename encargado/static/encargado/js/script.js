// Toggle del Sidebar
const menuIcon = document.getElementById('menu');
const sidebar = document.getElementById('sidebar');
const main = document.getElementById('main');

if (menuIcon) {
    menuIcon.addEventListener('click', function () {
        sidebar.classList.toggle('menu-open');
        main.classList.toggle('main-shifted');
    });
}



