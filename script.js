async function updateSlots() {
    const dateInput = document.getElementById("date");
    const masterInput = document.getElementById("master_id");
    const timeSelect = document.getElementById("time");

    if (!dateInput || !masterInput || !timeSelect) return;

    const date = dateInput.value;
    const masterId = masterInput.value;

    if (!date || !masterId) {
        timeSelect.innerHTML = '<option value="">Сначала выберите мастера и дату</option>';
        return;
    }

    const response = await fetch(`/slots?date=${date}&master_id=${masterId}`);
    const slots = await response.json();

    timeSelect.innerHTML = "";

    if (!slots.length) {
        timeSelect.innerHTML = '<option value="">Свободных слотов нет</option>';
        return;
    }

    slots.forEach((slot, index) => {
        const option = document.createElement("option");
        option.value = slot;
        option.textContent = slot;
        if (index === 0) option.selected = true;
        timeSelect.appendChild(option);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const dateInput = document.getElementById("date");
    const masterInput = document.getElementById("master_id");

    if (dateInput) dateInput.addEventListener("change", updateSlots);
    if (masterInput) masterInput.addEventListener("change", updateSlots);
});
