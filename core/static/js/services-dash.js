/* =========================
   ELEMENTS
========================= */
const grid = document.getElementById("service-grid");
const toggleBtn = document.getElementById("service-toggle-btn");
const cards = document.querySelectorAll(".service-card");

const subtotalEl = document.getElementById("subtotal");
const vatEl = document.getElementById("vat");
const totalEl = document.getElementById("total");
const deliveryEl = document.getElementById("delivery");
const serviceNameEl = document.getElementById("selected-service");

const submitBtn = document.querySelector(".submit-btn");

/* INPUTS */
const inputs = {
  name: document.querySelector('input[name="full_name"]'),
  phone: document.querySelector('input[name="phone"]'),
  email: document.querySelector('input[name="email"]'),
  address: document.querySelector('#address-input'),
  date: document.getElementById("pickup-date"),
  quantity: document.querySelector('input[name="quantity"]'),
  location: document.getElementById("location-select")
};

/* =========================
   DISCOUNT
========================= */
/* =========================
   DISCOUNT
========================= */
const discountInput = document.getElementById("discount-code");
const discountBtn = document.getElementById("apply-discount");

let discountApplied = false;
let discountValue = 0;

/* =========================
   DISCOUNT SYSTEM (ADD HERE)
========================= */
if (discountBtn) {
  discountBtn.addEventListener("click", () => {
    const code = discountInput.value.trim().toUpperCase();

    if (discountApplied) return;

    if (code === "SNKYLN") {
      discountApplied = true;
      discountValue = 2000;

      discountInput.disabled = true;
      discountBtn.disabled = true;
      discountBtn.textContent = "Applied";

      if (window.InfoToast) {
        InfoToast.show("Discount applied");
      }
    } else {
      if (window.InfoToast) {
        InfoToast.show("Invalid code", "error");
      }
    }

    updatePrice(); // 🔥 important
  });
}

/* =========================
   TOAST
========================= */
const toast = document.getElementById("service-toast");
const toastMsg = document.getElementById("toast-message");
const toastConfirm = document.getElementById("toast-confirm");
const toastCancel = document.getElementById("toast-cancel");

let toastCallback = null;

function showToast(message, onConfirm) {
  if (!toast) return;

  toast.classList.remove("active");

  setTimeout(() => {
    toastMsg.textContent = message;
    toast.classList.add("active");
    toastCallback = onConfirm || null;
  }, 10);
}

toastConfirm.addEventListener("click", () => {
  if (!toast.classList.contains("active")) return;

  toast.classList.remove("active");

  if (typeof toastCallback === "function") {
    toastCallback();
  }

  toastCallback = null;
});

toastCancel.addEventListener("click", () => {
  toast.classList.remove("active");
  toastCallback = null;
});

/* =========================
   STATE
========================= */
window.selectedServices = [];
let isOpen = false;

/* =========================
   HELPERS
========================= */
function getType(name) {
  const n = name.toLowerCase();
  if (n.includes("basic") || n.includes("deep")) return "cleaning";
  if (n.includes("suede")) return "suede";
  if (n.includes("restoration")) return "restoration";
  return "unknown";
}

function getTotalServicePrice() {
  return window.selectedServices.reduce((sum, s) => sum + s.price, 0);
}

/* =========================
   TOGGLE TEXT
========================= */
function updateToggleText() {
  if (isOpen) {
    toggleBtn.textContent = "− Hide selection";
    return;
  }

  if (window.selectedServices.length === 0) {
    toggleBtn.textContent = "+ Select Service";
  } else {
    toggleBtn.innerHTML = `<span class="mdi mdi-swap-horizontal-circle-outline"></span> Change Service`;
  }
}

/* =========================
   TOGGLE GRID
========================= */
toggleBtn.addEventListener("click", () => {
  isOpen = !isOpen;
  grid.style.display = isOpen ? "grid" : "none";
  updateToggleText();
});

/* =========================
   CORE SELECTION (FIXED LOGIC ONLY)
========================= */
window.handleSelection = function(card) {

  const price = parseInt(card.dataset.price);
  const name = card.querySelector("h3").textContent;
  const type = getType(name);

  if (!price || isNaN(price)) return;

  const exists = window.selectedServices.find(s => s.card === card);
  const hasRestoration = window.selectedServices.some(s => s.type === "restoration");
  const hasCleaning = window.selectedServices.some(s => s.type === "cleaning");

  // REMOVE
  if (exists) {
    window.selectedServices = window.selectedServices.filter(s => s.card !== card);
    refreshUI();
    if (window.InfoToast) InfoToast.show("Service removed");
    return;
  }

  // ❌ BLOCK: restoration + cleaning
  if (hasRestoration && type === "cleaning") {
    if (window.InfoToast) InfoToast.show("Invalid combination", "error");
    return;
  }

  // ❌ BLOCK: cleaning + restoration
  if (type === "restoration" && hasCleaning) {
    if (window.InfoToast) InfoToast.show("Invalid combination", "error");
    return;
  }

  // CLEANING SWITCH (only one cleaning)
  if (type === "cleaning" && hasCleaning) {
    window.selectedServices = window.selectedServices.filter(s => s.type !== "cleaning");
  }

  // ADD (allows restoration + suede naturally)
  window.selectedServices.push({ card, price, type, name });

  refreshUI();

  if (window.InfoToast) InfoToast.show("Service selected", "success");
};

/* =========================
   UI UPDATE
========================= */
function refreshUI() {
  updateCards();
  updateServiceText();
  updateQuantity();
  updatePrice();
  updateButtonState();
  updateToggleText();

  document.dispatchEvent(new CustomEvent("serviceSelected", {
    detail: { price: getTotalServicePrice() }
  }));
}

function updateCards() {
  cards.forEach(card => {
    card.classList.remove("active");
    card.querySelector("button").textContent = "Select";
    card.style.opacity = "1";
  });

  window.selectedServices.forEach(s => {
    s.card.classList.add("active");
    s.card.querySelector("button").textContent = "Remove";
  });

  if (window.selectedServices.some(s => s.type === "restoration")) {
  cards.forEach(card => {
    const name = card.querySelector("h3").textContent.toLowerCase();
    const type = getType(name);

    // ❌ only dim cleaning
    if (type === "cleaning") {
      card.style.opacity = "0.4";
    }
  });
}
}

function updateServiceText() {
  serviceNameEl.textContent = window.selectedServices.length
    ? window.selectedServices.map(s => s.name).join(" + ")
    : "None";
}

function updateQuantity() {
  const serviceCount = window.selectedServices.length;

  // 🔒 COMBO MODE
  if (serviceCount > 1) {
    inputs.quantity.value = 2;
    inputs.quantity.disabled = true;
    inputs.quantity.style.opacity = "0.6";
    return 2;
  }

  // ✅ SINGLE SERVICE MODE (DO NOT OVERRIDE USER INPUT)
  inputs.quantity.disabled = false;
  inputs.quantity.style.opacity = "1";

  let qty = parseInt(inputs.quantity.value);

  if (isNaN(qty) || qty < 1) {
    qty = 1;
    inputs.quantity.value = 1;
  }

  return qty;
}

/* =========================
   PRICE
========================= */
function updatePrice() {
  const quantity = updateQuantity();

  const serviceTotal = getTotalServicePrice();
  const isCombo = window.selectedServices.length > 1;

  // 🔥 KEY FIX
  const subtotal = isCombo
    ? serviceTotal              // combo = flat bundle
    : serviceTotal * quantity;  // single service = per quantity

  const delivery = 3500;
  const vat = subtotal * 0.075;

  let total = subtotal + vat + delivery;

  if (discountApplied) {
    total = Math.max(0, total - discountValue);
  }

  subtotalEl.textContent = subtotal.toLocaleString();
  vatEl.textContent = Math.round(vat).toLocaleString();
  deliveryEl.textContent = delivery.toLocaleString();

  if (discountApplied) {
    const originalTotal = subtotal + vat + delivery;

    totalEl.innerHTML = `
      <span class="old-price">₦${Math.round(originalTotal).toLocaleString()}</span>
      <span class="discounted-price">₦${Math.round(total).toLocaleString()}</span>
    `;
  } else {
    totalEl.textContent = Math.round(total).toLocaleString();
  }
}
/* =========================
   VALIDATION
========================= */
function isValid() {
  return (
    inputs.address.value.trim() !== "" &&
    inputs.date.value.trim() !== "" &&
    inputs.location.value !== "" &&
    window.selectedServices.length > 0
  );
}

function updateButtonState() {
  submitBtn.disabled = !isValid();
  submitBtn.style.background = isValid() ? "#fe5a00" : "#999";
}

/* =========================
   EVENTS
========================= */
cards.forEach(card => {
  const btn = card.querySelector("button");
  btn.addEventListener("click", () => {
    window.handleSelection(card);
  });
});

/* =========================
   INPUT LISTENERS
========================= */
Object.values(inputs).forEach(input => {
  if (!input) return;

  input.addEventListener("input", () => {
    updatePrice();
    updateButtonState();
  });

  input.addEventListener("change", updateButtonState);
});

/* =========================
   INIT
========================= */
grid.style.display = "none";
isOpen = false;

submitBtn.disabled = true;
submitBtn.style.background = "#999";

updateToggleText();