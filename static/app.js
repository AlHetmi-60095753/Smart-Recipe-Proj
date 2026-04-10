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

// Main button handler: send request -> show errors or show recipe.
async function generateRecipe() {
  const requestBody = buildRecipeRequest();

  // Small client-side help to avoid calling the API with obvious bad input.
  if (!customMode && requestBody.ingredients.length !== 5) {
    showError('Please enter exactly 5 ingredients.');
    return;
  }

  setLoading(true);
  try {
    const result = await fetchRecipeFromApi(requestBody);

    if (!result.ok) {
      showError(result.error || 'Request failed.');
      return;
    }

    renderRecipe(result.recipe);

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
