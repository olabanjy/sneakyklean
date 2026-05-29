// =========================
// VALIDATION SYSTEM (SYNCED WITH SERVICES.JS)
// =========================
function initValidation() {

  const form = document.querySelector(".pickup-form");
  const submitBtn = document.querySelector(".submit-btn");

  if (!form || !submitBtn) return;

  const inputs = {
    name: form.querySelector('input[name="full_name"]'),
    phone: form.querySelector('input[name="phone"]'),
    email: form.querySelector('input[name="email"]'),
    address: form.querySelector('input[name="address"]'),

    // ✅ FIXED (was broken before)
    date: document.getElementById("pickup-date"),

    quantity: form.querySelector('input[name="quantity"]'),
    terms: form.querySelector('input[name="terms"]'),
    location: form.querySelector('#location-select')
  };

  let selectedPrice = 0;

  /* =========================
     SYNC WITH SERVICE SYSTEM
  ========================= */
  document.addEventListener("serviceSelected", (e) => {
    selectedPrice = e.detail.price || 0;
    updateButton();
  });

  /* =========================
     FIELD VALIDATION
  ========================= */
  function validateField(input) {
    if (!input) return true;

    let valid = true;

    if (input.type === "checkbox") {
      valid = input.checked;
    } 
    else if (input.name === "email") {
      valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim());
    } 
    else if (input.name === "quantity") {
      valid = parseInt(input.value) > 0;
    } 
    else if (input.tagName === "SELECT") {
      valid = input.value !== "";
    } 
    else {
      valid = input.value.trim() !== "";
    }

    input.classList.toggle("input-error", !valid);
    return valid;
  }

  /* =========================
     FORM VALIDATION
  ========================= */
  function isValid() {
    const allValid = Object.values(inputs).every(input => validateField(input));

    // ✅ fallback safety (in case event hasn't fired yet)
    const hasService = selectedPrice > 0;

    return allValid && hasService;
  }

  function updateButton() {
    if (isValid()) {
      submitBtn.style.background = "#fe5a00";
      submitBtn.disabled = false;
    } else {
      submitBtn.style.background = "#999";
      submitBtn.disabled = true;
    }
  }

  /* =========================
     LISTENERS
  ========================= */
  Object.values(inputs).forEach(input => {
    if (!input) return;

    input.addEventListener("input", () => {
      validateField(input);
      updateButton();

      if (typeof updatePriceUI === "function") {
        updatePriceUI();
      }
    });

    input.addEventListener("blur", () => {
      validateField(input);
    });
  });

  if (inputs.terms) {
    inputs.terms.addEventListener("change", () => {
      validateField(inputs.terms);
      updateButton();
    });
  }

  /* =========================
     INIT STATE (IMPORTANT)
  ========================= */
  updateButton(); // ✅ ensures correct state on load
}

// =========================
// INIT
// =========================
document.addEventListener("DOMContentLoaded", initValidation);