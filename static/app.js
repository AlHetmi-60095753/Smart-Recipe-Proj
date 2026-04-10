const el = (id) => document.getElementById(id);
const show = (id) => el(id).classList.remove('hidden');
const hide = (id) => el(id).classList.add('hidden');

const ingredientIds = [
  'ingredient-1',
  'ingredient-2',
  'ingredient-3',
  'ingredient-4',
  'ingredient-5',
];

let customMode = false;

let currentRecipe = null;

// Get the 5 ingredient input values from the page.
function getIngredients() {
  return ingredientIds.map((id) => el(id).value.trim()).filter(Boolean);
}

// Write ingredient values into the 5 ingredient inputs.
function setIngredientInputs(values) {
  const normalized = [...values];
  ingredientIds.forEach((id, index) => {
    el(id).value = normalized[index] || '';
  });
}

// Show one error message (simple + readable).
function showError(message) {
  el('error-msg').textContent = message;
  show('error-msg');
}

// Clear the error area.
function clearError() {
  hide('error-msg');
  el('error-msg').textContent = '';
}

// Enable/disable the loading UI.
function setLoading(isLoading) {
  el('generate-btn').disabled = isLoading;
  if (isLoading) show('loading');
  else hide('loading');
}

function setButtonDisabledIfPresent(id, disabled) {
  const node = document.getElementById(id);
  if (!node) return;
  node.disabled = Boolean(disabled);
}

function setTextIfPresent(id, value) {
  const node = el(id);
  if (!node) return;
  node.textContent = value == null ? '' : String(value);
}

// Toggle inputs and label based on the current mode.
function syncModeUI() {
  el('mode-toggle').setAttribute('aria-pressed', String(customMode));
  el('mode-label').textContent = customMode ? 'Custom Recipe' : '5 Ingredients';

  el('recipe-name').disabled = !customMode;
  el('recipe-idea').disabled = !customMode;

  ingredientIds.forEach((id) => {
    el(id).disabled = customMode;
  });

  clearError();
}

// Build the JSON payload that we send to the Python API.
function buildRecipeRequest() {
  clearError();

  // If its Custom mode: take the comma-separated list and send it as recipeIdea.
  if (customMode) {
    const recipeIdea = el('recipe-idea').value.trim();
    return {
      mode: 'custom',
      recipeName: el('recipe-name').value.trim(),
      recipeIdea,
    };
  }

  // If its 5 ingredients mode
  const ingredients = getIngredients();
  return {
    mode: '5',
    ingredients,
  };
}

// Call the AI-backed API in app.py: POST /api/recipe/generate
async function fetchRecipeFromApi(requestBody) {
  const response = await fetch('/api/recipe/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });

  const data = await response.json().catch(() => null);
  if (!data) return { ok: false, error: 'Server returned invalid JSON.' };

  if (!response.ok) {
    return { ok: false, error: data.error || 'Recipe generation failed.' };
  }

  return { ok: true, recipe: data };
}

// Put the API results onto the page.
function renderRecipe(recipe) {
  currentRecipe = recipe;

  setTextIfPresent('recipe-title', recipe.recipeName || 'Recipe generated');
  setTextIfPresent('ingredients-used', (recipe.ingredientsUsed || []).join(', '));

  // These elements may or may not exist depending on your HTML. We set them only if present.
  setTextIfPresent('cooking-time', recipe.cookingTime || '');
  setTextIfPresent('servings', recipe.servings || '');

  const stepsList = el('steps-list');
  if (stepsList && Array.isArray(recipe.steps)) {
    stepsList.innerHTML = '';
    recipe.steps.forEach((step) => {
      const item = document.createElement('li');
      item.textContent = step;
      stepsList.appendChild(item);
    });
  }

  hide('recipe-empty');
  show('recipe-content');
}

function renderSavedRecipes(recipes) {
  const container = document.getElementById('saved-list');
  if (!container) return;

  container.innerHTML = '';
  if (!recipes || !recipes.length) {
    container.innerHTML = '<p class="empty-state compact">No recipes saved yet.</p>';
    return;
  }

  recipes.forEach((recipe) => {
    const card = document.createElement('article');
    card.className = 'saved-card';
    card.innerHTML = `
      <div class="saved-card-top">
        <h3>${recipe.recipe_name}</h3>
        <span>${recipe.saved_at}</span>
      </div>
      <p>${(recipe.ingredients || []).join(', ')}</p>
      <div class="saved-meta">
        <span>${recipe.cooking_time || ''}</span>
        <span>${recipe.servings || ''}</span>
      </div>
    `;
    container.appendChild(card);
  });
}

async function loadSavedRecipes() {
  const container = document.getElementById('saved-list');
  try {
    const response = await fetch('/api/recipes');
    const recipes = await response.json();
    renderSavedRecipes(recipes);
  } catch (error) {
    if (container) {
      container.innerHTML = '<p class="empty-state compact">Saved recipes could not be loaded.</p>';
    }
  }
}

async function saveRecipe() {
  const statusEl = document.getElementById('save-status');

  if (!currentRecipe) {
    if (statusEl) statusEl.textContent = 'Generate a recipe before saving.';
    return;
  }

  setButtonDisabledIfPresent('save-btn', true);
  if (statusEl) statusEl.textContent = 'Saving...';

  try {
    const response = await fetch('/api/recipes/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentRecipe),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok || !data || !data.ok) {
      throw new Error('Save failed');
    }

    if (statusEl) statusEl.textContent = 'Recipe saved.';
    await loadSavedRecipes();
  } catch (error) {
    if (statusEl) statusEl.textContent = 'Recipe could not be saved.';
    setButtonDisabledIfPresent('save-btn', false);
  }
}

// Main button handler: send request -> show errors or show recipe.
async function generateRecipe() {
  const requestBody = buildRecipeRequest();

  // Small client-side help to avoid calling the API with obvious bad input.
  if (!customMode && requestBody.ingredients.length !== 5) {
    showError('Please enter exactly 5 ingredients.');
    return;
  }

  setLoading(true);
  setButtonDisabledIfPresent('save-btn', true);
  try {
    const result = await fetchRecipeFromApi(requestBody);

    if (!result.ok) {
      showError(result.error || 'Request failed.');
      return;
    }

    renderRecipe(result.recipe);
    setButtonDisabledIfPresent('save-btn', false);

    // Optional: if custom mode uses recipeIdea to fill ingredients, keep the 5 boxes in sync.
    if (customMode && Array.isArray(result.recipe?.inputIngredients)) {
      setIngredientInputs(result.recipe.inputIngredients);
    }
  } catch (error) {
    showError('Failed to call /api/recipe/generate.');
  } finally {
    setLoading(false);
  }
}

// Wire up UI events (script is loaded at the end of index.html).
el('mode-toggle').addEventListener('click', () => {
  customMode = !customMode;
  syncModeUI();
});
el('generate-btn').addEventListener('click', generateRecipe);

syncModeUI();

const saveBtn = document.getElementById('save-btn');
if (saveBtn) saveBtn.addEventListener('click', saveRecipe);

const refreshBtn = document.getElementById('refresh-btn');
if (refreshBtn) refreshBtn.addEventListener('click', loadSavedRecipes);

loadSavedRecipes();
