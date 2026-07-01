/* =============================================
   THMS — Transport Hire Management System
   Main JavaScript
   ============================================= */

// ---- Date display ----
(function () {
  const el = document.getElementById("currentDate");
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleDateString("en-NG", {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }
})();

// ---- Sidebar toggle ----
(function () {
  const sidebar = document.getElementById("sidebar");
  const mainWrapper = document.getElementById("mainWrapper");
  const toggleBtn = document.getElementById("sidebarToggle");
  if (!sidebar || !toggleBtn) return;

  const isMobile = () => window.innerWidth <= 768;

  function applyCollapsed(collapsed) {
    if (isMobile()) {
      sidebar.classList.toggle("mobile-open", !collapsed);
    } else {
      sidebar.classList.toggle("collapsed", collapsed);
      mainWrapper && mainWrapper.classList.toggle("expanded", collapsed);
    }
    try { localStorage.setItem("sidebarCollapsed", collapsed ? "1" : "0"); } catch (_) {}
  }

  toggleBtn.addEventListener("click", () => {
    if (isMobile()) {
      const isOpen = sidebar.classList.contains("mobile-open");
      applyCollapsed(isOpen);
    } else {
      const isCollapsed = sidebar.classList.contains("collapsed");
      applyCollapsed(!isCollapsed);
    }
  });

  // Mobile: close sidebar on overlay click
  document.addEventListener("click", (e) => {
    if (isMobile() && sidebar.classList.contains("mobile-open")) {
      if (!sidebar.contains(e.target) && e.target !== toggleBtn) {
        applyCollapsed(true);
      }
    }
  });

  // Restore state on desktop
  if (!isMobile()) {
    try {
      const saved = localStorage.getItem("sidebarCollapsed");
      if (saved === "1") applyCollapsed(true);
    } catch (_) {}
  }
})();

// ---- Dark mode toggle ----
(function () {
  const toggleBtn = document.getElementById("themeToggle");
  const icon = document.getElementById("themeIcon");
  const html = document.documentElement;

  function setTheme(dark) {
    html.setAttribute("data-bs-theme", dark ? "dark" : "light");
    if (icon) {
      icon.className = dark ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
    }
    try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch (_) {}
  }

  // Restore saved theme
  try {
    const saved = localStorage.getItem("theme");
    if (saved === "dark") setTheme(true);
  } catch (_) {}

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isDark = html.getAttribute("data-bs-theme") === "dark";
      setTheme(!isDark);
    });
  }
})();

// ---- Auto-dismiss alerts after 5s ----
(function () {
  document.querySelectorAll(".alert.fade.show").forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert && bsAlert.close();
    }, 5000);
  });
})();

// ---- Format currency inputs ----
document.querySelectorAll("input[data-currency]").forEach((input) => {
  input.addEventListener("blur", () => {
    const val = parseFloat(input.value.replace(/,/g, ""));
    if (!isNaN(val)) input.value = val.toLocaleString("en-NG");
  });
});

// ---- Confirm dangerous actions ----
document.querySelectorAll("[data-confirm]").forEach((el) => {
  el.addEventListener("click", (e) => {
    if (!confirm(el.dataset.confirm || "Are you sure?")) {
      e.preventDefault();
    }
  });
});

// ---- Service Worker (PWA) ----
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/service-worker.js")
      .catch(() => {});
  });
}
