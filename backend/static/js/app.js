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

// ---- Tooltips: auto-enable Bootstrap tooltips on any titled element ----
(function () {
  document.querySelectorAll("[title]:not([data-bs-toggle])").forEach((el) => {
    el.setAttribute("data-bs-toggle", "tooltip");
    el.setAttribute("data-bs-placement", el.dataset.bsPlacement || "top");
  });
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
    try { bootstrap.Tooltip.getOrCreateInstance(el); } catch (_) {}
  });
})();

// ---- Loading spinner + disable submit button while a form is processing ----
(function () {
  document.querySelectorAll("form").forEach((form) => {
    if (form.dataset.noLoading !== undefined) return;
    if ((form.method || "get").toLowerCase() !== "post") return;

    form.addEventListener("submit", (e) => {
      // Skip if another handler (e.g. an inline confirm()) already cancelled it.
      if (e.defaultPrevented) return;

      form.querySelectorAll('button[type="submit"], input[type="submit"]').forEach((btn) => {
        if (btn.disabled) return;
        btn.dataset.originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.setAttribute("aria-busy", "true");
        const label = btn.dataset.loadingText || "Please wait…";
        btn.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' +
          label;
      });
    });
  });
})();

// ---- Export buttons: brief spinner feedback (download happens in background) ----
(function () {
  document.querySelectorAll('a[href*="format=pdf"], a[href*="format=xlsx"], a[href*="format=csv"]').forEach((link) => {
    link.addEventListener("click", () => {
      if (link.dataset.exporting) return;
      link.dataset.exporting = "1";
      const icon = link.querySelector("i");
      const iconClass = icon ? icon.className : null;
      if (icon) icon.className = "spinner-border spinner-border-sm";
      setTimeout(() => {
        if (icon && iconClass) icon.className = iconClass;
        delete link.dataset.exporting;
      }, 1800);
    });
  });
})();

// ---- Search term highlighting ----
(function () {
  const params = new URLSearchParams(window.location.search);
  const term = (params.get("q") || "").trim();
  if (!term || term.length < 2) return;

  const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp("(" + escaped + ")", "ig");

  document.querySelectorAll(".thms-table tbody td").forEach((cell) => {
    if (cell.querySelector("a, form, button, input, select")) return; // don't touch interactive cells
    const walker = document.createTreeWalker(cell, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    let node;
    while ((node = walker.nextNode())) {
      if (pattern.test(node.nodeValue)) textNodes.push(node);
    }
    textNodes.forEach((textNode) => {
      const span = document.createElement("span");
      span.innerHTML = textNode.nodeValue.replace(pattern, "<mark>$1</mark>");
      textNode.replaceWith(span);
    });
  });
})();

// ---- Service Worker (PWA) ----
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/service-worker.js")
      .catch(() => {});
  });
}
