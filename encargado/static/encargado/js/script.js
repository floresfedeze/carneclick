(function () {
    /* ========= SIDEBAR TOGGLE ========= */
    const menuTrigger = document.getElementById('menu');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sb-overlay');

    const isDesktop = () => window.innerWidth >= 992;

    function openSidebar() {
        sidebar.classList.add('menu-open');
        document.body.classList.add('sb-open');
        if (!isDesktop() && overlay) overlay.classList.add('active');
        if (isDesktop()) localStorage.setItem('sidebarOpen', 'true');
    }

    function closeSidebar() {
        sidebar.classList.remove('menu-open');
        document.body.classList.remove('sb-open');
        if (overlay) overlay.classList.remove('active');
        if (isDesktop()) localStorage.setItem('sidebarOpen', 'false');
    }

    if (menuTrigger) {
        menuTrigger.addEventListener('click', () => {
            sidebar.classList.contains('menu-open') ? closeSidebar() : openSidebar();
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    /* --- Restore desktop state (default: open) --- */
    if (isDesktop()) {
        const saved = localStorage.getItem('sidebarOpen');
        if (saved !== 'false') openSidebar();
    }

    /* --- Active link detection --- */
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar a[href]').forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href === '#') return;
        if (currentPath === href || (href.length > 1 && currentPath.startsWith(href))) {
            link.classList.add('active');
            const parentCollapse = link.closest('ul.collapse');
            if (parentCollapse) {
                const bsCollapse = bootstrap.Collapse.getOrCreateInstance(parentCollapse, { toggle: false });
                bsCollapse.show();
            }
        }
    });

    /* --- Close sidebar on mobile when a leaf link is clicked --- */
    document.querySelectorAll('.sidebar a[href]:not([data-bs-toggle])').forEach(link => {
        link.addEventListener('click', () => { if (!isDesktop()) closeSidebar(); });
    });

    /* --- Resize handler --- */
    window.addEventListener('resize', () => {
        if (isDesktop()) {
            if (overlay) overlay.classList.remove('active');
            document.body.classList.remove('sb-open');
            const saved = localStorage.getItem('sidebarOpen');
            saved === 'false' ? sidebar.classList.remove('menu-open') : sidebar.classList.add('menu-open');
        } else {
            closeSidebar();
        }
    });

    /* ========= SEARCH PANEL ========= */
    const btnSearch = document.getElementById('btn-search');
    const searchPanel = document.getElementById('search-panel');
    const searchInput = document.getElementById('search-input');
    const searchClose = document.getElementById('search-close');
    const searchList = document.getElementById('search-suggestions');
    let searchOpen = false;

    function openSearch() {
        searchPanel.classList.add('open');
        searchPanel.setAttribute('aria-hidden', 'false');
        searchInput.value = '';
        renderSuggestions('');
        setTimeout(() => searchInput.focus(), 80);
        searchOpen = true;
        if (btnSearch) btnSearch.classList.add('active');
    }
    function closeSearch() {
        searchPanel.classList.remove('open');
        searchPanel.setAttribute('aria-hidden', 'true');
        searchOpen = false;
        if (btnSearch) btnSearch.classList.remove('active');
    }

    function renderSuggestions(query) {
        const q = query.toLowerCase().trim();
        const items = typeof SEARCH_ITEMS !== 'undefined' ? SEARCH_ITEMS : [];
        const filtered = q
            ? items.filter(it => it.label.toLowerCase().includes(q))
            : items.slice(0, 9);
        if (filtered.length === 0) {
            searchList.innerHTML = '<p class="search-empty">No se encontraron resultados</p>';
            return;
        }
        searchList.innerHTML = filtered.map(it =>
            `<li><a href="${it.url}"><i class="bi ${it.icon}"></i>${it.label}</a></li>`
        ).join('');
    }

    if (btnSearch) btnSearch.addEventListener('click', () => searchOpen ? closeSearch() : openSearch());
    if (searchClose) searchClose.addEventListener('click', closeSearch);

    if (searchInput) {
        searchInput.addEventListener('input', () => renderSuggestions(searchInput.value));
        searchInput.addEventListener('keydown', e => {
            if (e.key === 'Escape') { closeSearch(); return; }
            const links = [...searchList.querySelectorAll('a')];
            if (!links.length) return;
            const focused = searchList.querySelector('a.focused');
            let idx = links.indexOf(focused);
            if (e.key === 'ArrowDown') {
                if (focused) focused.classList.remove('focused');
                idx = (idx + 1) % links.length;
                links[idx].classList.add('focused');
                links[idx].scrollIntoView({ block: 'nearest' });
                e.preventDefault();
            } else if (e.key === 'ArrowUp') {
                if (focused) focused.classList.remove('focused');
                idx = (idx - 1 + links.length) % links.length;
                links[idx].classList.add('focused');
                links[idx].scrollIntoView({ block: 'nearest' });
                e.preventDefault();
            } else if (e.key === 'Enter' && focused) {
                focused.click();
            }
        });
    }

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && searchOpen) closeSearch();
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchOpen ? closeSearch() : openSearch();
        }
    });

    /* ========= NOTIFICATIONS PANEL ========= */
    const btnNotif = document.getElementById('btn-notif');
    const notifPanel = document.getElementById('notif-panel');
    const notifClose = document.getElementById('notif-close');
    const notifBackdrop = document.getElementById('notif-backdrop');
    const notifBody = document.getElementById('notif-body');
    const notifBadge = document.getElementById('notif-badge');
    let notifOpen = false;
    let notifLoaded = false;

    function openNotif() {
        notifPanel.classList.add('open');
        notifPanel.setAttribute('aria-hidden', 'false');
        notifBackdrop.classList.add('active');
        notifOpen = true;
        if (btnNotif) btnNotif.classList.add('active');
        if (!notifLoaded) loadNotifications();
    }
    function closeNotif() {
        notifPanel.classList.remove('open');
        notifPanel.setAttribute('aria-hidden', 'true');
        notifBackdrop.classList.remove('active');
        notifOpen = false;
        if (btnNotif) btnNotif.classList.remove('active');
    }

    const COLOR_MAP = { warning: 'warning', danger: 'danger', success: 'success', info: 'info' };

    function updateBadge(total) {
        if (!notifBadge) return;
        if (total > 0) {
            notifBadge.textContent = total > 99 ? '99+' : total;
            notifBadge.classList.remove('d-none');
        } else {
            notifBadge.classList.add('d-none');
        }
    }

    function renderNotifications(data) {
        notifLoaded = true;
        updateBadge(data.total || 0);
        if (!data.items || data.items.length === 0) {
            notifBody.innerHTML = '<p class="notif-loading">Sin notificaciones pendientes</p>';
            return;
        }
        notifBody.innerHTML = data.items.map((item, i) => `
        <a href="${item.url}" class="notif-item">
            <div class="notif-icon ${COLOR_MAP[item.color] || 'info'}">
                <i class="bi ${item.icon}"></i>
            </div>
            <div class="notif-text">
                <div class="notif-text-label">${item.label}</div>
                <div class="notif-text-count${item.count === 0 ? ' zero' : ''}">
                    ${item.count === 0 ? 'Sin pendientes' : item.count}
                </div>
            </div>
            <i class="bi bi-chevron-right notif-arrow"></i>
        </a>
        ${i < data.items.length - 1 ? '<div class="notif-divider"></div>' : ''}
    `).join('');
    }

    function loadNotifications() {
        if (typeof NOTIF_URL === 'undefined') return;
        fetch(NOTIF_URL)
            .then(r => r.json())
            .then(renderNotifications)
            .catch(() => {
                if (notifBody) notifBody.innerHTML = '<p class="notif-loading">Error al cargar notificaciones</p>';
            });
    }

    if (btnNotif) btnNotif.addEventListener('click', () => notifOpen ? closeNotif() : openNotif());
    if (notifClose) notifClose.addEventListener('click', closeNotif);
    if (notifBackdrop) notifBackdrop.addEventListener('click', closeNotif);

    /* Pre-cargar badge en segundo plano al abrir la página */
    if (typeof NOTIF_URL !== 'undefined') {
        fetch(NOTIF_URL)
            .then(r => r.json())
            .then(d => updateBadge(d.total || 0))
            .catch(() => { });
    }

})();


