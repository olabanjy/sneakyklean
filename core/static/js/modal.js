function initModal() {
  const modal = document.getElementById("pickup-modal");
  const openBtn = document.getElementById("sneaky-book-btn");
  const closeBtn = document.getElementById("pickup-close");
  const backdrop = document.querySelector(".pickup-backdrop");

  if (!modal || !openBtn) return;

  const open = () => {
    modal.classList.add("active");
    document.body.classList.add("no-scroll");
  };

  const close = () => {
    modal.classList.remove("active");
    document.body.classList.remove("no-scroll");
  };

  openBtn.addEventListener("click", open);
  closeBtn?.addEventListener("click", close);
  backdrop?.addEventListener("click", close);
}