function initCounter() {
  const counter = document.getElementById("sneaky-count");
  if (!counter) return;

  let done = false;

  const animate = () => {
    let start = 0;
    const target = parseInt(counter.textContent);
    const step = target / 100;

    const run = () => {
      start += step;
      if (start < target) {
        counter.textContent = Math.floor(start);
        requestAnimationFrame(run);
      } else {
        counter.textContent = target;
      }
    };

    run();
  };

  new IntersectionObserver(entries => {
    if (entries[0].isIntersecting && !done) {
      animate();
      done = true;
    }
  }).observe(counter);
}