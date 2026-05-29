function initValidation() {

  const inputs = {
    address: document.getElementById("address-input"),
    location: document.getElementById("location-select"),
    date: document.getElementById("pickup-date"),
    quantity: document.querySelector('input[name="quantity"]'),
    terms: document.querySelector('input[name="terms"]')
  };

  function validateField(input) {
    if (!input) return false;

    let valid = true;

    if (input.type === "checkbox") {
      valid = input.checked;
    } 
    else if (input.name === "quantity") {
      const val = parseInt(input.value, 10);
      valid = !isNaN(val) && val > 0;
    } 
    else if (input.id === "pickup-date") {
      valid = input.value.trim() !== "";
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

  function isValid() {
    const fieldsValid = Object.values(inputs).every(input => validateField(input));
    const hasService = window.selectedServices && window.selectedServices.length > 0;

    return fieldsValid && hasService;
  }

  function updateButton() {
    if (typeof updateButtonState === "function") {
      updateButtonState();
    }
  }

  Object.values(inputs).forEach(input => {
    if (!input) return;

    input.addEventListener("input", () => {
      validateField(input);
      updateButton();
    });

    input.addEventListener("change", () => {
      validateField(input);
      updateButton();
    });
  });

  document.querySelectorAll(".dropdown-item").forEach(item => {
    item.addEventListener("click", () => {
      inputs.address.value = item.dataset.address;
      inputs.location.value = item.dataset.area;

      inputs.address.dispatchEvent(new Event("input"));
      inputs.location.dispatchEvent(new Event("input"));
    });
  });

  updateButton();
}

document.addEventListener("DOMContentLoaded", initValidation);