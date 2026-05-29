/* =========================
   CONTEXT-AWARE SERVICES DASH
   (FOR index.html BOOKING FORM)
   - Dynamically loads services from Django API
   - Submits service IDs to backend
========================= */

document.addEventListener("DOMContentLoaded", async () => {

  /* =========================
     ELEMENTS (FIXED SELECTORS)
  ========================= */
  const grid = document.getElementById("service-grid");
  const toggleBtn = document.getElementById("service-toggle-btn");

  const subtotalEl = document.getElementById("subtotal");
  const vatEl = document.getElementById("vat");
  const totalEl = document.getElementById("total");
  const deliveryEl = document.getElementById("delivery");
  const serviceNameEl = document.getElementById("selected-service");

  const submitBtn = document.querySelector(".submit-btn");
  const form = document.querySelector("form.pickup-form");

  /* INPUTS (MATCHED TO HTML) */
  const inputs = {
    name: document.querySelector('input[name="full_name"]'),
    phone: document.querySelector('input[name="phone"]'),
    email: document.querySelector('input[name="email"]'),
    address: document.querySelector('input[name="address"]'),
    date: document.getElementById("pickup-date"),
    quantity: document.querySelector('input[name="quantity"]'),
    location: document.getElementById("location-select")
  };

  /* =========================
     STATE
  ========================= */
  let servicesData = []; // Loaded from API
  let selectedServices = [];
  let isOpen = false;

  let discountApplied = false;
  let discountValue = 0;

  /* =========================
     LOAD SERVICES FROM API
  ========================= */
  async function loadServices() {
    try {
      const response = await fetch('/api/services/');
      if (!response.ok) throw new Error('Failed to load services');
      
      servicesData = await response.json();
      servicesData.sort((a, b) => a.display_order - b.display_order);
      
      renderServiceCards();
      initCardEvents();
      
    } catch (error) {
      console.error('Error loading services:', error);
      showToast('Failed to load services. Please refresh.', 'error');
    }
  }

  /* =========================
     RENDER SERVICE CARDS
  ========================= */
  function renderServiceCards() {
    grid.innerHTML = '';
    
    servicesData.forEach((service, index) => {
      const colors = ['orange', 'green', 'blue', 'pink'];
      const color = colors[index % colors.length];
      
      const card = document.createElement('div');
      card.className = `service-card ${color}`;
      card.dataset.serviceId = service.id;
      card.dataset.price = service.price;
      
      card.innerHTML = `
        <h3>${service.name}</h3>
        <p>₦${parseFloat(service.price).toLocaleString()}</p>
        <div class="service-tags">
          ${service.description ? `<span class="tag">${service.description}</span>` : ''}
        </div>
        <button>Select</button>
      `;
      
      grid.appendChild(card);
    });
  }

  /* =========================
     INIT CARD EVENTS
  ========================= */
  function initCardEvents() {
    const cards = document.querySelectorAll(".service-card");
    cards.forEach(card => {
      card.querySelector("button").addEventListener("click", () => {
        handleSelection(card);
      });
    });
  }

  /* =========================
     TOAST (REPLACED + UNIFIED)
  ========================= */
  function showToast(message, type) {
    if (window.InfoToast) {
      InfoToast.show(message, type);
    }
  }
  

  /* =========================
     HELPERS
  ========================= */
  function getType(name) {
    const n = name.toLowerCase();
    if (n.includes("basic") || n.includes("deep")) return "cleaning";
    if (n.includes("suede")) return "suede";
    if (n.includes("restoration")) return "restoration";
    return "other";
  }

  function getTotalServicePrice() {
    return selectedServices.reduce((sum, s) => sum + s.price, 0);
  }

  /* =========================
     TOGGLE GRID
  ========================= */
  function updateToggleText() {
    if (isOpen) {
      toggleBtn.textContent = "− Hide selection";
    } else if (selectedServices.length === 0) {
      toggleBtn.textContent = "+ Select Service";
    } else {
      toggleBtn.innerHTML = `<span class="mdi mdi-swap-horizontal-circle-outline"></span> Change Service`;
    }
  }

  toggleBtn.addEventListener("click", () => {
    isOpen = !isOpen;
    grid.style.display = isOpen ? "grid" : "none";
    updateToggleText();
  });

  /* =========================
     CORE SELECTION
  ========================= */
  function handleSelection(card) {
    const serviceId = parseInt(card.dataset.serviceId);
    const price = parseFloat(card.dataset.price);
    const name = card.querySelector("h3").textContent;
    const type = getType(name);

    const exists = selectedServices.find(s => s.id === serviceId);

    const hasCleaning = selectedServices.some(s => s.type === "cleaning");
    const hasRestoration = selectedServices.some(s => s.type === "restoration");

    // REMOVE
    if (exists) {
      selectedServices = selectedServices.filter(s => s.id !== serviceId);
      refreshUI();
      showToast("Service removed");
      return;
    }

    // INVALID COMBO RULES
    if (hasRestoration && type === "cleaning") {
      showToast("Invalid combination", "error");
      return;
    }

    if (type === "restoration" && hasCleaning) {
      showToast("Invalid combination", "error");
      return;
    }

    // CLEANING SWITCH
    if (type === "cleaning" && hasCleaning) {
      selectedServices = selectedServices.filter(s => s.type !== "cleaning");
    }

    selectedServices.push({ id: serviceId, card, price, type, name });

    refreshUI();
    showToast("Service selected");
  }

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
  }

  function updateCards() {
    const cards = document.querySelectorAll(".service-card");
    
    cards.forEach(card => {
      card.classList.remove("active");
      card.querySelector("button").textContent = "Select";
      card.style.opacity = "1";
    });

    selectedServices.forEach(s => {
      s.card.classList.add("active");
      s.card.querySelector("button").textContent = "Remove";
    });

    // dim cleaning if restoration selected
    if (selectedServices.some(s => s.type === "restoration")) {
      cards.forEach(card => {
        const name = card.querySelector("h3").textContent.toLowerCase();
        if (name.includes("cleaning")) {
          card.style.opacity = "0.4";
        }
      });
    }
  }

  function updateServiceText() {
    const serviceName = selectedServices.length
      ? selectedServices.map(s => s.name).join(" + ")
      : "None";
    serviceNameEl.textContent = serviceName;
  }

  /* =========================
   QUANTITY (BUSINESS RULE)
========================= */
  function updateQuantity() {
    const serviceCount = selectedServices.length;

    if (serviceCount > 1) {
      inputs.quantity.value = 2;
      inputs.quantity.disabled = true;
      inputs.quantity.style.opacity = "0.6";
      return 2;
    }

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
     PRICE SYSTEM
  ========================= */
  function updatePrice() {
    const quantity = updateQuantity();

    const serviceTotal = getTotalServicePrice();
    const isCombo = selectedServices.length > 1;

    const subtotal = isCombo
      ? serviceTotal
      : serviceTotal * quantity;

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
     DISCOUNT SYSTEM
  ========================= */
  const discountInput = document.getElementById("discount-code");
  const discountBtn = document.getElementById("apply-discount");

  discountBtn.addEventListener("click", () => {
    const code = discountInput.value.trim().toUpperCase();

    if (discountApplied) return;

    if (code === "SNKYLN") {
      discountApplied = true;
      discountValue = 2000;

      discountInput.disabled = true;
      discountBtn.disabled = true;
      discountBtn.textContent = "Applied";

      showToast("Discount applied");
    } else {
      showToast("Invalid code");
    }

    updatePrice();
  });

  /* =========================
     VALIDATION
  ========================= */
  function isValid() {
    return (
      inputs.name.value.trim() &&
      inputs.phone.value.trim() &&
      inputs.email.value.trim() &&
      inputs.address.value.trim() &&
      inputs.date.value.trim() &&
      inputs.location.value &&
      selectedServices.length > 0
    );
  }

  function updateButtonState() {
    submitBtn.disabled = !isValid();
    submitBtn.style.background = isValid() ? "#fe5a00" : "#999";
  }

  /* =========================
     EVENTS
  ========================= */
  Object.values(inputs).forEach(input => {
    if (!input) return;

    input.addEventListener("input", () => {
      updateQuantity();
      updatePrice();
      updateButtonState();
    });

    input.addEventListener("change", updateButtonState);
  });

  /* =========================
     FORM SUBMISSION
  ========================= */
  form.addEventListener("submit", (e) => {
    // Remove any existing service_ids[] inputs
    const existingInputs = form.querySelectorAll('input[name="service_ids[]"]');
    existingInputs.forEach(input => input.remove());

    // Add hidden inputs for each selected service
    selectedServices.forEach(service => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = "service_ids[]";
      input.value = service.id;
      form.appendChild(input);
    });
  });

  /* =========================
     QUICK SELECT (HERO CARDS)
  ========================= */
  function initQuickSelect() {
    const previewCards = document.querySelectorAll(".sneaky-card");
    const modal = document.getElementById("pickup-modal");

    previewCards.forEach(preview => {
      preview.addEventListener("click", () => {
        const serviceName = preview.dataset.service;

        // open modal
        modal.classList.add("active");
        document.body.classList.add("no-scroll");

        // match service
        const cards = document.querySelectorAll(".service-card");
        const match = Array.from(cards).find(card =>
          card.querySelector("h3").textContent === serviceName
        );

        if (!match) return;

        handleSelection(match);

        setTimeout(() => {
          match.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 300);
      });
    });
  }

  /* =========================
     INIT
  ========================= */
  grid.style.display = "none";
  submitBtn.disabled = true;
  submitBtn.style.background = "#999";

  // Load services from API
  await loadServices();

  initQuickSelect();
  updateToggleText();

});