// ── Utilities ─────────────────────────────────────────────────────────────────

let _uid = 0;
const uid = () => ++_uid;
const $ = (id) => document.getElementById(id);

function debounce(fn, ms) {
    let t;
    return (...a) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...a), ms);
    };
}

// ── Ingredient autocomplete ───────────────────────────────────────────────────

let _modalCallback = null;

function setupAutocomplete(rowId) {
    const input = $(`ing-search-${rowId}`);
    const hidden = $(`ing-id-${rowId}`);
    const drop = $(`ing-drop-${rowId}`);

    const search = debounce(async (q) => {
        if (!q.trim()) {
            drop.classList.add("hidden");
            return;
        }
        const res = await fetch(`/api/ingredients?q=${encodeURIComponent(q)}`);
        const results = await res.json();
        renderDropdown(drop, results, q, input, hidden);
    }, 250);

    input.addEventListener("input", (e) => {
        hidden.value = "";
        search(e.target.value);
    });
    input.addEventListener("focus", (e) => {
        if (e.target.value) search(e.target.value);
    });
    document.addEventListener("click", (e) => {
        if (!input.closest(".autocomplete-wrap").contains(e.target)) {
            drop.classList.add("hidden");
        }
    });
}

function renderDropdown(drop, results, query, input, hidden) {
    drop.innerHTML = "";
    results.forEach((ing) => {
        const li = document.createElement("li");
        li.textContent = ing.name;
        li.onclick = () => {
            input.value = ing.name;
            hidden.value = ing.id;
            drop.classList.add("hidden");
        };
        drop.appendChild(li);
    });

    if (results.length > 0) {
        const divider = document.createElement("li");
        divider.className = "dropdown-divider";
        drop.appendChild(divider);
    }

    const create = document.createElement("li");
    create.className = "dropdown-create";
    create.textContent = results.length ? `+ Create "${query}"` : `No results — create "${query}"`;
    create.onclick = () => {
        drop.classList.add("hidden");
        openCreateModal(query, (ing) => {
            input.value = ing.name;
            hidden.value = ing.id;
        });
    };
    drop.appendChild(create);
    drop.classList.remove("hidden");
}

// ── Create ingredient modal ───────────────────────────────────────────────────

function openCreateModal(name, callback) {
    $("modal-ing-name").value = name;
    $("modal-error").classList.add("hidden");
    $("create-ing-modal").classList.remove("hidden");
    $("modal-ing-name").focus();
    _modalCallback = callback;
}

function closeCreateModal() {
    $("create-ing-modal").classList.add("hidden");
    _modalCallback = null;
}

async function submitCreateIngredient() {
    const name = $("modal-ing-name").value.trim();
    const typeId = parseInt($("modal-ing-type").value);
    if (!name) return;

    const res = await fetch("/api/ingredients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, type_id: typeId }),
    });
    if (res.ok) {
        const ing = await res.json();
        if (_modalCallback) _modalCallback(ing);
        closeCreateModal();
    } else {
        const err = await res.json();
        const el = $("modal-error");
        el.textContent = err.detail || STRINGS.failedCreateIngredient;
        el.classList.remove("hidden");
    }
}

// ── Row helpers ───────────────────────────────────────────────────────────────

function moveRow(btn, down = false) {
    const row = btn.closest(".ingredient-row, .ingredient-group, .step-row");
    const parent = row.parentElement;
    if (down) {
        const next = row.nextElementSibling;
        if (next) parent.insertBefore(next, row);
    } else {
        const prev = row.previousElementSibling;
        if (prev) parent.insertBefore(row, prev);
    }
    if (row.classList.contains("step-row")) updateStepNumbers();
}

function removeRow(id) {
    const el = $(id);
    if (el) {
        el.remove();
        updateStepNumbers();
    }
}

// ── Ingredient rows ───────────────────────────────────────────────────────────

function unitOptions() {
    return AMOUNT_UNITS.map(
        (u) => `<option value="${u.id}">${u.name} (${u.abbreviation})</option>`
    ).join("");
}

function addIngredientRow(containerId) {
    const id = uid();
    const container = $(`${containerId}-ings`);
    const div = document.createElement("div");
    div.id = `ing-row-${id}`;
    div.className = "ingredient-row";
    div.innerHTML = `
        <div class="autocomplete-wrap">
            <input id="ing-search-${id}" type="text" placeholder="${STRINGS.ingredientPlaceholder}" autocomplete="off" class="ing-search">
            <input id="ing-id-${id}" type="hidden">
            <ul id="ing-drop-${id}" class="autocomplete-dropdown hidden"></ul>
        </div>
        <input id="ing-amount-${id}" type="number" placeholder="${STRINGS.amountPlaceholder}" min="0.001" step="0.001" class="ing-amount">
        <select id="ing-unit-${id}" class="ing-unit">${unitOptions()}</select>
        <div class="row-controls">
            <button type="button" class="btn-icon" onclick="moveRow(this)">↑</button>
            <button type="button" class="btn-icon" onclick="moveRow(this, true)">↓</button>
            <button type="button" class="btn-icon btn-remove" onclick="removeRow('ing-row-${id}')">×</button>
        </div>`;
    container.appendChild(div);
    setupAutocomplete(id);
    $(`ing-search-${id}`).focus();
}

// ── Groups ────────────────────────────────────────────────────────────────────

function addGroup() {
    const id = uid();
    const container = $("groups-container");
    const div = document.createElement("div");
    div.id = `group-${id}`;
    div.className = "ingredient-group";
    div.innerHTML = `
        <div class="group-header">
            <input type="text" id="group-name-${id}" class="group-name" placeholder="${STRINGS.groupNamePlaceholder}">
            <div class="row-controls">
                <button type="button" class="btn-icon" onclick="moveRow(this)">↑</button>
                <button type="button" class="btn-icon" onclick="moveRow(this, true)">↓</button>
                <button type="button" class="btn-icon btn-remove" onclick="removeRow('group-${id}')">×</button>
            </div>
        </div>
        <div id="group-${id}-ings" class="ingredient-list group-ingredient-list"></div>
        <button type="button" class="btn-add btn-add-sub" onclick="addIngredientRow('group-${id}')">+ Add ingredient</button>`;
    container.appendChild(div);
    $(`group-name-${id}`).focus();
}

// ── Steps ─────────────────────────────────────────────────────────────────────

function addStep() {
    const id = uid();
    const container = $("steps-container");
    const pos = container.children.length + 1;
    const div = document.createElement("div");
    div.id = `step-row-${id}`;
    div.className = "step-row";
    div.innerHTML = `
        <span class="step-number">${pos}</span>
        <textarea id="step-desc-${id}" class="step-desc" rows="2" placeholder="${STRINGS.stepPlaceholder}"></textarea>
        <div class="step-duration">
            <input id="step-dur-${id}" type="number" class="duration-input" placeholder="—" min="1">
            <span class="duration-unit">min</span>
        </div>
        <div class="row-controls">
            <button type="button" class="btn-icon" onclick="moveRow(this)">↑</button>
            <button type="button" class="btn-icon" onclick="moveRow(this, true)">↓</button>
            <button type="button" class="btn-icon btn-remove" onclick="removeRow('step-row-${id}')">×</button>
        </div>`;
    container.appendChild(div);
    $(`step-desc-${id}`).focus();
}

function updateStepNumbers() {
    document.querySelectorAll("#steps-container .step-row").forEach((row, i) => {
        row.querySelector(".step-number").textContent = i + 1;
    });
}

// ── Collect form data ─────────────────────────────────────────────────────────

function collectIngredients(listId) {
    const list = $(listId);
    if (!list) return [];
    return Array.from(list.querySelectorAll(".ingredient-row"))
        .map((row) => {
            const id = row.id.replace("ing-row-", "");
            return {
                ingredient_id: parseInt($(`ing-id-${id}`).value) || null,
                amount: parseFloat($(`ing-amount-${id}`).value) || null,
                unit_id: parseInt($(`ing-unit-${id}`).value),
            };
        })
        .filter((r) => r.ingredient_id && r.amount);
}

function collectGroups() {
    return Array.from($("groups-container").querySelectorAll(".ingredient-group")).map(
        (g, i) => {
            const id = g.id.replace("group-", "");
            return {
                name: $(`group-name-${id}`).value.trim() || `Group ${i + 1}`,
                position: i,
                ingredients: collectIngredients(`${g.id}-ings`),
            };
        }
    );
}

function collectSteps() {
    return Array.from($("steps-container").querySelectorAll(".step-row"))
        .map((row, i) => {
            const id = row.id.replace("step-row-", "");
            const dur = parseInt($(`step-dur-${id}`).value);
            return {
                position: i + 1,
                description: $(`step-desc-${id}`).value.trim(),
                duration: isNaN(dur) ? null : dur,
            };
        })
        .filter((s) => s.description);
}

// ── Submit ────────────────────────────────────────────────────────────────────

async function submitRecipe(e) {
    e.preventDefault();
    hideError();

    const title = $("f-title").value.trim();
    if (!title) {
        showError(STRINGS.titleRequired);
        return;
    }

    const servings = parseInt($("f-servings").value);
    const payload = {
        title,
        description: $("f-description").value.trim() || null,
        type_id: parseInt($("f-type").value),
        servings: isNaN(servings) ? null : servings,
        ungrouped_ingredients: collectIngredients("ungrouped-ings"),
        ingredient_groups: collectGroups(),
        steps: collectSteps(),
    };

    const btn = $("submit-btn");
    btn.disabled = true;
    btn.textContent = STRINGS.saving;

    try {
        const res = await fetch("/api/recipes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (res.ok) {
            window.location.href = "/dashboard";
        } else {
            const err = await res.json();
            showError(err.detail || STRINGS.failedSave);
        }
    } catch {
        showError(STRINGS.networkError);
    } finally {
        btn.disabled = false;
        btn.textContent = STRINGS.saveRecipe;
    }
}

function showError(msg) {
    const el = $("form-error");
    el.textContent = msg;
    el.classList.remove("hidden");
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function hideError() {
    $("form-error").classList.add("hidden");
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    const typeSelect = $("modal-ing-type");
    INGREDIENT_TYPES.forEach((t) => {
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = t.name;
        typeSelect.appendChild(opt);
    });

    $("recipe-form").addEventListener("submit", submitRecipe);
});
