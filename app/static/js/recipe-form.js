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
    const classification = $("modal-ing-classification").value;
    if (!name) return;

    const res = await fetch("/api/ingredients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, type_id: typeId, classification }),
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

// ── Image upload ──────────────────────────────────────────────────────────────

async function uploadImage(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/uploads", { method: "POST", body: fd });
    if (!res.ok) throw new Error(STRINGS.uploadFailed);
    return await res.json();
}

function setRecipeImage(filename) {
    $("recipe-image-preview").src = "/uploads/thumb_" + filename;
    $("recipe-image-filename").value = filename;
    $("recipe-image-preview-wrap").classList.remove("hidden");
    $("recipe-image-label").classList.add("hidden");
}

function clearRecipeImage() {
    $("recipe-image-preview").src = "";
    $("recipe-image-filename").value = "";
    $("recipe-image-preview-wrap").classList.add("hidden");
    $("recipe-image-label").classList.remove("hidden");
    $("recipe-image-input").value = "";
}

function addStepImagePreview(stepRowId, filename) {
    const strip = $("step-img-strip-" + stepRowId);
    const wrapper = document.createElement("div");
    wrapper.className = "step-img-thumb";
    wrapper.dataset.filename = filename;

    const img = document.createElement("img");
    img.src = "/uploads/thumb_" + filename;
    img.alt = "";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "image-remove-btn";
    btn.setAttribute("aria-label", STRINGS.removeImage);
    btn.textContent = "×";
    btn.addEventListener("click", () => {
        wrapper.remove();
        _syncStepFilenames(stepRowId);
    });

    wrapper.appendChild(img);
    wrapper.appendChild(btn);
    strip.appendChild(wrapper);
    _syncStepFilenames(stepRowId);
}

function _syncStepFilenames(stepRowId) {
    const row = $("step-row-" + stepRowId);
    const filenames = [...row.querySelectorAll(".step-img-thumb")].map((el) => el.dataset.filename);
    row.dataset.imageFilenames = JSON.stringify(filenames);
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

function addIngredientRow(containerId, skipFocus = false) {
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
    if (!skipFocus) $(`ing-search-${id}`).focus();
    return id;
}

// ── Groups ────────────────────────────────────────────────────────────────────

function addGroup(skipFocus = false) {
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
        <button type="button" class="btn-add btn-add-sub" onclick="addIngredientRow('group-${id}')">${STRINGS.addIngredient}</button>`;
    container.appendChild(div);
    if (!skipFocus) $(`group-name-${id}`).focus();
    return id;
}

// ── Steps ─────────────────────────────────────────────────────────────────────

function addStep(skipFocus = false) {
    const id = uid();
    const container = $("steps-container");
    const pos = container.children.length + 1;
    const div = document.createElement("div");
    div.id = "step-row-" + id;
    div.className = "step-row";
    div.dataset.imageFilenames = "[]";

    // Step number
    const num = document.createElement("span");
    num.className = "step-number";
    num.textContent = pos;

    // Description textarea
    const ta = document.createElement("textarea");
    ta.id = "step-desc-" + id;
    ta.className = "step-desc";
    ta.rows = 2;
    ta.placeholder = STRINGS.stepPlaceholder;

    // Duration
    const durWrap = document.createElement("div");
    durWrap.className = "step-duration";
    const durInput = document.createElement("input");
    durInput.id = "step-dur-" + id;
    durInput.type = "number";
    durInput.className = "duration-input";
    durInput.placeholder = "—";
    durInput.min = "1";
    const durUnit = document.createElement("span");
    durUnit.className = "duration-unit";
    durUnit.textContent = "min";
    durWrap.appendChild(durInput);
    durWrap.appendChild(durUnit);

    // Step images strip
    const strip = document.createElement("div");
    strip.className = "step-images-strip";
    strip.id = "step-img-strip-" + id;

    // Add image label/button
    const imgLabel = document.createElement("label");
    imgLabel.className = "btn-add btn-add-img";
    const imgInput = document.createElement("input");
    imgInput.type = "file";
    imgInput.accept = "image/*";
    imgInput.id = "step-img-input-" + id;
    imgInput.className = "sr-only";
    const imgSpan = document.createElement("span");
    imgSpan.textContent = STRINGS.addImage;
    imgLabel.appendChild(imgInput);
    imgLabel.appendChild(imgSpan);

    imgInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        imgSpan.textContent = STRINGS.uploading;
        imgLabel.classList.add("uploading");
        try {
            const data = await uploadImage(file);
            addStepImagePreview(id, data.filename);
        } catch {
            imgSpan.textContent = STRINGS.uploadFailed;
            setTimeout(() => { imgSpan.textContent = STRINGS.addImage; }, 2000);
        } finally {
            imgLabel.classList.remove("uploading");
            imgSpan.textContent = STRINGS.addImage;
            e.target.value = "";
        }
    });

    // Row controls
    const controls = document.createElement("div");
    controls.className = "row-controls";
    const btnUp = document.createElement("button");
    btnUp.type = "button";
    btnUp.className = "btn-icon";
    btnUp.textContent = "↑";
    btnUp.addEventListener("click", () => moveRow(btnUp));
    const btnDown = document.createElement("button");
    btnDown.type = "button";
    btnDown.className = "btn-icon";
    btnDown.textContent = "↓";
    btnDown.addEventListener("click", () => moveRow(btnDown, true));
    const btnRm = document.createElement("button");
    btnRm.type = "button";
    btnRm.className = "btn-icon btn-remove";
    btnRm.textContent = "×";
    btnRm.addEventListener("click", () => removeRow("step-row-" + id));
    controls.appendChild(btnUp);
    controls.appendChild(btnDown);
    controls.appendChild(btnRm);

    div.appendChild(num);
    div.appendChild(ta);
    div.appendChild(durWrap);
    div.appendChild(strip);
    div.appendChild(imgLabel);
    div.appendChild(controls);
    container.appendChild(div);

    if (!skipFocus) $("step-desc-" + id).focus();
    return id;
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
            const dur = parseInt($("step-dur-" + id).value);
            return {
                position: i + 1,
                description: $("step-desc-" + id).value.trim(),
                duration: isNaN(dur) ? null : dur,
                image_filenames: JSON.parse(row.dataset.imageFilenames || "[]"),
            };
        })
        .filter((s) => s.description);
}

// ── Submit ────────────────────────────────────────────────────────────────────

function validateIngredientRows(listId) {
    const list = $(listId);
    if (!list) return true;
    for (const row of list.querySelectorAll(".ingredient-row")) {
        const id = row.id.replace("ing-row-", "");
        const ingId = $(`ing-id-${id}`).value;
        const amount = $(`ing-amount-${id}`).value;
        if (ingId && !amount) return false;
    }
    return true;
}

async function submitRecipe(e) {
    e.preventDefault();
    hideError();

    const title = $("f-title").value.trim();
    if (!title) {
        showError(STRINGS.titleRequired);
        return;
    }

    const servings = parseInt($("f-servings").value);
    const ungrouped = collectIngredients("ungrouped-ings");
    const groups = collectGroups();
    const steps = collectSteps();

    // Validate: each selected ingredient must have an amount
    const ungroupedOk = validateIngredientRows("ungrouped-ings");
    const groupsOk = Array.from($("groups-container").querySelectorAll(".ingredient-group"))
        .every((g) => validateIngredientRows(`${g.id}-ings`));
    if (!ungroupedOk || !groupsOk) {
        showError(STRINGS.amountRequired);
        return;
    }

    // Validate: at least one ingredient
    const totalIngredients = ungrouped.length + groups.reduce((s, g) => s + g.ingredients.length, 0);
    if (totalIngredients === 0) {
        showError(STRINGS.ingredientRequired);
        return;
    }

    // Validate: at least one step
    if (steps.length === 0) {
        showError(STRINGS.stepRequired);
        return;
    }

    const payload = {
        title,
        description: $("f-description").value.trim() || null,
        type_id: parseInt($("f-type").value),
        servings: isNaN(servings) ? null : servings,
        image_filename: $("recipe-image-filename").value || null,
        ungrouped_ingredients: ungrouped,
        ingredient_groups: groups,
        steps,
    };

    const btn = $("submit-btn");
    btn.disabled = true;
    btn.textContent = STRINGS.saving;

    const url = RECIPE_ID != null ? `/api/recipes/${RECIPE_ID}` : "/api/recipes";
    const method = RECIPE_ID != null ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (res.ok) {
            const data = await res.json();
            window.location.href = `/recipes/${data.id}`;
        } else {
            const err = await res.json();
            showError(err.detail || STRINGS.failedSave);
        }
    } catch {
        showError(STRINGS.networkError);
    } finally {
        btn.disabled = false;
        btn.textContent = RECIPE_ID != null ? STRINGS.saveChanges : STRINGS.saveRecipe;
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

// ── Prefill (edit mode) ───────────────────────────────────────────────────────

function prefillIngredient(containerId, ing) {
    const rowId = addIngredientRow(containerId, true);
    $(`ing-search-${rowId}`).value = ing.ingredient_name;
    $(`ing-id-${rowId}`).value = ing.ingredient_id;
    $(`ing-amount-${rowId}`).value = ing.amount;
    $(`ing-unit-${rowId}`).value = ing.unit_id;
}

function prefillForm(data) {
    $("f-title").value = data.title || "";
    $("f-description").value = data.description || "";
    $("f-servings").value = data.servings || "";
    $("f-type").value = data.type_id;

    if (data.image_filename) setRecipeImage(data.image_filename);

    (data.ungrouped_ingredients || []).forEach((ing) => prefillIngredient("ungrouped", ing));

    (data.ingredient_groups || []).forEach((group) => {
        const groupId = addGroup(true);
        $("group-name-" + groupId).value = group.name;
        (group.ingredients || []).forEach((ing) => prefillIngredient("group-" + groupId, ing));
    });

    (data.steps || []).forEach((step) => {
        const stepId = addStep(true);
        $("step-desc-" + stepId).value = step.description;
        if (step.duration) $("step-dur-" + stepId).value = step.duration;
        (step.image_filenames || []).forEach((fn) => addStepImagePreview(stepId, fn));
    });
    updateStepNumbers();
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

    const classSelect = $("modal-ing-classification");
    INGREDIENT_CLASSIFICATIONS.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.value;
        opt.textContent = c.label;
        classSelect.appendChild(opt);
    });

    $("recipe-form").addEventListener("submit", submitRecipe);

    // Recipe cover image upload
    const recipeImgInput = $("recipe-image-input");
    recipeImgInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const status = $("recipe-image-status");
        status.textContent = STRINGS.uploading;
        status.classList.remove("hidden");
        try {
            const data = await uploadImage(file);
            setRecipeImage(data.filename);
        } catch {
            status.textContent = STRINGS.uploadFailed;
            setTimeout(() => status.classList.add("hidden"), 2000);
        } finally {
            status.classList.add("hidden");
            recipeImgInput.value = "";
        }
    });
    $("recipe-image-remove").addEventListener("click", clearRecipeImage);

    if (RECIPE_DATA) {
        prefillForm(RECIPE_DATA);
        $("submit-btn").textContent = STRINGS.saveChanges;
    }
});
