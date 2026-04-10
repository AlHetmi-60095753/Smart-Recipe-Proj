const el = (id) => document.getElementById(id);
const ingredientIds = ["ingredient-1", "ingredient-2", "ingredient-3", "ingredient-4", "ingredient-5"];

let currentRecipe = null;
let customMode = false;

const getIngredients = () =>
  ingredientIds.map((id) => el(id).value.trim()).filter(Boolean);

const setIngredients = (items = []) =>
  ingredientIds.forEach((id, i) => (el(id).value = items[i] || ""));

const parseIdeaList = () =>
  el("recipe-idea").value.split(",").map((x) => x.trim()).filter(Boolean);

function toggle(id, show) {
  el(id).classList.toggle("hidden", !show);
}

function setError(message = "") {
  el("error-msg").textContent = message;
  toggle("error-msg", !!message);
}

function updateUI() {
  el("mode-toggle").setAttribute("aria-pressed", String(customMode));
  el("mode-label").textContent = customMode ? "Custom Recipe" : "5 Ingredients";
  el("recipe-name").disabled = !customMode;
  el("recipe-idea").disabled = !customMode;
  el("save-btn").disabled = !customMode && !currentRecipe;
  el("save-btn").textContent = customMode ? "Save Custom Recipe" : "Save Recipe";
}

function setLoading(loading) {
  el("generate-btn").disabled = loading;
  el("save-btn").disabled = loading || (!customMode && !currentRecipe);
  toggle("loading", loading);
  if (!loading) updateUI();
}

function getInput({ customOnly = false, requireName = false } = {}) {
  setError();

  if (customOnly && !customMode) {
    setError("Switch to Custom Recipe mode to save a custom recipe.");
    return null;
  }

  const name = customMode ? el("recipe-name").value.trim() : "";
  const ideaList = customMode ? parseIdeaList() : [];

  if (ideaList.length) {
    if (ideaList.length !== 5) {
      setError("Custom recipe mode requires exactly 5 ingredients in the ingredients list.");
      return null;
    }
    setIngredients(ideaList);
  }

  const ingredients = getIngredients();
  if (ingredients.length !== 5) {
    setError("Please enter exactly 5 ingredients.");
    return null;
  }

  if (requireName && !name) {
    setError("Enter a recipe name in custom mode.");
    return null;
  }

  return { name, ingredients };
}

function renderRecipe(recipe) {
  currentRecipe = recipe;
  el("recipe-title").textContent = recipe.recipeName;
  el("ingredients-used").textContent = recipe.ingredientsUsed.join(", ");
  el("cooking-time").textContent = recipe.cookingTime;
  el("servings").textContent = recipe.servings;
  el("steps-list").innerHTML = recipe.steps.map((step) => `<li>${step}</li>`).join("");
  toggle("recipe-empty", false);
  toggle("recipe-content", true);
  el("save-status").textContent = "";
  updateUI();
}

function renderSavedRecipes(recipes) {
  el("saved-list").innerHTML = recipes.length
    ? recipes.map((recipe) => `
        <article class="saved-card">
          <div class="saved-card-top">
            <h3>${recipe.recipe_name}</h3>
            <span>${recipe.saved_at}</span>
          </div>
          <p>${recipe.ingredients.join(", ")}</p>
          <div class="saved-meta">
            <span>${recipe.cooking_time}</span>
            <span>${recipe.servings}</span>
          </div>
        </article>
      `).join("")
    : '<p class="empty-state compact">No recipes saved yet.</p>';
}

async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  const data = await res.json();
  return { res, data };
}

async function loadSavedRecipes() {
  try {
    const { data } = await fetchJSON("/api/recipes");
    renderSavedRecipes(data);
  } catch {
    el("saved-list").innerHTML = '<p class="empty-state compact">Saved recipes could not be loaded.</p>';
  }
}

async function generateRecipe() {
  const input = getInput();
  if (!input) return;

  setLoading(true);
  try {
    const { res, data } = await fetchJSON("/api/recipe/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ingredients: input.ingredients,
        custom_name: input.name,
      }),
    });

    if (!res.ok) return setError(data.error || "Recipe generation failed.");
    renderRecipe(data);
  } catch {
    setError("Recipe generation failed.");
  } finally {
    setLoading(false);
  }
}

async function saveRecipe() {
  let recipe = currentRecipe;

  if (customMode) {
    const input = getInput({ customOnly: true, requireName: true });
    if (!input) return;

    recipe = {
      recipeName: input.name,
      ingredientsUsed: input.ingredients,
      steps: [
        "Custom recipe saved directly from your manual input.",
        "Add your own cooking steps later if needed.",
      ],
      cookingTime: "Custom",
      servings: "Custom",
      pantryStaples: [],
      inputMode: "custom",
      promptName: input.name,
      inputIngredients: input.ingredients,
    };

    renderRecipe(recipe);
  } else if (!recipe) {
    el("save-status").textContent = "Generate a recipe before saving.";
    return;
  }

  el("save-btn").disabled = true;
  el("save-status").textContent = "Saving...";

  try {
    const { res, data } = await fetchJSON("/api/recipes/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(recipe),
    });

    if (!res.ok || !data.ok) throw new Error();
    el("save-status").textContent = "Recipe saved.";
    await loadSavedRecipes();
  } catch {
    el("save-status").textContent = "Recipe could not be saved.";
    updateUI();
  }
}

async function loadStudentId() {
  try {
    const { data } = await fetchJSON("/api/info");
    el("student-id-display").textContent = data.student_id;
    el("student-id-top").textContent = data.student_id;
  } catch {
    el("student-id-display").textContent = "unavailable";
    el("student-id-top").textContent = "unavailable";
  }
}

el("mode-toggle").onclick = () => {
  customMode = !customMode;
  updateUI();
};
el("generate-btn").onclick = generateRecipe;
el("save-btn").onclick = saveRecipe;
el("refresh-btn").onclick = loadSavedRecipes;

updateUI();
loadStudentId();
loadSavedRecipes();