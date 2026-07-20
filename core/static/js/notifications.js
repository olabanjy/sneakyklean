document.addEventListener("DOMContentLoaded", () => {
  const wrapper = document.querySelector(".notif-wrapper");
  const button = document.getElementById("notif-btn");
  const dropdown = document.getElementById("notif-dropdown");
  const closeButton = document.getElementById("notif-close");
  const dot = wrapper?.querySelector(".notif-dot");
  const items = Array.from(dropdown?.querySelectorAll(".notif-item") || []);

  if (!wrapper || !button || !dropdown || !closeButton || !dot) return;

  const storageKey = `sneakyklean.notifications.lastSeen.${wrapper.dataset.userId}`;
  const latestUpdate = items.reduce((latest, item) => {
    const timestamp = Date.parse(item.dataset.updatedAt || "");
    return Number.isNaN(timestamp) ? latest : Math.max(latest, timestamp);
  }, 0);

  function getLastSeen() {
    try {
      const value = Number.parseInt(window.localStorage.getItem(storageKey) || "0", 10);
      return Number.isNaN(value) ? 0 : value;
    } catch (_error) {
      return 0;
    }
  }

  function updateUnreadDot() {
    dot.hidden = latestUpdate === 0 || latestUpdate <= getLastSeen();
  }

  function markAsRead() {
    if (!latestUpdate) return;

    try {
      window.localStorage.setItem(storageKey, String(latestUpdate));
    } catch (_error) {
      // The dropdown still works when storage is unavailable.
    }

    dot.hidden = true;
  }

  function setOpen(open) {
    dropdown.classList.toggle("is-open", open);
    dropdown.setAttribute("aria-hidden", String(!open));
    button.setAttribute("aria-expanded", String(open));

    if (open) {
      markAsRead();
      closeButton.focus({ preventScroll: true });
    }
  }

  button.addEventListener("click", (event) => {
    event.stopPropagation();
    setOpen(!dropdown.classList.contains("is-open"));
  });

  closeButton.addEventListener("click", (event) => {
    event.stopPropagation();
    setOpen(false);
    button.focus({ preventScroll: true });
  });

  dropdown.addEventListener("click", event => event.stopPropagation());

  document.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && dropdown.classList.contains("is-open")) {
      setOpen(false);
      button.focus({ preventScroll: true });
    }
  });

  window.addEventListener("storage", (event) => {
    if (event.key === storageKey) updateUnreadDot();
  });

  updateUnreadDot();
});
