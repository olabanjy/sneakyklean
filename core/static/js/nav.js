function initNav() {
  const toggle = document.getElementById("sneaky-nav-toggle");
  const links = document.getElementById("sneaky-nav-links");

  if (!toggle || !links) return;

  toggle.addEventListener("click", () => {
    links.classList.toggle("active");
    toggle.classList.toggle("active");
    document.body.classList.toggle("no-scroll");
  });

  document.querySelectorAll("#sneaky-nav-links a").forEach(link => {
    link.addEventListener("click", () => {
      links.classList.remove("active");
      toggle.classList.remove("active");
      document.body.classList.remove("no-scroll");
    });
  });

  let lastScroll = 0;
  const nav = document.getElementById("sneaky-nav");

  window.addEventListener("scroll", () => {
    const current = window.pageYOffset;

    nav.classList.toggle("sneaky-nav-scrolled", current > 10);

    if (!links.classList.contains("active")) {
      nav.classList.toggle(
        "sneaky-nav-hidden",
        current > lastScroll && current > 80
      );
    }

    lastScroll = current;
  });
}