function initSlider() {
  const slider = document.querySelector(".sneaky-slider");
  if (!slider) return;

  const divider = slider.querySelector(".sneaky-divider");
  const before = slider.querySelector(".slider-before");

  let isDragging = false;

  const move = (x) => {
    const rect = slider.getBoundingClientRect();
    let pos = Math.max(0, Math.min(x - rect.left, rect.width));
    const percent = (pos / rect.width) * 100;

    before.style.width = percent + "%";
    divider.style.left = percent + "%";
  };

  divider.addEventListener("mousedown", () => isDragging = true);
  window.addEventListener("mouseup", () => isDragging = false);
  window.addEventListener("mousemove", e => isDragging && move(e.clientX));

  divider.addEventListener("touchstart", () => isDragging = true);
  window.addEventListener("touchend", () => isDragging = false);
  window.addEventListener("touchmove", e => isDragging && move(e.touches[0].clientX));
}